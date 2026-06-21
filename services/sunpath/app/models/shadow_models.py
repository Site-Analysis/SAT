# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

"""Pydantic models for shadow analysis requests and responses."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ShadowRequestBase(BaseModel):
    """Base model for shadow calculation requests."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=100, ge=1, le=1000, description="Items per page")


class ShadowBBoxRequest(ShadowRequestBase):
    """Request model for shadow calculation with bounding box."""

    min_lat: float = Field(..., ge=-90, le=90, description="Minimum latitude")
    min_lon: float = Field(..., ge=-180, le=180, description="Minimum longitude")
    max_lat: float = Field(..., ge=-90, le=90, description="Maximum latitude")
    max_lon: float = Field(..., ge=-180, le=180, description="Maximum longitude")
    timestamp: datetime = Field(..., description="Timestamp for shadow calculation")


class ShadowRadiusRequest(ShadowRequestBase):
    """Request model for shadow calculation with radius."""

    latitude: float = Field(..., ge=-90, le=90, description="Center latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Center longitude")
    radius_meters: float = Field(..., gt=0, le=5000, description="Radius in meters")
    timestamp: datetime = Field(..., description="Timestamp for shadow calculation")


class ShadowPolygonRequest(ShadowRequestBase):
    """Request model for shadow calculation with polygon."""

    coordinates: list[list[float]] = Field(
        ..., min_length=3, description="Polygon vertices [[lon, lat], ...]"
    )
    timestamp: datetime = Field(..., description="Timestamp for shadow calculation")


class ShadowAddressRequest(ShadowRequestBase):
    """Request model for shadow calculation with address."""

    address: str = Field(..., min_length=3, description="Address to geocode")
    radius_meters: float = Field(
        default=500, gt=0, le=5000, description="Radius around address in meters"
    )
    timestamp: datetime = Field(..., description="Timestamp for shadow calculation")


class ShadowTimeseriesBBoxRequest(BaseModel):
    """Request model for timeseries shadow calculation with bounding box."""

    min_lat: float = Field(..., ge=-90, le=90)
    min_lon: float = Field(..., ge=-180, le=180)
    max_lat: float = Field(..., ge=-90, le=90)
    max_lon: float = Field(..., ge=-180, le=180)
    start_datetime: datetime = Field(..., description="Start timestamp")
    end_datetime: datetime = Field(..., description="End timestamp")
    interval_minutes: int = Field(default=30, ge=1, le=1440, description="Time interval in minutes")


