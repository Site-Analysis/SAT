"""Google Earth Engine service for building data extraction."""

import os
from typing import Any

import ee
from app.core.config import settings
from app.core.exceptions import GEEServiceError
from app.core.logging import get_logger
from shapely.geometry import Point, Polygon

logger = get_logger(__name__)


class GEEService:
    """Service for querying Google Earth Engine building datasets."""

    _instance = None

    def __new__(cls):
        """Singleton pattern - ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.initialized = False
            cls._instance.open_buildings_v3 = None
            cls._instance.open_buildings_temporal = None
        return cls._instance

    def __init__(self):
        """Initialize the GEE service (only runs once due to singleton)."""
        pass

    def initialize(self):
        """Initialize and authenticate with Google Earth Engine."""
        if self.initialized:
            return

        try:
            logger.info("Initializing Google Earth Engine")

            # Resolve the path to the GEE JSON file (handle relative paths)
            gee_json_path = settings.GEE_JSON_PATH
            if not os.path.isabs(gee_json_path):
                # If relative path, resolve from the backend root directory
                backend_root = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                gee_json_path = os.path.join(backend_root, gee_json_path)

            # Check if service account JSON exists
            if not settings.GEE_JSON_PATH:
                raise GEEServiceError("GEE_JSON_PATH not configured")

            if not os.path.exists(gee_json_path):
                raise GEEServiceError(f"GEE service account JSON not found at: {gee_json_path}")

            logger.info(f"Loading GEE credentials from: {gee_json_path}")

            # Authenticate with service account
            credentials = ee.ServiceAccountCredentials(
                email=None,  # Will be read from JSON
                key_file=gee_json_path,
            )
            ee.Initialize(credentials)

            # Load datasets
            self.open_buildings_v3 = ee.FeatureCollection(
                "GOOGLE/Research/open-buildings/v3/polygons"
            )
            self.open_buildings_temporal = ee.ImageCollection(
                "GOOGLE/Research/open-buildings-temporal/v1"
            )

            self.initialized = True
            logger.info("Google Earth Engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize GEE: {str(e)}", exc_info=True)
            raise GEEServiceError(f"Failed to initialize Google Earth Engine: {str(e)}")

    def get_building_footprints(
        self, bbox: tuple[float, float, float, float]
    ) -> list[dict[str, Any]]:
        """
        Query Open Buildings V3 for building footprints within a bounding box.

        Args:
            bbox: Bounding box as (min_lon, min_lat, max_lon, max_lat)

        Returns:
            List of building dictionaries with geometry and properties
        """
        try:
            if not self.initialized:
                self.initialize()

            min_lon, min_lat, max_lon, max_lat = bbox
            logger.info(f"Querying GEE Open Buildings V3 for bbox: {bbox}")

            # Create bounding box geometry
            bbox_geom = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])

            # Filter buildings within bbox
            buildings = self.open_buildings_v3.filterBounds(bbox_geom)

            # Limit to reasonable number to avoid timeout
            buildings = buildings.limit(5000)

            # Get features
            features = buildings.getInfo()

            if not features or "features" not in features:
                logger.warning("No buildings found in GEE Open Buildings V3")
                return []

            building_list = []
            for feature in features["features"]:
                try:
                    geometry = feature.get("geometry")
                    properties = feature.get("properties", {})

                    if not geometry:
                        continue

                    building_data = {
                        "geometry": geometry,
                        "area_in_meters": properties.get("area_in_meters"),
                        "confidence": properties.get("confidence"),
                        "full_plus_code": properties.get("full_plus_code"),
                        "longitude_latitude": properties.get("longitude_latitude"),
                    }
                    building_list.append(building_data)

                except Exception as e:
                    logger.warning(f"Failed to parse GEE building feature: {str(e)}")
                    continue

            logger.info(f"Retrieved {len(building_list)} buildings from GEE")
            return building_list

        except Exception as e:
            logger.error(f"Failed to query GEE Open Buildings V3: {str(e)}", exc_info=True)
            raise GEEServiceError(f"Failed to query building footprints: {str(e)}")

    def get_building_height(self, geometry: dict[str, Any]) -> float | None:
        """
        Sample building height from Open Buildings Temporal V1.

        Args:
            geometry: GeoJSON geometry of the building

        Returns:
            Average height in meters or None if sampling fails
        """
        try:
            if not self.initialized:
                self.initialize()

            # Convert geometry to EE geometry
            if geometry["type"] == "Polygon":
                coords = geometry["coordinates"][0]
                ee_geom = ee.Geometry.Polygon(coords)
            else:
                logger.warning(f"Unsupported geometry type: {geometry['type']}")
                return None

            # Get the most recent image
            image = self.open_buildings_temporal.select("building_height").mosaic()

            # Sample multiple points within the polygon
            ee_geom.centroid(1).buffer(10).bounds()

            # Reduce region to get mean height
            stats = image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=ee_geom,
                scale=4,  # 4 meter resolution
                maxPixels=1e9,
            )

            height_info = stats.getInfo()
            height = height_info.get("building_height")

            if height is not None and height > 0:
                return round(float(height), 2)

            return None

        except Exception as e:
            logger.debug(f"Failed to sample height for building: {str(e)}")
            return None

    def sample_heights_at_points(self, points: list[tuple[float, float]]) -> list[float | None]:
        """
        Sample building heights at multiple point locations.

        Args:
            points: List of (lon, lat) tuples

        Returns:
            List of heights in meters (None if no data)
        """
        try:
            if not self.initialized:
                self.initialize()

            if not points:
                return []

            logger.debug(f"Sampling heights at {len(points)} points")

            # Create feature collection from points
            features = [
                ee.Feature(ee.Geometry.Point([lon, lat]), {"index": i})
                for i, (lon, lat) in enumerate(points)
            ]
            points_fc = ee.FeatureCollection(features)

            # Get the most recent image
            image = self.open_buildings_temporal.select("building_height").mosaic()

            # Sample at points
            sampled = image.sampleRegions(collection=points_fc, scale=4, geometries=True)

            # Get results
            sampled_info = sampled.getInfo()

            # Create results array with None defaults
            heights = [None] * len(points)

            if sampled_info and "features" in sampled_info:
                for feature in sampled_info["features"]:
                    props = feature.get("properties", {})
                    index = props.get("index")
                    height = props.get("building_height")

                    if index is not None and height is not None and height > 0:
                        heights[index] = round(float(height), 2)

            return heights

        except Exception as e:
            logger.warning(f"Failed to sample heights at points: {str(e)}")
            return [None] * len(points)

    def sample_height_within_footprint(
        self, geometry: dict[str, Any], num_points: int = 5
    ) -> float | None:
        """
        Sample building height at multiple points within a footprint and return average.

        Args:
            geometry: GeoJSON geometry of the building
            num_points: Number of points to sample

        Returns:
            Average height in meters or None
        """
        try:
            # Convert to shapely polygon
            if geometry["type"] != "Polygon":
                return None

            coords = geometry["coordinates"][0]
            poly = Polygon(coords)

            # Generate sample points within polygon
            bounds = poly.bounds
            min_x, min_y, max_x, max_y = bounds

            sample_points = []
            attempts = 0
            max_attempts = num_points * 10

            # Generate random points within polygon
            import random

            while len(sample_points) < num_points and attempts < max_attempts:
                x = random.uniform(min_x, max_x)
                y = random.uniform(min_y, max_y)
                point = Point(x, y)

                if poly.contains(point):
                    sample_points.append((x, y))

                attempts += 1

            if not sample_points:
                # Fallback to centroid
                centroid = poly.centroid
                sample_points = [(centroid.x, centroid.y)]

            # Sample heights at these points
            heights = self.sample_heights_at_points(sample_points)

            # Calculate average of non-None values
            valid_heights = [h for h in heights if h is not None]

            if valid_heights:
                return round(sum(valid_heights) / len(valid_heights), 2)

            return None

        except Exception as e:
            logger.debug(f"Failed to sample height within footprint: {str(e)}")
            return None
