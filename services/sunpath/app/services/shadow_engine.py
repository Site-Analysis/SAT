# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

"""
Shadow calculation engine for building shadow analysis.
Implements Phase 1 (geometry calculation) and Phase 2 (batch processing).
"""

import math
from typing import Any

import pyproj
import tzfpy
from app.core.config import settings
from app.core.logging import get_logger
from app.models.building_models import BuildingFeature
from app.services.gee_service import GEEService
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree

logger = get_logger(__name__)


class ShadowEngine:
    """Engine for calculating building shadows based on solar position."""

    def __init__(self, gee_service: GEEService | None = None):
        """Initialize shadow engine with optional GEE service for height enrichment."""
        self.gee_service = gee_service if gee_service else GEEService()
        self.simplification_tolerance = settings.SHADOW_SIMPLIFICATION_TOLERANCE_METERS
        self.max_shadow_length = settings.SHADOW_MAX_LENGTH_METERS
        self.min_solar_elevation = settings.SHADOW_MIN_SOLAR_ELEVATION
        self.base_opacity = settings.SHADOW_BASE_OPACITY
        self.max_opacity = settings.SHADOW_MAX_OPACITY
        self.min_shadow_area = 1.0  # Minimum shadow area in square meters

    def detect_timezone(self, latitude: float, longitude: float) -> str:
        """
        Detect timezone from geographic coordinates using tzfpy.

        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees

        Returns:
            Timezone string (e.g., 'America/New_York') or 'UTC' if detection fails
        """
        try:
            tz_name = tzfpy.get_tz(longitude, latitude)
            if tz_name:
                logger.info(
                    f"Detected timezone: {tz_name} for location ({latitude:.4f}, {longitude:.4f})"
                )
                return tz_name
            else:
                logger.warning(
                    f"Timezone detection returned None for ({latitude:.4f}, {longitude:.4f}), using UTC"
                )
                return "UTC"
        except Exception as e:
            logger.warning(
                f"Timezone detection failed for ({latitude:.4f}, {longitude:.4f}): {str(e)}, using UTC"
            )
            return "UTC"

    def calculate_shadow_metrics(
        self, building_height: float, solar_elevation: float, solar_azimuth: float
    ) -> dict[str, float]:
        """
        Calculate shadow length and direction from solar position.

        Args:
            building_height: Height of building in meters
            solar_elevation: Solar elevation angle in degrees (0-90)
            solar_azimuth: Solar azimuth angle in degrees (0-360)

        Returns:
            Dictionary with shadow_length, shadow_azimuth, and other metrics
        """
        # Sun below horizon - no shadow
        if solar_elevation <= self.min_solar_elevation:
            return {
                "shadow_length_meters": 0.0,
                "shadow_azimuth_degrees": 0.0,
                "casts_shadow": False,
            }

        # Calculate shadow length using trigonometry
        # shadow_length = height / tan(elevation)
        elevation_rad = math.radians(solar_elevation)
        shadow_length = building_height / math.tan(elevation_rad)

        # Clip extremely long shadows at low sun angles
        if shadow_length > self.max_shadow_length:
            shadow_length = self.max_shadow_length

        # Shadow points opposite to sun direction
        # If sun is at azimuth 180° (south), shadow points north (0°)
        shadow_azimuth = (solar_azimuth + 180) % 360

        return {
            "shadow_length_meters": shadow_length,
            "shadow_azimuth_degrees": shadow_azimuth,
            "casts_shadow": True,
        }

    def generate_shadow_polygon(
        self,
        building_footprint: list[list[float]],  # [[lon, lat], ...]
        building_height: float,
        solar_elevation: float,
        solar_azimuth: float,
        centroid_lon: float,
        building_id: str = "unknown",
    ) -> dict[str, Any] | None:
        """
        Generate shadow polygon from building footprint and solar position.
        Removes building footprint from shadow to prevent overlap.

        Args:
            building_footprint: Building polygon coordinates in WGS84 [[lon, lat], ...]
            building_height: Height of building in meters
            solar_elevation: Solar elevation angle in degrees
            solar_azimuth: Solar azimuth angle in degrees
            centroid_lon: Longitude of building centroid for UTM zone selection
            building_id: Building identifier for logging

        Returns:
            Shadow polygon(s) as GeoJSON geometry or None if no shadow
        """
        # Calculate shadow metrics
        metrics = self.calculate_shadow_metrics(building_height, solar_elevation, solar_azimuth)

        if not metrics["casts_shadow"] or metrics["shadow_length_meters"] == 0:
            return None

        shadow_length = metrics["shadow_length_meters"]
        shadow_azimuth = metrics["shadow_azimuth_degrees"]

        try:
            # Create shapely polygon from footprint
            building_poly = Polygon([(coord[0], coord[1]) for coord in building_footprint])

            # Simplify building footprint for performance
            if self.simplification_tolerance > 0:
                building_poly = building_poly.simplify(
                    tolerance=self.simplification_tolerance
                    / 111000,  # Convert meters to degrees (approx)
                    preserve_topology=True,
                )

            # Determine UTM zone from centroid longitude
            utm_zone = int((centroid_lon + 180) / 6) + 1
            # Get first coordinate for latitude to determine hemisphere
            centroid_lat = building_footprint[0][1]
            hemisphere = "north" if centroid_lat >= 0 else "south"

            # Create transformer: WGS84 → UTM → WGS84
            wgs84 = pyproj.CRS("EPSG:4326")
            utm = pyproj.CRS(
                f"+proj=utm +zone={utm_zone} +{hemisphere} +datum=WGS84 +units=m +no_defs"
            )

            project_to_utm = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True).transform
            project_to_wgs84 = pyproj.Transformer.from_crs(utm, wgs84, always_xy=True).transform

            # Transform building polygon to UTM for meter-based calculations
            building_utm = transform(project_to_utm, building_poly)

            # Calculate shadow offset vector in meters
            # Azimuth is measured clockwise from north
            # Convert to radians and calculate x,y offsets
            azimuth_rad = math.radians(shadow_azimuth)
            offset_x = shadow_length * math.sin(azimuth_rad)
            offset_y = shadow_length * math.cos(azimuth_rad)

            # Create shadow polygon by offsetting all vertices
            building_coords = list(building_utm.exterior.coords)

            # NEW APPROACH: Create a swept shadow polygon, then use difference to remove building
            # This is cleaner than trying to construct only the shadow part
            shadow_coords = []

            # Build shadow polygon: building vertices + shadow-offset vertices
            # Connect: building[0] → building[1] → ... → building[n] →
            #          shadow[n] → shadow[n-1] → ... → shadow[0] → building[0]

            for coord in building_coords[:-1]:  # Exclude last (duplicate of first)
                shadow_coords.append(coord)

            # Add shadow-offset vertices in reverse order
            for coord in reversed(building_coords[:-1]):
                shadow_coords.append((coord[0] + offset_x, coord[1] + offset_y))

            # Close the polygon
            shadow_coords.append(shadow_coords[0])

            # Create shadow polygon in UTM
            shadow_swept_utm = Polygon(shadow_coords)

            # Ensure geometries are valid
            if not shadow_swept_utm.is_valid:
                shadow_swept_utm = shadow_swept_utm.buffer(0)  # Fix invalid geometry
            if not building_utm.is_valid:
                building_utm = building_utm.buffer(0)  # Fix invalid geometry

            # Remove building footprint from shadow IN UTM COORDINATES (Bug #2 Fix)
            try:
                # Use difference to remove building from swept shadow
                cleaned_shadow_utm = shadow_swept_utm.difference(building_utm)

                # Check if result is empty
                if cleaned_shadow_utm.is_empty:
                    logger.debug(
                        f"Shadow for building {building_id} completely overlaps building, skipping"
                    )
                    return None

                # Ensure result is valid
                if not cleaned_shadow_utm.is_valid:
                    cleaned_shadow_utm = cleaned_shadow_utm.buffer(0)

                # Check if result is too small
                shadow_area = (
                    cleaned_shadow_utm.area
                    if isinstance(cleaned_shadow_utm, Polygon)
                    else sum(g.area for g in cleaned_shadow_utm.geoms)
                )
                if shadow_area < self.min_shadow_area:
                    logger.debug(
                        f"Shadow for building {building_id} too small ({shadow_area:.2f} m²), skipping"
                    )
                    return None

            except Exception as e:
                logger.warning(f"Failed to remove building overlap for {building_id}: {str(e)}")
                return None

            # Handle both Polygon and MultiPolygon results
            shadow_features = []

            if isinstance(cleaned_shadow_utm, MultiPolygon):
                # Multiple shadow pieces - create separate features for each
                logger.debug(
                    f"Building {building_id} casts {len(cleaned_shadow_utm.geoms)} separate shadow pieces"
                )
                for geom_utm in cleaned_shadow_utm.geoms:
                    # Transform each piece back to WGS84
                    geom_wgs84 = transform(project_to_wgs84, geom_utm)
                    shadow_features.append(
                        {
                            "type": "Polygon",
                            "coordinates": [[list(coord) for coord in geom_wgs84.exterior.coords]],
                            "area_sq_meters": geom_utm.area,  # Area in square meters (already in UTM)
                            "shadow_length": shadow_length,
                            "shadow_azimuth": shadow_azimuth,
                        }
                    )
            else:
                # Single shadow piece - transform back to WGS84
                cleaned_shadow_wgs84 = transform(project_to_wgs84, cleaned_shadow_utm)
                shadow_features.append(
                    {
                        "type": "Polygon",
                        "coordinates": [
                            [list(coord) for coord in cleaned_shadow_wgs84.exterior.coords]
                        ],
                        "area_sq_meters": cleaned_shadow_utm.area,  # Area in square meters (already in UTM)
                        "shadow_length": shadow_length,
                        "shadow_azimuth": shadow_azimuth,
                    }
                )

            return shadow_features

        except Exception as e:
            logger.warning(
                f"Failed to generate shadow polygon for {building_id}: {str(e)}", exc_info=True
            )
            return None

    async def calculate_shadows_for_buildings(
        self,
        buildings: list[BuildingFeature],
        solar_elevation: float,
        solar_azimuth: float,
        timestamp: str,
        enrich_missing_heights: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Calculate shadows for multiple buildings using FACE-BASED shadow algorithm.
        Each building edge (face) casts a separate shadow.

        Args:
            buildings: List of building features with geometries and heights
            solar_elevation: Solar elevation angle in degrees
            solar_azimuth: Solar azimuth angle in degrees
            timestamp: ISO format timestamp string
            enrich_missing_heights: If True, query GEE for missing heights

        Returns:
            List of shadow features with geometries and properties
        """
        # Import face shadow engine
        from app.services.face_shadow_engine import compute_face_shadows

        # First pass: identify buildings without height data
        buildings_without_height = []
        for building in buildings:
            if building.properties.height is None or building.properties.height <= 0:
                buildings_without_height.append(building)

        # Enrich missing heights from GEE if requested
        if enrich_missing_heights and buildings_without_height:
            logger.info(
                f"Enriching heights for {len(buildings_without_height)} buildings from GEE Temporal V1"
            )
            await self._enrich_heights_from_gee(buildings_without_height)

        # Convert buildings to GeoJSON FeatureCollection format for face_shadow_engine
        buildings_fc = {"type": "FeatureCollection", "features": []}

        for building in buildings:
            # Use default height if still missing
            building_height = building.properties.height
            if building_height is None or building_height <= 0:
                building_height = self._get_default_height(
                    building.properties.building_type_normalized
                )

            feature = {
                "type": "Feature",
                "id": building.properties.osm_id or f"building_{id(building)}",
                "geometry": {"type": "Polygon", "coordinates": building.geometry.coordinates},
                "properties": {"height": building_height, "osm_id": building.properties.osm_id},
            }
            buildings_fc["features"].append(feature)

        # Use face-based shadow calculation
        logger.info(f"Calculating face-based shadows for {len(buildings)} buildings")
        shadows_fc = compute_face_shadows(
            buildings_fc=buildings_fc,
            sun_azimuth_deg=solar_azimuth,
            sun_elevation_deg=solar_elevation,
            height_attr="height",
            min_elev_deg=self.min_solar_elevation,
            max_shadow_length_m=self.max_shadow_length,
        )

        # Convert back to shadow features format and add opacity
        shadows = []
        for shadow_feature in shadows_fc.get("features", []):
            props = shadow_feature["properties"]

            # Skip fully overlapped shadows (empty geometry)
            if (
                props.get("was_fully_overlapped_by_self", False)
                and props.get("shadow_area_m2", 0) == 0
            ):
                continue

            shadow = {
                "type": "Feature",
                "geometry": shadow_feature["geometry"],
                "properties": {
                    "source_building_id": props["building_id"],
                    "face_index": props["face_index"],
                    "building_height": props["height_m"],
                    "shadow_length": props["shadow_length_m"],
                    "timestamp": timestamp,
                    "solar_elevation": solar_elevation,
                    "solar_azimuth": solar_azimuth,
                    "opacity": self.base_opacity,
                    "area_sq_meters": props["shadow_area_m2"],
                    "overlaps": props.get("overlaps", []),
                },
            }
            shadows.append(shadow)

        logger.info(f"Generated {len(shadows)} face shadows from {len(buildings)} buildings")

        # Calculate overlaps and adjust opacity (Phase 2: Cumulative Opacity)
        if shadows:
            shadows = self._calculate_shadow_overlaps(shadows)

        return shadows

    def _calculate_shadow_overlaps(self, shadows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Detect shadow overlaps and adjust opacity using logarithmic scaling.

        Args:
            shadows: List of shadow features

        Returns:
            Shadow features with adjusted opacity based on overlaps
        """
        if len(shadows) <= 1:
            return shadows

        try:
            # Create shapely polygons and spatial index
            shadow_polygons = []
            for shadow in shadows:
                coords = shadow["geometry"]["coordinates"][0]
                poly = Polygon([(c[0], c[1]) for c in coords])
                shadow_polygons.append(poly)

            # Build spatial index for fast queries
            tree = STRtree(shadow_polygons)

            # For each shadow, count how many other shadows it overlaps with
            for idx, shadow in enumerate(shadows):
                poly = shadow_polygons[idx]

                # Query spatial index for potential overlaps
                potential_overlaps = tree.query(poly)

                # Count actual overlaps (excluding self)
                overlap_count = 0
                for other_idx in potential_overlaps:
                    if other_idx != idx and poly.intersects(shadow_polygons[other_idx]):
                        overlap_count += 1

                # Apply logarithmic opacity scaling
                # 0 overlaps: 0.75, 1 overlap: 0.825, 2: 0.875, 3: 0.9125, 4+: 0.95
                if overlap_count == 0:
                    opacity = self.base_opacity
                else:
                    # Logarithmic formula: base + (max - base) * (1 - 1/2^overlap_count)
                    opacity = self.base_opacity + (self.max_opacity - self.base_opacity) * (
                        1 - 1 / (2**overlap_count)
                    )
                    opacity = min(opacity, self.max_opacity)

                shadow["properties"]["opacity"] = round(opacity, 3)
                shadow["properties"]["overlap_count"] = overlap_count

            logger.info(f"Calculated overlaps for {len(shadows)} shadows")

        except Exception as e:
            logger.warning(f"Failed to calculate shadow overlaps: {str(e)}")

        return shadows

    async def _enrich_heights_from_gee(self, buildings: list[BuildingFeature]):
        """Query GEE Temporal V1 for building heights."""
        try:
            # Ensure GEE is initialized (singleton pattern ensures this only happens once)
            if not self.gee_service.initialized:
                logger.info("Initializing GEE service for shadow height enrichment")
                self.gee_service.initialize()

            for building in buildings:
                try:
                    # Sample height from GEE
                    geometry = {
                        "type": "Polygon",
                        "coordinates": [building.geometry.coordinates[0]],
                    }
                    height = self.gee_service.sample_height_within_footprint(geometry, num_points=3)

                    if height and height > 0:
                        building.properties.height = height
                        # Estimate floors if not present
                        if not building.properties.floors:
                            building.properties.floors = max(1, int(height / 3.0))

                except Exception as e:
                    logger.debug(f"Failed to sample height for building: {str(e)}")
                    continue

        except Exception as e:
            logger.warning(f"Failed to enrich heights from GEE: {str(e)}")

    def _get_default_height(self, building_category: str) -> float:
        """Get default height for building based on category."""
        category_map = settings.SHADOW_DEFAULT_HEIGHTS

        # Handle None or empty category
        if not building_category:
            return category_map["other"]["default"]

        if building_category in category_map:
            return category_map[building_category].get("default", 10.0)

        return category_map["other"]["default"]

    def calculate_total_shadow_area(self, shadows: list[dict[str, Any]]) -> float:
        """
        Calculate total shadow area including overlaps.

        Args:
            shadows: List of shadow features

        Returns:
            Total shadow area in square meters
        """
        if not shadows:
            return 0.0

        try:
            polygons = []
            for shadow in shadows:
                coords = shadow["geometry"]["coordinates"][0]
                poly = Polygon([(c[0], c[1]) for c in coords])
                polygons.append(poly)

            # Union all shadow polygons
            union = unary_union(polygons)

            # Calculate area (approximate using local UTM)
            if not polygons:
                return 0.0

            # Get centroid of first polygon for UTM zone
            centroid = polygons[0].centroid
            utm_zone = int((centroid.x + 180) / 6) + 1
            hemisphere = "north" if centroid.y >= 0 else "south"

            wgs84 = pyproj.CRS("EPSG:4326")
            utm = pyproj.CRS(
                f"+proj=utm +zone={utm_zone} +{hemisphere} +datum=WGS84 +units=m +no_defs"
            )

            project = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True).transform
            union_utm = transform(project, union)

            return union_utm.area

        except Exception as e:
            logger.warning(f"Failed to calculate total shadow area: {str(e)}")
            return sum(s["properties"].get("area_sq_meters", 0) for s in shadows)
