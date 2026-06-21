# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

"""Pydantic models for building extraction endpoints."""

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ============= Enums =============


class BuildingSource(StrEnum):
    """Source of building data."""

    OVERPASS = "overpass"
    GEE = "gee"


class BuildingCategory(StrEnum):
    """Normalized building categories."""

    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"
    INDUSTRIAL = "industrial"
    INSTITUTIONAL = "institutional"
    MIXED_USE = "mixed_use"
    OTHER = "other"


# ============= Request Models =============


class BoundingBoxRequest(BaseModel):
    """Request model for bounding box building extraction."""

    min_lat: float = Field(..., ge=-90, le=90, description="Minimum latitude")
    min_lon: float = Field(..., ge=-180, le=180, description="Minimum longitude")
    max_lat: float = Field(..., ge=-90, le=90, description="Maximum latitude")
    max_lon: float = Field(..., ge=-180, le=180, description="Maximum longitude")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=100, ge=1, le=1000, description="Number of buildings per page")

    @field_validator("max_lat")
    @classmethod
    def validate_lat_order(cls, v, info):
        """Validate that max_lat > min_lat."""
        if "min_lat" in info.data and v <= info.data["min_lat"]:
            raise ValueError("max_lat must be greater than min_lat")
        return v

    @field_validator("max_lon")
    @classmethod
    def validate_lon_order(cls, v, info):
        """Validate that max_lon > min_lon."""
        if "min_lon" in info.data and v <= info.data["min_lon"]:
            raise ValueError("max_lon must be greater than min_lon")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "min_lat": 40.7,
                "min_lon": -74.1,
                "max_lat": 40.8,
                "max_lon": -74.0,
                "page": 1,
                "page_size": 100,
            }
        }
    )


class RadiusRequest(BaseModel):
    """Request model for radius-based building extraction."""

    latitude: float = Field(..., ge=-90, le=90, description="Center latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Center longitude")
    radius_meters: float = Field(..., gt=0, le=10000, description="Radius in meters (max 10km)")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=100, ge=1, le=1000, description="Number of buildings per page")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "latitude": 40.7580,
                "longitude": -73.9855,
                "radius_meters": 500,
                "page": 1,
                "page_size": 100,
            }
        }
    )


class PolygonRequest(BaseModel):
    """Request model for custom polygon building extraction."""

    coordinates: list[list[float]] = Field(
        ...,
        description="Polygon coordinates as [[lon, lat], ...]. First and last point must match.",
    )
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=100, ge=1, le=1000, description="Number of buildings per page")

    @field_validator("coordinates")
    @classmethod
    def validate_polygon(cls, v):
        """Validate polygon coordinates."""
        if len(v) < 4:
            raise ValueError("Polygon must have at least 4 points (including closing point)")
        if v[0] != v[-1]:
            raise ValueError("First and last coordinates must be identical (closed polygon)")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "coordinates": [
                    [-74.0, 40.7],
                    [-74.0, 40.8],
                    [-73.9, 40.8],
                    [-73.9, 40.7],
                    [-74.0, 40.7],
                ],
                "page": 1,
                "page_size": 100,
            }
        }
    )


class AddressRequest(BaseModel):
    """Request model for address-based building extraction."""

    address: str = Field(..., min_length=3, description="Address to geocode")
    radius_meters: float = Field(
        default=500, gt=0, le=10000, description="Radius around geocoded location in meters"
    )
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=100, ge=1, le=1000, description="Number of buildings per page")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "address": "Times Square, New York, NY",
                "radius_meters": 500,
                "page": 1,
                "page_size": 100,
            }
        }
    )


# ============= Building Data Models =============


