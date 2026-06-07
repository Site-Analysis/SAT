"""
Time-series shadow analysis service (Phase 3).
Calculates shadows over time periods and cumulative shadow coverage.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd
import pvlib
import pyproj
from app.core.logging import get_logger
from app.models.building_models import BuildingFeature
from app.models.shadow_models import DurationCategory
from app.services.shadow_engine import ShadowEngine
from shapely.geometry import Polygon
from shapely.ops import transform, unary_union

logger = get_logger(__name__)


class ShadowTimeseriesService:
    """Service for calculating shadows over time periods."""

    def __init__(self, shadow_engine: ShadowEngine):
        """Initialize with shadow engine."""
        self.shadow_engine = shadow_engine

    def generate_time_range(
        self, start_datetime: datetime, end_datetime: datetime, interval_minutes: int
    ) -> list[datetime]:
        """
        Generate list of timestamps at specified interval.

        Args:
            start_datetime: Start timestamp
            end_datetime: End timestamp
            interval_minutes: Interval in minutes

        Returns:
            List of datetime objects
        """
        timestamps = []
        current = start_datetime

        while current <= end_datetime:
            timestamps.append(current)
            current += timedelta(minutes=interval_minutes)

        return timestamps

    def get_solar_positions(
        self, timestamps: list[datetime], latitude: float, longitude: float
    ) -> pd.DataFrame:
        """
        Calculate solar positions for multiple timestamps.

        Args:
            timestamps: List of datetime objects (assumed to be LOCAL time for the location)
            latitude: Location latitude
            longitude: Location longitude

        Returns:
            DataFrame with elevation, azimuth, zenith columns
        """
        # Determine timezone from longitude (approximate)
        # UTC offset = longitude / 15 (each 15 degrees = 1 hour)
        # This is an approximation; for precise results, use a timezone database
        utc_offset_hours = round(longitude / 15)
        local_tz = timezone(timedelta(hours=utc_offset_hours))

        logger.info(f"Using UTC offset {utc_offset_hours:+d} hours for longitude {longitude:.2f}")

        # Localize naive timestamps to the location's timezone
        localized_timestamps = []
        for ts in timestamps:
            if ts.tzinfo is None:
                # Naive datetime - assume it's local time for the location
                localized_ts = ts.replace(tzinfo=local_tz)
            else:
                localized_ts = ts
            localized_timestamps.append(localized_ts)

        # Create pandas DatetimeIndex with timezone info
        times = pd.DatetimeIndex(localized_timestamps)

        # Calculate solar position - pvlib handles timezone-aware timestamps correctly
        solar_position = pvlib.solarposition.get_solarposition(
            times, latitude, longitude, method="nrel_numpy"
        )

        return solar_position

    async def calculate_timeseries_shadows(
        self,
        buildings: list[BuildingFeature],
        timestamps: list[datetime],
        latitude: float,
        longitude: float,
        enrich_missing_heights: bool = True,
    ) -> list[dict[str, Any]]:
        """
        Calculate shadows for buildings across multiple timestamps.

        Args:
            buildings: List of building features
            timestamps: List of datetime objects (assumed to be LOCAL time)
            latitude: Location latitude
            longitude: Location longitude
            enrich_missing_heights: Whether to query GEE for missing heights

        Returns:
            List of shadow snapshots, one per timestamp
        """
        snapshots = []

        # Get solar positions for all timestamps
        logger.info(f"Calculating solar positions for {len(timestamps)} timestamps")
        solar_positions = self.get_solar_positions(timestamps, latitude, longitude)

        # Filter out nighttime (sun below horizon)
        valid_mask = solar_positions["elevation"] > self.shadow_engine.min_solar_elevation
        valid_solar_positions = solar_positions[valid_mask]

        if valid_solar_positions.empty:
            logger.warning("No valid timestamps (sun above horizon) in requested range")
            return []

        logger.info(f"Processing {len(valid_solar_positions)} timestamps with sun above horizon")

        # Calculate shadows for each valid timestamp
        for idx, (ts_index, solar_pos) in enumerate(valid_solar_positions.iterrows()):
            # Use original timestamp for display (local time)
            timestamp_str = ts_index.strftime("%Y-%m-%dT%H:%M:%S")

            elevation = float(solar_pos["elevation"])
            azimuth = float(solar_pos["azimuth"])
            zenith = float(solar_pos["zenith"])

            logger.debug(
                f"Timestamp {timestamp_str}: elevation={elevation:.1f}°, azimuth={azimuth:.1f}°"
            )

            # Calculate shadows
            shadows = await self.shadow_engine.calculate_shadows_for_buildings(
                buildings=buildings,
                solar_elevation=elevation,
                solar_azimuth=azimuth,
                timestamp=timestamp_str,
                enrich_missing_heights=enrich_missing_heights
                and len(snapshots) == 0,  # Only enrich on first iteration
            )

            # Create snapshot
            snapshot = {
                "timestamp": timestamp_str,
                "solar_position": {
                    "elevation": round(elevation, 2),
                    "azimuth": round(azimuth, 2),
                    "zenith": round(zenith, 2),
                },
                "shadows": {"type": "FeatureCollection", "features": shadows},
                "metadata": {
                    "shadow_count": len(shadows),
                    "total_shadow_area_sq_meters": round(
                        self.shadow_engine.calculate_total_shadow_area(shadows), 2
                    ),
                },
            }

            snapshots.append(snapshot)

            logger.info(
                f"Calculated {len(shadows)} shadows for {timestamp_str} (elev={elevation:.1f}°)"
            )

        return snapshots

    async def calculate_cumulative_shadows(
        self,
        buildings: list[BuildingFeature],
        date: str,
        latitude: float,
        longitude: float,
        interval_minutes: int = 30,
        enrich_missing_heights: bool = True,
    ) -> dict[str, Any]:
        """
        Calculate cumulative shadow coverage for a full day.

        Args:
            buildings: List of building features
            date: Date string in YYYY-MM-DD format
            latitude: Location latitude
            longitude: Location longitude
            interval_minutes: Time interval for sampling
            enrich_missing_heights: Whether to query GEE for missing heights

        Returns:
            Dictionary with coverage zones categorized by duration
        """
        # Parse date and calculate sunrise/sunset
        date_obj = datetime.fromisoformat(date)

        # Get sunrise and sunset times
        times = pd.DatetimeIndex([date_obj])
        pvlib.solarposition.get_solarposition(times, latitude, longitude)

        # Calculate day timestamps from sunrise to sunset
        # Use full day for now (00:00 to 23:59)
        start_datetime = datetime.combine(date_obj.date(), datetime.min.time())
        end_datetime = datetime.combine(
            date_obj.date(), datetime.max.time().replace(second=0, microsecond=0)
        )

        # Generate timestamps
        timestamps = self.generate_time_range(start_datetime, end_datetime, interval_minutes)

        # Calculate shadows for all timestamps
        logger.info(f"Calculating cumulative shadows for {date} with {len(timestamps)} snapshots")
        snapshots = await self.calculate_timeseries_shadows(
            buildings=buildings,
            timestamps=timestamps,
            latitude=latitude,
            longitude=longitude,
            enrich_missing_heights=enrich_missing_heights,
        )

        if not snapshots:
            return {
                "coverage_zones": [],
                "metadata": {
                    "date": date,
                    "sunrise": "N/A",
                    "sunset": "N/A",
                    "total_snapshots": 0,
                    "total_buildings": len(buildings),
                    "total_shadow_area_sq_meters": 0.0,
                    "max_shadow_hours": 0.0,
                },
            }

        # Calculate shadow duration for each spatial area
        shadow_duration_map = self._calculate_shadow_duration_map(snapshots, interval_minutes)

        # Create coverage zones by duration category
        coverage_zones = self._create_coverage_zones(shadow_duration_map)

        # Calculate metadata
        total_shadow_area = sum(zone["area_sq_meters"] for zone in coverage_zones)
        max_hours = max((zone["hours_range"][1] for zone in coverage_zones), default=0.0)

        # Find actual sunrise/sunset from snapshots
        sunrise = snapshots[0]["timestamp"] if snapshots else "N/A"
        sunset = snapshots[-1]["timestamp"] if snapshots else "N/A"

        return {
            "coverage_zones": coverage_zones,
            "metadata": {
                "date": date,
                "sunrise": sunrise,
                "sunset": sunset,
                "total_snapshots": len(snapshots),
                "total_buildings": len(buildings),
                "total_shadow_area_sq_meters": round(total_shadow_area, 2),
                "max_shadow_hours": round(max_hours, 2),
            },
        }

    def _calculate_shadow_duration_map(
        self, snapshots: list[dict[str, Any]], interval_minutes: int
    ) -> dict[str, float]:
        """
        Calculate how many hours each area was in shadow.

        Args:
            snapshots: List of shadow snapshots
            interval_minutes: Time interval between snapshots

        Returns:
            Dictionary mapping polygon WKT to hours in shadow
        """
        # Collect all unique shadow polygons with their count
        shadow_areas = {}  # polygon_wkt -> count

        for snapshot in snapshots:
            shadows = snapshot["shadows"]["features"]

            for shadow in shadows:
                coords = shadow["geometry"]["coordinates"][0]
                poly = Polygon([(c[0], c[1]) for c in coords])

                # Use WKT as key (can be slow for large datasets, but works for now)
                poly_wkt = poly.wkt

                if poly_wkt in shadow_areas:
                    shadow_areas[poly_wkt]["count"] += 1
                    shadow_areas[poly_wkt]["polygons"].append(poly)
                else:
                    shadow_areas[poly_wkt] = {
                        "count": 1,
                        "polygons": [poly],
                        "geometry": shadow["geometry"],
                    }

        # Convert counts to hours
        hours_per_snapshot = interval_minutes / 60.0

        for poly_wkt in shadow_areas:
            count = shadow_areas[poly_wkt]["count"]
            shadow_areas[poly_wkt]["hours"] = count * hours_per_snapshot

        return shadow_areas

    def _create_coverage_zones(self, shadow_duration_map: dict[str, float]) -> list[dict[str, Any]]:
        """
        Group shadow areas by duration category and create simplified polygons.

        Args:
            shadow_duration_map: Map of polygon WKT to shadow data

        Returns:
            List of coverage zones with duration categories
        """
        # Define duration categories
        categories = [
            (DurationCategory.ZERO_TO_TWO, 0.0, 2.0, "#E8E8E8", 0.3),
            (DurationCategory.TWO_TO_FOUR, 2.0, 4.0, "#C0C0C0", 0.45),
            (DurationCategory.FOUR_TO_SIX, 4.0, 6.0, "#989898", 0.6),
            (DurationCategory.SIX_TO_EIGHT, 6.0, 8.0, "#707070", 0.75),
            (DurationCategory.EIGHT_PLUS, 8.0, float("inf"), "#484848", 0.9),
        ]

        coverage_zones = []

        for category, min_hours, max_hours, color, opacity in categories:
            # Collect polygons in this duration range
            polygons_in_range = []

            for poly_wkt, data in shadow_duration_map.items():
                hours = data["hours"]
                if min_hours <= hours < max_hours:
                    polygons_in_range.extend(data["polygons"])

            if not polygons_in_range:
                continue

            # Union all polygons in this category
            try:
                union_poly = unary_union(polygons_in_range)

                # Calculate area in square meters
                # Use UTM projection for accurate area
                if polygons_in_range:
                    centroid = polygons_in_range[0].centroid
                    utm_zone = int((centroid.x + 180) / 6) + 1
                    hemisphere = "north" if centroid.y >= 0 else "south"

                    wgs84 = pyproj.CRS("EPSG:4326")
                    utm = pyproj.CRS(
                        f"+proj=utm +zone={utm_zone} +{hemisphere} +datum=WGS84 +units=m +no_defs"
                    )

                    project = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True).transform
                    union_utm = transform(project, union_poly)
                    area_sq_meters = union_utm.area
                else:
                    area_sq_meters = 0.0

                # Convert to GeoJSON
                if union_poly.geom_type == "Polygon":
                    coords = list(union_poly.exterior.coords)
                    geojson_geom = {
                        "type": "Polygon",
                        "coordinates": [[list(coord) for coord in coords]],
                    }
                elif union_poly.geom_type == "MultiPolygon":
                    geojson_geom = {
                        "type": "MultiPolygon",
                        "coordinates": [
                            [[list(coord) for coord in poly.exterior.coords]]
                            for poly in union_poly.geoms
                        ],
                    }
                else:
                    continue

                coverage_zone = {
                    "duration_category": category.value,
                    "hours_range": [min_hours, max_hours if max_hours != float("inf") else 24.0],
                    "polygon": geojson_geom,
                    "area_sq_meters": round(area_sq_meters, 2),
                    "color": color,
                    "opacity": opacity,
                }

                coverage_zones.append(coverage_zone)

            except Exception as e:
                logger.warning(f"Failed to create coverage zone for {category.value}: {str(e)}")
                continue

        return coverage_zones
