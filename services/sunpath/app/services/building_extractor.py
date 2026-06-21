# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

"""
Building extraction service that orchestrates data from Overpass API and Google Earth Engine.
Merges datasets, detects overlaps, enriches with heights, and handles pagination.
"""

import math
import time
from dataclasses import dataclass
from typing import Any

import pyproj
from app.core.config import settings
from app.core.exceptions import AreaLimitExceededError, GeocodingError
from app.core.logging import get_logger
from app.models.building_models import (
    AddressRequest,
    BoundingBoxRequest,
    BuildingCategory,
    BuildingFeature,
    BuildingGeometry,
    BuildingProperties,
    BuildingResponse,
    BuildingSource,
    BuildingSummary,
    PaginationInfo,
    PolygonRequest,
    RadiusRequest,
)
from app.services.gee_service import GEEService
from app.services.geocoding_service import GeocodingService
from app.services.osm_extractor import OverpassBuilding, OverpassService
from shapely.geometry import Point, Polygon
from shapely.ops import transform

logger = get_logger(__name__)


@dataclass
class MergedBuilding:
    """Internal representation of a building after merging datasets."""

    source: BuildingSource
    geometry: list[list[float]]  # [lon, lat] coordinates
    height: float | None
    floors: int | None
    building_type_raw: str
    building_type_normalized: BuildingCategory
    address: str | None
    footprint_area: float
    confidence: float | None
    osm_tags: dict[str, str] | None
    osm_id: str | None