class ShadowTimeseriesRadiusRequest(BaseModel):
    """Request model for timeseries shadow calculation with radius."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_meters: float = Field(..., gt=0, le=5000)
    start_datetime: datetime
    end_datetime: datetime
    interval_minutes: int = Field(default=30, ge=1, le=1440)


class ShadowTimeseriesPolygonRequest(BaseModel):
    """Request model for timeseries shadow calculation with polygon."""

    coordinates: list[list[float]] = Field(..., min_length=3)
    start_datetime: datetime
    end_datetime: datetime
    interval_minutes: int = Field(default=30, ge=1, le=1440)


class ShadowTimeseriesAddressRequest(BaseModel):
    """Request model for timeseries shadow calculation with address."""

    address: str = Field(..., min_length=3)
    radius_meters: float = Field(default=500, gt=0, le=5000)
    start_datetime: datetime
    end_datetime: datetime
    interval_minutes: int = Field(default=30, ge=1, le=1440)


class ShadowCumulativeBBoxRequest(BaseModel):
    """Request model for cumulative shadow calculation with bounding box."""

    min_lat: float = Field(..., ge=-90, le=90)
    min_lon: float = Field(..., ge=-180, le=180)
    max_lat: float = Field(..., ge=-90, le=90)
    max_lon: float = Field(..., ge=-180, le=180)
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    interval_minutes: int = Field(default=30, ge=1, le=1440)


class ShadowCumulativeRadiusRequest(BaseModel):
    """Request model for cumulative shadow calculation with radius."""

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius_meters: float = Field(..., gt=0, le=5000)
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    interval_minutes: int = Field(default=30, ge=1, le=1440)


class ShadowCumulativePolygonRequest(BaseModel):
    """Request model for cumulative shadow calculation with polygon."""

    coordinates: list[list[float]] = Field(..., min_length=3)
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    interval_minutes: int = Field(default=30, ge=1, le=1440)


class ShadowCumulativeAddressRequest(BaseModel):
    """Request model for cumulative shadow calculation with address."""

    address: str = Field(..., min_length=3)
    radius_meters: float = Field(default=500, gt=0, le=5000)
    date: str = Field(..., description="Date in YYYY-MM-DD format")
    interval_minutes: int = Field(default=30, ge=1, le=1440)


class ShadowGeometry(BaseModel):
    """GeoJSON geometry for shadow polygon."""

    type: str = "Polygon"
    coordinates: list[list[list[float]]]


class ShadowProperties(BaseModel):
    """Properties for shadow feature."""

    source_building_id: str
    building_height: float
    shadow_length: float
    timestamp: str
    solar_elevation: float
    solar_azimuth: float
    opacity: float = 0.75
    default_height_used: bool = False


class ShadowFeature(BaseModel):
    """GeoJSON feature for shadow."""

    type: str = "Feature"
    geometry: ShadowGeometry
    properties: ShadowProperties


class ShadowMetadata(BaseModel):
    """Metadata for shadow calculation response."""

    total_buildings: int
    buildings_with_shadows: int
    buildings_without_height: int
    total_shadow_area_sq_meters: float
    timestamp: str
    solar_elevation: float
    solar_azimuth: float
    query_time_seconds: float


class ShadowResponse(BaseModel):
    """Response model for single timestamp shadow calculation."""

    buildings: dict[str, Any]  # Building GeoJSON FeatureCollection
    shadows: dict[str, Any]  # Shadow GeoJSON FeatureCollection
    metadata: ShadowMetadata


class SolarPosition(BaseModel):
    """Solar position data for a timestamp."""

    elevation: float
    azimuth: float
    zenith: float


class ShadowSnapshot(BaseModel):
    """Shadow data for a single timestamp."""

    timestamp: str
    solar_position: SolarPosition
    shadows: dict[str, Any]  # GeoJSON FeatureCollection
    metadata: dict[str, Any]


class ShadowTimeseriesMetadata(BaseModel):
    """Metadata for timeseries shadow calculation."""

    start_datetime: str
    end_datetime: str
    interval_minutes: int
    total_snapshots: int
    total_buildings: int
    query_time_seconds: float


class ShadowTimeseriesResponse(BaseModel):
    """Response model for timeseries shadow calculation."""

    buildings: dict[str, Any]  # Building GeoJSON FeatureCollection
    snapshots: list[ShadowSnapshot]
    metadata: ShadowTimeseriesMetadata


class DurationCategory(StrEnum):
    """Shadow duration categories for cumulative analysis."""

    ZERO_TO_TWO = "0-2 hours"
    TWO_TO_FOUR = "2-4 hours"
    FOUR_TO_SIX = "4-6 hours"
    SIX_TO_EIGHT = "6-8 hours"
    EIGHT_PLUS = "8+ hours"


class CoverageZone(BaseModel):
    """Shadow coverage zone with duration category."""

    duration_category: DurationCategory
    hours_range: list[float]  # [min_hours, max_hours]
    polygon: dict[str, Any]  # GeoJSON geometry
    area_sq_meters: float
    color: str
    opacity: float


class ShadowCumulativeMetadata(BaseModel):
    """Metadata for cumulative shadow calculation."""

    date: str
    sunrise: str
    sunset: str
    total_snapshots: int
    total_buildings: int
    total_shadow_area_sq_meters: float
    max_shadow_hours: float
    query_time_seconds: float


class ShadowCumulativeResponse(BaseModel):
    """Response model for cumulative shadow calculation."""

    buildings: dict[str, Any]  # Building GeoJSON FeatureCollection
    coverage_zones: list[CoverageZone]
    metadata: ShadowCumulativeMetadata