class BuildingProperties(BaseModel):
    """Properties of a single building."""

    source: BuildingSource = Field(..., description="Data source (overpass or gee)")
    height: float | None = Field(None, description="Building height in meters")
    floors: int | None = Field(None, description="Number of floors")
    building_type_raw: str | None = Field(None, description="Raw building type from source")
    building_type_normalized: BuildingCategory | None = Field(
        None, description="Normalized category"
    )
    address: str | None = Field(None, description="Building address if available")
    footprint_area: float | None = Field(None, description="Footprint area in square meters")
    confidence: float | None = Field(None, description="Confidence score (GEE only, 0-1)")
    osm_tags: dict[str, Any] | None = Field(None, description="Raw OSM tags (Overpass only)")
    osm_id: str | None = Field(None, description="OSM way ID (Overpass only)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": "overpass",
                "height": 45.0,
                "floors": 12,
                "building_type_raw": "apartments",
                "building_type_normalized": "residential",
                "address": "123 Main St",
                "footprint_area": 850.5,
                "confidence": None,
                "osm_tags": {"building": "apartments", "name": "Park Plaza"},
                "osm_id": "way/12345678",
            }
        }
    )


class BuildingGeometry(BaseModel):
    """GeoJSON geometry for a building."""

    type: Literal["Polygon", "MultiPolygon"] = Field(..., description="Geometry type")
    coordinates: list[Any] = Field(..., description="Geometry coordinates")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [-74.0060, 40.7128],
                        [-74.0060, 40.7138],
                        [-74.0050, 40.7138],
                        [-74.0050, 40.7128],
                        [-74.0060, 40.7128],
                    ]
                ],
            }
        }
    )


class BuildingFeature(BaseModel):
    """GeoJSON feature representing a building."""

    type: Literal["Feature"] = Field(default="Feature", description="GeoJSON type")
    geometry: BuildingGeometry = Field(..., description="Building geometry")
    properties: BuildingProperties = Field(..., description="Building properties")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-74.0060, 40.7128],
                            [-74.0060, 40.7138],
                            [-74.0050, 40.7138],
                            [-74.0050, 40.7128],
                            [-74.0060, 40.7128],
                        ]
                    ],
                },
                "properties": {
                    "source": "overpass",
                    "height": 45.0,
                    "floors": 12,
                    "building_type_raw": "apartments",
                    "building_type_normalized": "residential",
                },
            }
        }
    )


# ============= Response Models =============


class BuildingSummary(BaseModel):
    """Summary statistics for extracted buildings."""

    total_buildings: int = Field(..., description="Total number of buildings")
    overpass_count: int = Field(..., description="Buildings from Overpass API")
    gee_count: int = Field(..., description="Buildings from Google Earth Engine")
    area_sq_km: float = Field(..., description="Query area in square kilometers")
    avg_height: float | None = Field(None, description="Average building height in meters")
    avg_footprint_area: float | None = Field(None, description="Average footprint area in m²")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_buildings": 245,
                "overpass_count": 180,
                "gee_count": 65,
                "area_sq_km": 0.85,
                "avg_height": 32.5,
                "avg_footprint_area": 425.8,
            }
        }
    )


class PaginationInfo(BaseModel):
    """Pagination metadata."""

    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_count: int = Field(..., description="Total number of buildings")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "page_size": 100,
                "total_count": 245,
                "total_pages": 3,
                "has_next": True,
                "has_prev": False,
            }
        }
    )


class BuildingResponse(BaseModel):
    """Response model for building extraction endpoints."""

    type: Literal["FeatureCollection"] = Field(
        default="FeatureCollection", description="GeoJSON type"
    )
    features: list[BuildingFeature] = Field(..., description="List of building features")
    summary: BuildingSummary = Field(..., description="Summary statistics")
    pagination: PaginationInfo = Field(..., description="Pagination information")
    query_time_seconds: float = Field(..., description="Query execution time")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "FeatureCollection",
                "features": [],
                "summary": {
                    "total_buildings": 245,
                    "overpass_count": 180,
                    "gee_count": 65,
                    "area_sq_km": 0.85,
                },
                "pagination": {
                    "page": 1,
                    "page_size": 100,
                    "total_count": 245,
                    "total_pages": 3,
                    "has_next": True,
                    "has_prev": False,
                },
                "query_time_seconds": 3.45,
                "timestamp": "2025-11-24T12:00:00Z",
            }
        }
    )