class BuildingExtractor:
    """Main orchestrator for building extraction from multiple data sources."""

    def __init__(self, gee_service: GEEService | None = None):
        self.overpass_service = OverpassService()
        self.gee_service = gee_service if gee_service else GEEService()
        self.geocoding_service = GeocodingService()

        # Track if GEE was provided externally (already initialized)
        self._gee_initialized = gee_service is not None and gee_service.initialized

    def _ensure_gee_initialized(self):
        """Initialize GEE service if not already done."""
        if not self._gee_initialized:
            logger.info("Initializing Google Earth Engine service")
            self.gee_service.initialize()
            self._gee_initialized = True

    async def extract_from_bbox(self, request: BoundingBoxRequest) -> BuildingResponse:
        """
        Extract buildings within a bounding box.

        Args:
            request: BoundingBoxRequest with coordinates and pagination

        Returns:
            BuildingResponse with features and metadata
        """
        start_time = time.time()

        # Validate area
        bbox = (request.min_lat, request.min_lon, request.max_lat, request.max_lon)
        area_sq_km = self._calculate_bbox_area(bbox)
        self._validate_area(area_sq_km)

        # Extract and merge buildings
        logger.info(f"Extracting buildings from bbox: {bbox}")
        merged_buildings = await self._extract_and_merge(bbox=bbox)

        # Enrich with heights and addresses
        skip_height = not settings.ENABLE_GEE_HEIGHT_ENRICHMENT
        enriched_buildings = await self._enrich_buildings(
            merged_buildings, skip_height_enrichment=skip_height
        )

        # Convert to response format with pagination
        query_time = time.time() - start_time
        return self._create_response(
            enriched_buildings,
            page=request.page,
            page_size=request.page_size,
            query_time=query_time,
            area_sq_km=area_sq_km,
        )

    async def extract_from_radius(self, request: RadiusRequest) -> BuildingResponse:
        """
        Extract buildings within a radius from a center point.

        Args:
            request: RadiusRequest with center coordinates, radius, and pagination

        Returns:
            BuildingResponse with features and metadata
        """
        start_time = time.time()

        # Create circular polygon
        polygon = self._create_circle_polygon(
            request.latitude, request.longitude, request.radius_meters
        )

        # Validate area
        area_sq_km = self._calculate_polygon_area_sq_km(polygon)
        self._validate_area(area_sq_km)

        # Extract and merge buildings
        logger.info(
            f"Extracting buildings within {request.radius_meters}m of ({request.latitude}, {request.longitude})"
        )
        merged_buildings = await self._extract_and_merge(polygon=polygon)

        # Enrich with heights and addresses
        skip_height = not settings.ENABLE_GEE_HEIGHT_ENRICHMENT
        enriched_buildings = await self._enrich_buildings(
            merged_buildings, skip_height_enrichment=skip_height
        )

        # Convert to response format with pagination
        query_time = time.time() - start_time
        return self._create_response(
            enriched_buildings,
            page=request.page,
            page_size=request.page_size,
            query_time=query_time,
            area_sq_km=area_sq_km,
        )

    async def extract_from_polygon(self, request: PolygonRequest) -> BuildingResponse:
        """
        Extract buildings within a custom polygon.

        Args:
            request: PolygonRequest with polygon coordinates and pagination

        Returns:
            BuildingResponse with features and metadata
        """
        start_time = time.time()

        # Convert to standard format
        polygon = request.coordinates

        # Validate area
        area_sq_km = self._calculate_polygon_area_sq_km(polygon)
        self._validate_area(area_sq_km)

        # Extract and merge buildings
        logger.info(f"Extracting buildings from polygon with {len(request.coordinates)} vertices")
        merged_buildings = await self._extract_and_merge(polygon=polygon)

        # Enrich with heights and addresses
        skip_height = not settings.ENABLE_GEE_HEIGHT_ENRICHMENT
        enriched_buildings = await self._enrich_buildings(
            merged_buildings, skip_height_enrichment=skip_height
        )

        # Convert to response format with pagination
        query_time = time.time() - start_time
        return self._create_response(
            enriched_buildings,
            page=request.page,
            page_size=request.page_size,
            query_time=query_time,
            area_sq_km=area_sq_km,
        )

    async def extract_from_address(self, request: AddressRequest) -> BuildingResponse:
        """
        Extract buildings near an address.

        Args:
            request: AddressRequest with address string, radius, and pagination

        Returns:
            BuildingResponse with features and metadata
        """
        start_time = time.time()

        # Geocode address to coordinates
        logger.info(f"Geocoding address: {request.address}")
        try:
            lat, lon = self.geocoding_service.geocode_address(request.address)
        except Exception as e:
            raise GeocodingError(f"Failed to geocode address '{request.address}': {str(e)}")

        # Create circular polygon
        polygon = self._create_circle_polygon(lat, lon, request.radius_meters)

        # Validate area
        area_sq_km = self._calculate_polygon_area_sq_km(polygon)
        self._validate_area(area_sq_km)

        # Extract and merge buildings
        logger.info(
            f"Extracting buildings within {request.radius_meters}m of geocoded location ({lat}, {lon})"
        )
        merged_buildings = await self._extract_and_merge(polygon=polygon)

        # Enrich with heights and addresses
        skip_height = not settings.ENABLE_GEE_HEIGHT_ENRICHMENT
        enriched_buildings = await self._enrich_buildings(
            merged_buildings, skip_height_enrichment=skip_height
        )

        # Convert to response format with pagination
        query_time = time.time() - start_time
        return self._create_response(
            enriched_buildings,
            page=request.page,
            page_size=request.page_size,
            query_time=query_time,
            area_sq_km=area_sq_km,
        )

    async def _extract_and_merge(
        self,
        bbox: tuple[float, float, float, float] | None = None,
        polygon: list[list[float]] | None = None,
    ) -> list[MergedBuilding]:
        """
        Extract buildings from both Overpass and GEE, then merge them.

        Args:
            bbox: Optional bounding box
            polygon: Optional polygon coordinates

        Returns:
            List of merged buildings
        """
        # Ensure GEE is initialized
        self._ensure_gee_initialized()

        # Extract from Overpass API
        logger.info("Querying Overpass API for OSM buildings")
        overpass_buildings = self.overpass_service.query_buildings(bbox=bbox, polygon=polygon)
        logger.info(f"Found {len(overpass_buildings)} buildings from Overpass")

        # Extract from Google Earth Engine
        logger.info("Querying Google Earth Engine for building footprints")
        if bbox:
            # Convert bbox from (min_lat, min_lon, max_lat, max_lon) to (min_lon, min_lat, max_lon, max_lat) for GEE
            gee_bbox = (bbox[1], bbox[0], bbox[3], bbox[2])
            gee_buildings = self.gee_service.get_building_footprints(gee_bbox)
        else:
            # Convert polygon to bbox for GEE query
            poly = Polygon([(coord[0], coord[1]) for coord in polygon])
            bounds = poly.bounds  # (minx, miny, maxx, maxy)
            gee_bbox = (
                bounds[1],
                bounds[0],
                bounds[3],
                bounds[2],
            )  # (min_lat, min_lon, max_lat, max_lon)
            gee_buildings = self.gee_service.get_building_footprints(gee_bbox)

            # Filter GEE buildings by polygon
            filtered_gee = []
            for gee_building in gee_buildings:
                # Check if building centroid is within polygon
                centroid = self._calculate_polygon_centroid(
                    gee_building["geometry"]["coordinates"][0]
                )
                point = Point(centroid[0], centroid[1])
                if poly.contains(point):
                    filtered_gee.append(gee_building)
            gee_buildings = filtered_gee

        logger.info(f"Found {len(gee_buildings)} buildings from GEE")

        # Merge datasets
        merged_buildings = self._merge_datasets(overpass_buildings, gee_buildings)
        logger.info(
            f"Merged into {len(merged_buildings)} total buildings ({sum(1 for b in merged_buildings if b.source == BuildingSource.OVERPASS)} from Overpass, {sum(1 for b in merged_buildings if b.source == BuildingSource.GEE)} from GEE)"
        )

        return merged_buildings

    def _merge_datasets(
        self, overpass_buildings: list[OverpassBuilding], gee_buildings: list[dict[str, Any]]
    ) -> list[MergedBuilding]:
        """
        Merge Overpass and GEE datasets, prioritizing Overpass and removing overlaps.

        Args:
            overpass_buildings: Buildings from Overpass API
            gee_buildings: Buildings from Google Earth Engine

        Returns:
            List of merged buildings with source attribution
        """
        merged = []

        # Convert Overpass buildings to MergedBuilding format
        overpass_polygons = []
        for osm_building in overpass_buildings:
            # Extract data from OSM tags
            height = self.overpass_service.extract_height_from_tags(osm_building.tags)
            floors = self.overpass_service.extract_floors_from_tags(osm_building.tags)
            building_type = osm_building.tags.get("building", "yes")
            category = self.overpass_service.normalize_building_category(osm_building.tags)

            # Calculate footprint area
            area = self._calculate_polygon_area(osm_building.geometry)

            merged_building = MergedBuilding(
                source=BuildingSource.OVERPASS,
                geometry=osm_building.geometry,
                height=height,
                floors=floors,
                building_type_raw=building_type,
                building_type_normalized=category,
                address=None,  # Will be enriched later
                footprint_area=area,
                confidence=None,  # Overpass doesn't provide confidence
                osm_tags=osm_building.tags,
                osm_id=osm_building.osm_id,
            )

            merged.append(merged_building)
            overpass_polygons.append(Polygon([(c[0], c[1]) for c in osm_building.geometry]))

        # Add GEE buildings that don't overlap with Overpass buildings
        for gee_building in gee_buildings:
            gee_coords = gee_building["geometry"]["coordinates"][0]
            gee_polygon = Polygon([(c[0], c[1]) for c in gee_coords])

            # Check for intersection with any Overpass building
            is_overlap = False
            for overpass_polygon in overpass_polygons:
                if gee_polygon.intersects(overpass_polygon):
                    # Calculate intersection area
                    intersection = gee_polygon.intersection(overpass_polygon)
                    intersection_ratio = intersection.area / gee_polygon.area

                    # Consider it an overlap if more than 30% of the building intersects
                    if intersection_ratio > 0.3:
                        is_overlap = True
                        break

            # Add GEE building if it doesn't overlap
            if not is_overlap:
                area = gee_building.get("area_in_meters", 0.0)
                confidence = gee_building.get("confidence", 0.0)

                merged_building = MergedBuilding(
                    source=BuildingSource.GEE,
                    geometry=gee_coords,
                    height=None,  # Will be sampled from GEE height dataset
                    floors=None,
                    building_type_raw="building",
                    building_type_normalized=BuildingCategory.OTHER,
                    address=None,
                    footprint_area=area,
                    confidence=confidence,
                    osm_tags=None,
                    osm_id=None,
                )

                merged.append(merged_building)

        return merged

    async def _enrich_buildings(
        self, buildings: list[MergedBuilding], skip_height_enrichment: bool = False
    ) -> list[MergedBuilding]:
        """
        Enrich buildings with height data and addresses.

        Args:
            buildings: List of merged buildings
            skip_height_enrichment: If True, skip sampling heights from GEE (much faster)

        Returns:
            List of enriched buildings
        """
        logger.info(f"Enriching {len(buildings)} buildings with height and address data")

        # Enrich GEE buildings with height data from GEE height dataset (optional, very slow)
        if not skip_height_enrichment:
            gee_buildings_to_enrich = [
                b for b in buildings if b.source == BuildingSource.GEE and b.height is None
            ]

            if gee_buildings_to_enrich:
                logger.info(
                    f"Sampling heights for {len(gee_buildings_to_enrich)} GEE buildings (this may take a while...)"
                )
                for building in gee_buildings_to_enrich:
                    try:
                        # Sample height using multiple points within footprint
                        height = self.gee_service.sample_height_within_footprint(
                            {"type": "Polygon", "coordinates": [building.geometry]}, num_points=5
                        )
                        if height and height > 0:
                            building.height = height
                            # Estimate floors
                            building.floors = max(1, int(height / 3.0))
                    except Exception as e:
                        logger.warning(f"Failed to sample height for GEE building: {e}")
        else:
            logger.info(
                "Skipping height enrichment for GEE buildings (disabled via ENABLE_GEE_HEIGHT_ENRICHMENT=False)"
            )

        # Optionally enrich Overpass buildings without height
        overpass_buildings_without_height = [
            b for b in buildings if b.source == BuildingSource.OVERPASS and b.height is None
        ]

        if overpass_buildings_without_height:
            logger.info(
                f"Sampling heights for {len(overpass_buildings_without_height)} Overpass buildings without height tags"
            )
            for building in overpass_buildings_without_height:
                try:
                    height = self.gee_service.sample_height_within_footprint(
                        {"type": "Polygon", "coordinates": [building.geometry]}, num_points=5
                    )
                    if height and height > 0:
                        building.height = height
                        if building.floors is None:
                            building.floors = max(1, int(height / 3.0))
                except Exception as e:
                    logger.warning(f"Failed to sample height for Overpass building: {e}")

        # Note: Reverse geocoding for addresses is expensive and rate-limited
        # We'll skip it by default but it could be added as an optional feature

        return buildings

    def _create_response(
        self,
        buildings: list[MergedBuilding],
        page: int,
        page_size: int,
        query_time: float,
        area_sq_km: float,
    ) -> BuildingResponse:
        """
        Create a paginated BuildingResponse from merged buildings.

        Args:
            buildings: List of enriched buildings
            page: Page number (1-indexed)
            page_size: Number of items per page
            query_time: Query execution time in seconds
            area_sq_km: Query area in square kilometers

        Returns:
            BuildingResponse with paginated features
        """
        total_count = len(buildings)

        # Calculate pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_buildings = buildings[start_idx:end_idx]

        # Convert to GeoJSON features
        features = []
        for building in paginated_buildings:
            properties = BuildingProperties(
                source=building.source,
                height=building.height,
                floors=building.floors,
                building_type_raw=building.building_type_raw,
                building_type_normalized=building.building_type_normalized,
                address=building.address,
                footprint_area=building.footprint_area,
                confidence=building.confidence,
                osm_tags=building.osm_tags,
                osm_id=building.osm_id,
            )

            geometry = BuildingGeometry(type="Polygon", coordinates=[building.geometry])

            feature = BuildingFeature(type="Feature", geometry=geometry, properties=properties)

            features.append(feature)

        # Calculate summary statistics
        summary = self._calculate_summary(buildings, area_sq_km)

        # Calculate total pages
        total_pages = math.ceil(total_count / page_size) if page_size > 0 else 0

        # Create pagination info
        pagination = PaginationInfo(
            page=page,
            page_size=page_size,
            total_count=total_count,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )

        return BuildingResponse(
            type="FeatureCollection",
            features=features,
            summary=summary,
            pagination=pagination,
            query_time_seconds=round(query_time, 2),
        )

    def _calculate_summary(
        self, buildings: list[MergedBuilding], area_sq_km: float
    ) -> BuildingSummary:
        """Calculate summary statistics for buildings."""
        total_buildings = len(buildings)
        overpass_count = sum(1 for b in buildings if b.source == BuildingSource.OVERPASS)
        gee_count = sum(1 for b in buildings if b.source == BuildingSource.GEE)

        heights = [b.height for b in buildings if b.height is not None]
        avg_height = sum(heights) / len(heights) if heights else None

        footprint_areas = [b.footprint_area for b in buildings if b.footprint_area > 0]
        avg_footprint_area = (
            sum(footprint_areas) / len(footprint_areas) if footprint_areas else None
        )

        return BuildingSummary(
            total_buildings=total_buildings,
            overpass_count=overpass_count,
            gee_count=gee_count,
            area_sq_km=round(area_sq_km, 4),
            avg_height=round(avg_height, 2) if avg_height else None,
            avg_footprint_area=round(avg_footprint_area, 2) if avg_footprint_area else None,
        )

    def _validate_area(self, area_sq_km: float):
        """
        Validate that the query area doesn't exceed the maximum allowed area.

        Args:
            area_sq_km: Area in square kilometers

        Raises:
            AreaLimitExceededError: If area exceeds MAX_AREA_SQ_KM
        """
        if area_sq_km > settings.MAX_AREA_SQ_KM:
            raise AreaLimitExceededError(
                f"Query area ({area_sq_km:.2f} km²) exceeds maximum allowed area ({settings.MAX_AREA_SQ_KM} km²)"
            )

        logger.info(f"Query area: {area_sq_km:.2f} km²")

    def _calculate_bbox_area(self, bbox: tuple[float, float, float, float]) -> float:
        """Calculate area of bounding box in square kilometers."""
        min_lat, min_lon, max_lat, max_lon = bbox

        # Create polygon from bbox
        polygon = [
            [min_lon, min_lat],
            [max_lon, min_lat],
            [max_lon, max_lat],
            [min_lon, max_lat],
            [min_lon, min_lat],
        ]

        return self._calculate_polygon_area_sq_km(polygon)

    def _calculate_polygon_area_sq_km(self, polygon: list[list[float]]) -> float:
        """Calculate area of polygon in square kilometers using UTM projection."""
        poly = Polygon([(coord[0], coord[1]) for coord in polygon])

        # Get centroid to determine UTM zone
        centroid = poly.centroid

        # Calculate UTM zone
        utm_zone = int((centroid.x + 180) / 6) + 1
        utm_epsg = 32600 + utm_zone if centroid.y >= 0 else 32700 + utm_zone

        # Project to UTM
        wgs84 = pyproj.CRS("EPSG:4326")
        utm = pyproj.CRS(f"EPSG:{utm_epsg}")
        project = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True).transform

        poly_utm = transform(project, poly)

        # Area in square meters, convert to square kilometers
        area_sq_m = poly_utm.area
        area_sq_km = area_sq_m / 1_000_000

        return area_sq_km

    def _calculate_polygon_area(self, coords: list[list[float]]) -> float:
        """Calculate area of polygon in square meters."""
        try:
            poly = Polygon([(c[0], c[1]) for c in coords])

            # Get centroid to determine UTM zone
            centroid = poly.centroid

            # Calculate UTM zone
            utm_zone = int((centroid.x + 180) / 6) + 1
            utm_epsg = 32600 + utm_zone if centroid.y >= 0 else 32700 + utm_zone

            # Project to UTM
            wgs84 = pyproj.CRS("EPSG:4326")
            utm = pyproj.CRS(f"EPSG:{utm_epsg}")
            project = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True).transform

            poly_utm = transform(project, poly)

            return poly_utm.area
        except Exception as e:
            logger.warning(f"Failed to calculate polygon area: {e}")
            return 0.0

    def _calculate_polygon_centroid(self, coords: list[list[float]]) -> tuple[float, float]:
        """Calculate centroid of a polygon."""
        try:
            poly = Polygon([(c[0], c[1]) for c in coords])
            centroid = poly.centroid
            return (centroid.x, centroid.y)
        except Exception as e:
            logger.warning(f"Failed to calculate centroid: {e}")
            return (coords[0][0], coords[0][1])

    def _create_circle_polygon(
        self, center_lat: float, center_lon: float, radius_meters: float, num_points: int = 32
    ) -> list[list[float]]:
        """
        Create a circular polygon around a center point.

        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            radius_meters: Radius in meters
            num_points: Number of points to approximate the circle

        Returns:
            List of [lon, lat] coordinates forming a polygon
        """
        # Convert to UTM for accurate distance calculation
        center_point = Point(center_lon, center_lat)

        # Determine UTM zone
        utm_zone = int((center_lon + 180) / 6) + 1
        utm_epsg = 32600 + utm_zone if center_lat >= 0 else 32700 + utm_zone

        # Create projection transformers
        wgs84 = pyproj.CRS("EPSG:4326")
        utm = pyproj.CRS(f"EPSG:{utm_epsg}")
        project_to_utm = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True).transform
        project_to_wgs84 = pyproj.Transformer.from_crs(utm, wgs84, always_xy=True).transform

        # Project center to UTM
        center_utm = transform(project_to_utm, center_point)

        # Create circle in UTM coordinates
        circle_utm = center_utm.buffer(radius_meters)

        # Project back to WGS84
        circle_wgs84 = transform(project_to_wgs84, circle_utm)

        # Extract coordinates
        coords = list(circle_wgs84.exterior.coords)

        # Convert to [lon, lat] format
        return [[coord[0], coord[1]] for coord in coords]
