# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

"""
Overpass API service for querying OpenStreetMap building data.
Implements tiling for large areas and parallel fetching for performance.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

import requests
from app.core.config import settings
from app.core.exceptions import BuildingExtractionError
from app.models.building_models import BuildingCategory
from shapely.geometry import Point, Polygon, box

logger = logging.getLogger(__name__)


@dataclass
class OverpassBuilding:
    """Raw building data from Overpass API."""

    osm_id: str
    geometry: list[list[float]]  # [lon, lat] coordinates
    tags: dict[str, str]
    centroid: tuple[float, float]  # (lon, lat)


class OverpassService:
    """Service for querying OpenStreetMap building data via Overpass API."""

    def __init__(self):
        self.overpass_url = settings.OVERPASS_API_URL
        self.timeout = settings.OVERPASS_TIMEOUT_SECONDS
        self.tile_size = settings.OVERPASS_TILE_SIZE_DEGREES
        self.max_concurrent = settings.OVERPASS_MAX_CONCURRENT_REQUESTS
        self._headers = {
            "User-Agent": "SAT-Platform/1.0 (site-analysis-tool; contact@sat-platform.dev)"
        }

    def query_buildings(
        self,
        bbox: tuple[float, float, float, float] | None = None,
        polygon: list[list[float]] | None = None,
    ) -> list[OverpassBuilding]:
        """
        Query buildings from Overpass API.

        Args:
            bbox: Bounding box as (min_lat, min_lon, max_lat, max_lon)
            polygon: Custom polygon as list of [lon, lat] coordinates

        Returns:
            List of OverpassBuilding objects

        Raises:
            BuildingExtractionError: If Overpass query fails
        """
        try:
            if polygon:
                return self._query_with_polygon(polygon)
            elif bbox:
                return self._query_with_bbox(bbox)
            else:
                raise BuildingExtractionError("Either bbox or polygon must be provided")

        except requests.exceptions.RequestException as e:
            logger.error(f"Overpass API request failed: {e}")
            raise BuildingExtractionError(f"Failed to query Overpass API: {str(e)}")

    def _query_with_bbox(self, bbox: tuple[float, float, float, float]) -> list[OverpassBuilding]:
        """Query buildings within a bounding box, using tiling if necessary."""
        min_lat, min_lon, max_lat, max_lon = bbox

        # Calculate area to decide if tiling is needed
        area_degrees_sq = (max_lat - min_lat) * (max_lon - min_lon)

        # If area is small enough, query directly
        if area_degrees_sq <= (self.tile_size * self.tile_size * 4):  # ~4 tiles worth
            logger.info(f"Querying Overpass API directly for bbox: {bbox}")
            return self._fetch_buildings_in_bbox(bbox)

        # Split into tiles for larger areas
        logger.info(f"Splitting large area into tiles (size: {self.tile_size}°)")
        tiles = self._split_bbox_into_tiles(bbox)
        return self._fetch_tiles_parallel(tiles)

    def _query_with_polygon(self, polygon: list[list[float]]) -> list[OverpassBuilding]:
        """Query buildings within a polygon, using tiling if necessary."""
        # Convert to shapely polygon
        poly = Polygon([(coord[0], coord[1]) for coord in polygon])

        # Get bounding box of polygon
        bounds = poly.bounds  # (minx, miny, maxx, maxy)
        bbox = (
            bounds[1],
            bounds[0],
            bounds[3],
            bounds[2],
        )  # Convert to (min_lat, min_lon, max_lat, max_lon)

        area_degrees_sq = (bounds[3] - bounds[1]) * (bounds[2] - bounds[0])

        # If area is small enough, query directly with polygon filter
        if area_degrees_sq <= (self.tile_size * self.tile_size * 4):
            logger.info("Querying Overpass API directly with polygon filter")
            return self._fetch_buildings_in_polygon(polygon)

        # Split bounding box into tiles and filter by polygon
        logger.info("Splitting large polygon area into tiles")
        tiles = self._split_bbox_into_tiles(bbox)

        # Filter tiles that intersect with polygon
        intersecting_tiles = []
        for tile_bbox in tiles:
            tile_poly = box(
                tile_bbox[1], tile_bbox[0], tile_bbox[3], tile_bbox[2]
            )  # box(minx, miny, maxx, maxy)
            if tile_poly.intersects(poly):
                intersecting_tiles.append(tile_bbox)

        logger.info(f"Found {len(intersecting_tiles)} tiles intersecting with polygon")
        buildings = self._fetch_tiles_parallel(intersecting_tiles)

        # Filter buildings to only include those within the polygon
        filtered_buildings = []
        for building in buildings:
            # Check if building centroid is within polygon
            point = Point(building.centroid[0], building.centroid[1])
            if poly.contains(point):
                filtered_buildings.append(building)

        logger.info(
            f"Filtered {len(filtered_buildings)} buildings within polygon from {len(buildings)} total"
        )
        return filtered_buildings

    def _split_bbox_into_tiles(
        self, bbox: tuple[float, float, float, float]
    ) -> list[tuple[float, float, float, float]]:
        """Split a bounding box into smaller tiles."""
        min_lat, min_lon, max_lat, max_lon = bbox
        tiles = []

        lat = min_lat
        while lat < max_lat:
            lon = min_lon
            while lon < max_lon:
                tile_max_lat = min(lat + self.tile_size, max_lat)
                tile_max_lon = min(lon + self.tile_size, max_lon)
                tiles.append((lat, lon, tile_max_lat, tile_max_lon))
                lon += self.tile_size
            lat += self.tile_size

        logger.info(f"Split bbox into {len(tiles)} tiles")
        return tiles

    def _fetch_tiles_parallel(
        self, tiles: list[tuple[float, float, float, float]]
    ) -> list[OverpassBuilding]:
        """Fetch buildings from multiple tiles concurrently via a thread pool.

        Uses threads rather than a nested asyncio event loop, so it is safe to
        call from inside FastAPI's already-running loop (the previous
        ``asyncio.new_event_loop().run_until_complete(...)`` raised RuntimeError
        for any area large enough to trigger tiling, i.e. radius ≳ 700 m).
        """
        all_buildings: list[OverpassBuilding] = []

        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            futures = {executor.submit(self._fetch_buildings_in_bbox, tile): tile for tile in tiles}
            for future in as_completed(futures):
                try:
                    all_buildings.extend(future.result())
                except Exception as exc:  # noqa: BLE001
                    logger.warning(f"Tile fetch failed for {futures[future]}: {exc}")

        # Remove duplicates (buildings on tile boundaries)
        unique_buildings = self._deduplicate_buildings(all_buildings)
        logger.info(f"Fetched {len(unique_buildings)} unique buildings from {len(tiles)} tiles")
        return unique_buildings

    def _fetch_buildings_in_bbox(
        self, bbox: tuple[float, float, float, float]
    ) -> list[OverpassBuilding]:
        """Fetch buildings from Overpass API for a single bounding box."""
        min_lat, min_lon, max_lat, max_lon = bbox

        # Overpass QL query for buildings
        query = f"""
        [out:json][timeout:{self.timeout}];
        (
          way["building"]({min_lat},{min_lon},{max_lat},{max_lon});
          relation["building"]({min_lat},{min_lon},{max_lat},{max_lon});
        );
        out body;
        >;
        out skel qt;
        """

        try:
            response = requests.post(
                self.overpass_url, data={"data": query}, headers=self._headers, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            return self._parse_overpass_response(data)

        except requests.exceptions.Timeout:
            logger.warning(f"Overpass query timeout for bbox: {bbox}")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Overpass request failed for bbox {bbox}: {e}")
            raise BuildingExtractionError(f"Overpass API request failed: {str(e)}")

    def _fetch_buildings_in_polygon(self, polygon: list[list[float]]) -> list[OverpassBuilding]:
        """Fetch buildings from Overpass API within a polygon."""
        # Convert polygon coordinates to Overpass polygon format
        poly_str = " ".join([f"{coord[1]} {coord[0]}" for coord in polygon])

        query = f"""
        [out:json][timeout:{self.timeout}];
        (
          way["building"](poly:"{poly_str}");
          relation["building"](poly:"{poly_str}");
        );
        out body;
        >;
        out skel qt;
        """

        try:
            response = requests.post(
                self.overpass_url, data={"data": query}, headers=self._headers, timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            return self._parse_overpass_response(data)

        except requests.exceptions.Timeout:
            logger.warning("Overpass query timeout for polygon")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"Overpass request failed for polygon: {e}")
            raise BuildingExtractionError(f"Overpass API request failed: {str(e)}")

    def _parse_overpass_response(self, data: dict[str, Any]) -> list[OverpassBuilding]:
        """Parse Overpass API JSON response into OverpassBuilding objects."""
        buildings = []

        # Create lookup for nodes
        nodes = {}
        for element in data.get("elements", []):
            if element["type"] == "node":
                nodes[element["id"]] = (element["lon"], element["lat"])

        # Process ways and relations
        for element in data.get("elements", []):
            if element["type"] == "way" and "building" in element.get("tags", {}):
                # Get coordinates from node references
                if "nodes" in element:
                    coords = []
                    for node_id in element["nodes"]:
                        if node_id in nodes:
                            coords.append(list(nodes[node_id]))

                    if len(coords) >= 3:  # Valid polygon
                        # Ensure closed polygon
                        if coords[0] != coords[-1]:
                            coords.append(coords[0])

                        # Calculate centroid
                        centroid = self._calculate_centroid(coords)

                        buildings.append(
                            OverpassBuilding(
                                osm_id=f"way/{element['id']}",
                                geometry=coords,
                                tags=element.get("tags", {}),
                                centroid=centroid,
                            )
                        )

            elif element["type"] == "relation" and "building" in element.get("tags", {}):
                # Handle multipolygon relations
                # For simplicity, we'll use the outer way coordinates
                outer_coords = []
                for member in element.get("members", []):
                    if member.get("role") == "outer" and member["type"] == "way":
                        way_id = member["ref"]
                        # Find the way in elements
                        for way_element in data.get("elements", []):
                            if way_element["type"] == "way" and way_element["id"] == way_id:
                                if "nodes" in way_element:
                                    coords = []
                                    for node_id in way_element["nodes"]:
                                        if node_id in nodes:
                                            coords.append(list(nodes[node_id]))
                                    outer_coords.extend(coords)
                                break

                if len(outer_coords) >= 3:
                    # Ensure closed polygon
                    if outer_coords[0] != outer_coords[-1]:
                        outer_coords.append(outer_coords[0])

                    centroid = self._calculate_centroid(outer_coords)

                    buildings.append(
                        OverpassBuilding(
                            osm_id=f"relation/{element['id']}",
                            geometry=outer_coords,
                            tags=element.get("tags", {}),
                            centroid=centroid,
                        )
                    )

        return buildings

    def _calculate_centroid(self, coords: list[list[float]]) -> tuple[float, float]:
        """Calculate centroid of a polygon."""
        if not coords:
            return (0.0, 0.0)

        try:
            poly = Polygon([(c[0], c[1]) for c in coords])
            centroid = poly.centroid
            return (centroid.x, centroid.y)
        except Exception as e:
            logger.warning(f"Failed to calculate centroid: {e}, using first coordinate")
            return (coords[0][0], coords[0][1])

    def _deduplicate_buildings(self, buildings: list[OverpassBuilding]) -> list[OverpassBuilding]:
        """Remove duplicate buildings based on OSM ID."""
        seen_ids = set()
        unique = []

        for building in buildings:
            if building.osm_id not in seen_ids:
                seen_ids.add(building.osm_id)
                unique.append(building)

        return unique

    @staticmethod
    def normalize_building_category(tags: dict[str, str]) -> BuildingCategory:
        """
        Normalize OSM building tags to standard categories.

        Args:
            tags: OSM tags dictionary

        Returns:
            Normalized BuildingCategory
        """
        building_value = tags.get("building", "").lower()

        # Residential
        residential_types = {
            "house",
            "detached",
            "semidetached_house",
            "terrace",
            "apartments",
            "residential",
            "bungalow",
            "cabin",
            "dormitory",
            "dwelling",
            "home",
            "villa",
            "chalet",
            "manor",
            "dwelling_house",
        }
        if building_value in residential_types:
            return BuildingCategory.RESIDENTIAL

        # Commercial
        commercial_types = {
            "commercial",
            "retail",
            "supermarket",
            "shop",
            "store",
            "mall",
            "kiosk",
            "office",
            "hotel",
            "motel",
        }
        if building_value in commercial_types:
            return BuildingCategory.COMMERCIAL

        # Industrial
        industrial_types = {
            "industrial",
            "warehouse",
            "factory",
            "manufacture",
            "depot",
            "hangar",
            "storage_tank",
            "silo",
        }
        if building_value in industrial_types:
            return BuildingCategory.INDUSTRIAL

        # Institutional
        institutional_types = {
            "school",
            "university",
            "college",
            "hospital",
            "clinic",
            "kindergarten",
            "civic",
            "government",
            "public",
            "chapel",
            "church",
            "mosque",
            "temple",
            "synagogue",
            "cathedral",
            "shrine",
            "religious",
        }
        if building_value in institutional_types:
            return BuildingCategory.INSTITUTIONAL

        # Mixed use
        if "mixed_use" in building_value or tags.get("shop") or tags.get("amenity"):
            return BuildingCategory.MIXED_USE

        # Default to other
        return BuildingCategory.OTHER

    @staticmethod
    def extract_height_from_tags(tags: dict[str, str]) -> float | None:
        """
        Extract building height from OSM tags.

        Args:
            tags: OSM tags dictionary

        Returns:
            Height in meters, or None if not available
        """
        # Try height tag
        if "height" in tags:
            try:
                height_str = tags["height"].replace("m", "").replace("meters", "").strip()
                return float(height_str)
            except ValueError:
                pass

        # Try building:levels
        if "building:levels" in tags:
            try:
                levels = float(tags["building:levels"])
                # Estimate 3 meters per level
                return levels * 3.0
            except ValueError:
                pass

        # Try levels tag
        if "levels" in tags:
            try:
                levels = float(tags["levels"])
                return levels * 3.0
            except ValueError:
                pass

        return None

    @staticmethod
    def extract_floors_from_tags(tags: dict[str, str]) -> int | None:
        """
        Extract number of floors from OSM tags.

        Args:
            tags: OSM tags dictionary

        Returns:
            Number of floors, or None if not available
        """
        # Try building:levels
        if "building:levels" in tags:
            try:
                return int(float(tags["building:levels"]))
            except ValueError:
                pass

        # Try levels tag
        if "levels" in tags:
            try:
                return int(float(tags["levels"]))
            except ValueError:
                pass

        return None
