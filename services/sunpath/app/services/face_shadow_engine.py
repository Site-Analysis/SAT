# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

"""
Face-based shadow calculation engine for building shadow analysis.
Each exterior edge (face) of a building casts a separate shadow polygon.
"""

import math
from typing import Any

import pyproj
from app.core.logging import get_logger
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import transform
from shapely.strtree import STRtree

logger = get_logger(__name__)


def compute_face_shadows(
    buildings_fc: dict,
    sun_azimuth_deg: float,
    sun_elevation_deg: float,
    height_attr: str = "height",
    min_elev_deg: float = 0.5,
    max_shadow_length_m: float = 500.0,
) -> dict:
    """
    Compute shadows cast by each face (edge) of each building.

    Args:
        buildings_fc: GeoJSON FeatureCollection with building features
        sun_azimuth_deg: Solar azimuth in degrees (0=North, 90=East, 180=South, 270=West)
        sun_elevation_deg: Solar elevation in degrees above horizon
        height_attr: Property name for building height in meters
        min_elev_deg: Minimum elevation to compute shadows
        max_shadow_length_m: Maximum shadow length to compute

    Returns:
        GeoJSON FeatureCollection of shadow features (one per building face)
    """
    # Check if sun is below horizon
    if sun_elevation_deg <= 0:
        logger.info("Sun below horizon, no shadows")
        return {
            "type": "FeatureCollection",
            "features": [],
            "metadata": {"status": "sun_below_horizon", "sun_elevation": sun_elevation_deg},
        }

    # Clamp low sun elevations
    if sun_elevation_deg < min_elev_deg:
        logger.warning(
            f"Sun elevation {sun_elevation_deg:.2f}° below minimum {min_elev_deg}°, clamping"
        )
        sun_elevation_deg = min_elev_deg

    buildings = buildings_fc.get("features", [])
    if not buildings:
        logger.warning("No buildings in input FeatureCollection")
        return {"type": "FeatureCollection", "features": []}

    # Calculate shadow length factor
    elevation_rad = math.radians(sun_elevation_deg)
    shadow_length_factor = 1.0 / math.tan(elevation_rad)

    # Compute sun vector (opposite direction for shadow projection)
    azimuth_rad = math.radians(sun_azimuth_deg)
    sun_vector_x = -math.sin(azimuth_rad)  # East component (negative = project away from sun)
    sun_vector_y = -math.cos(azimuth_rad)  # North component

    logger.info(
        f"Computing face shadows: elevation={sun_elevation_deg:.1f}°, azimuth={sun_azimuth_deg:.1f}°"
    )

    # Process each building and collect all shadow features
    all_shadow_features = []
    buildings_processed = 0
    buildings_skipped = 0
    total_faces = 0

    # Build spatial index for overlap detection (in WGS84 for simplicity)
    building_geoms = []
    building_ids = []
    for bldg in buildings:
        geom = bldg.get("geometry")
        if geom and geom.get("type") == "Polygon":
            coords = geom["coordinates"][0]
            poly = Polygon([(c[0], c[1]) for c in coords])
            if poly.is_valid:
                building_geoms.append(poly)
                building_ids.append(
                    bldg.get("id")
                    or bldg.get("properties", {}).get("osm_id", f"b_{len(building_ids)}")
                )

    spatial_index = STRtree(building_geoms) if building_geoms else None

    for building in buildings:
        try:
            # Validate building
            building_id = building.get("id") or building.get("properties", {}).get(
                "osm_id", f"building_{buildings_processed}"
            )
            geometry = building.get("geometry")
            properties = building.get("properties", {})

            if not geometry or geometry.get("type") != "Polygon":
                logger.debug(f"Skipping building {building_id}: invalid or missing geometry")
                buildings_skipped += 1
                continue

            # Get building height
            height = (
                properties.get(height_attr)
                or properties.get("height_m")
                or properties.get("height")
            )
            if height is None or height <= 0:
                # Try to estimate from levels
                levels = properties.get("levels") or properties.get("building_levels")
                if levels:
                    height = float(levels) * 3.0
                    height_source = "levels_estimate"
                else:
                    logger.debug(f"Skipping building {building_id}: no valid height")
                    buildings_skipped += 1
                    continue
            else:
                height = float(height)
                height_source = "property"

            # Skip very short buildings
            if height < 2.5:
                buildings_skipped += 1
                continue

            # Process building faces
            face_shadows = _process_building_faces(
                building_id=building_id,
                geometry=geometry,
                height=height,
                height_source=height_source,
                sun_vector_x=sun_vector_x,
                sun_vector_y=sun_vector_y,
                shadow_length_factor=shadow_length_factor,
                max_shadow_length_m=max_shadow_length_m,
                spatial_index=spatial_index,
                all_buildings_geoms=building_geoms,
                all_buildings_ids=building_ids,
            )

            all_shadow_features.extend(face_shadows)
            total_faces += len(face_shadows)
            buildings_processed += 1

        except Exception as e:
            logger.warning(f"Failed to process building {building_id}: {str(e)}", exc_info=True)
            buildings_skipped += 1
            continue

    logger.info(
        f"Generated {total_faces} face shadows from {buildings_processed} buildings ({buildings_skipped} skipped)"
    )

    return {
        "type": "FeatureCollection",
        "features": all_shadow_features,
        "metadata": {
            "buildings_processed": buildings_processed,
            "buildings_skipped": buildings_skipped,
            "total_face_shadows": total_faces,
            "sun_elevation": sun_elevation_deg,
            "sun_azimuth": sun_azimuth_deg,
        },
    }


def _process_building_faces(
    building_id: str,
    geometry: dict,
    height: float,
    height_source: str,
    sun_vector_x: float,
    sun_vector_y: float,
    shadow_length_factor: float,
    max_shadow_length_m: float,
    spatial_index: STRtree | None,
    all_buildings_geoms: list[Polygon],
    all_buildings_ids: list[str],
) -> list[dict[str, Any]]:
    """
    Process all faces of a single building and generate shadow features.

    Returns:
        List of shadow features (one per face)
    """
    coords = geometry["coordinates"][0]

    # Compute centroid for UTM zone selection
    centroid_lon = sum(c[0] for c in coords) / len(coords)
    centroid_lat = sum(c[1] for c in coords) / len(coords)

    # Determine UTM zone
    utm_zone = int((centroid_lon + 180) / 6) + 1
    hemisphere = "north" if centroid_lat >= 0 else "south"

    # Create coordinate transformers
    wgs84 = pyproj.CRS("EPSG:4326")
    utm = pyproj.CRS(f"+proj=utm +zone={utm_zone} +{hemisphere} +datum=WGS84 +units=m +no_defs")

    proj_to_utm = pyproj.Transformer.from_crs(wgs84, utm, always_xy=True).transform
    proj_to_wgs84 = pyproj.Transformer.from_crs(utm, wgs84, always_xy=True).transform

    # Transform building to UTM
    building_wgs84 = Polygon([(c[0], c[1]) for c in coords])
    building_utm = transform(proj_to_utm, building_wgs84)

    # Ensure valid geometry
    if not building_utm.is_valid:
        building_utm = building_utm.buffer(0)

    # Calculate shadow length
    shadow_length_m = min(height * shadow_length_factor, max_shadow_length_m)

    # Extract exterior ring vertices
    exterior_coords = list(building_utm.exterior.coords[:-1])  # Exclude closing vertex
    num_vertices = len(exterior_coords)

    face_shadows = []

    # Process each edge (face) of the building
    for face_idx in range(num_vertices):
        p1 = exterior_coords[face_idx]
        p2 = exterior_coords[(face_idx + 1) % num_vertices]

        # Skip very short edges
        edge_length = math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)
        if edge_length < 0.5:  # Skip edges shorter than 0.5m
            continue

        # Compute shadow polygon for this face
        # Shadow quad: [p1, p2, p2', p1'] where p' = p + shadow_offset
        offset_x = sun_vector_x * shadow_length_m
        offset_y = sun_vector_y * shadow_length_m

        p1_shadow = (p1[0] + offset_x, p1[1] + offset_y)
        p2_shadow = (p2[0] + offset_x, p2[1] + offset_y)

        # Create shadow polygon (quad from edge to its shadow)
        face_shadow_utm = Polygon([p1, p2, p2_shadow, p1_shadow, p1])

        # Ensure valid geometry
        if not face_shadow_utm.is_valid:
            face_shadow_utm = face_shadow_utm.buffer(0)

        if not face_shadow_utm.is_valid or face_shadow_utm.is_empty:
            continue

        # CRITICAL: Subtract ONLY the source building from this face shadow
        try:
            face_shadow_clean_utm = face_shadow_utm.difference(building_utm)

            # Check if completely overlapped by source building
            if face_shadow_clean_utm.is_empty:
                # Still record but with empty geometry
                face_shadow_wgs84 = transform(proj_to_wgs84, Polygon())
                shadow_area_m2 = 0.0
                was_fully_overlapped = True
            else:
                # Ensure cleaned shadow is valid
                if not face_shadow_clean_utm.is_valid:
                    face_shadow_clean_utm = face_shadow_clean_utm.buffer(0)

                # Transform back to WGS84
                face_shadow_wgs84 = transform(proj_to_wgs84, face_shadow_clean_utm)
                shadow_area_m2 = (
                    face_shadow_clean_utm.area
                    if isinstance(face_shadow_clean_utm, Polygon)
                    else sum(g.area for g in face_shadow_clean_utm.geoms)
                )
                was_fully_overlapped = False

        except Exception as e:
            logger.debug(
                f"Failed to clean shadow for building {building_id} face {face_idx}: {str(e)}"
            )
            continue

        # Detect overlaps with OTHER buildings
        overlaps = []
        if not was_fully_overlapped and spatial_index and shadow_area_m2 > 0:
            try:
                # Query spatial index for potential overlaps
                potential_overlaps = spatial_index.query(
                    building_wgs84.buffer(shadow_length_m / 111000)
                )  # Approx degrees

                for other_idx in potential_overlaps:
                    other_id = all_buildings_ids[other_idx]
                    if other_id == building_id:
                        continue  # Skip self

                    other_geom = all_buildings_geoms[other_idx]

                    # Check if face shadow intersects this other building
                    if face_shadow_wgs84.intersects(other_geom):
                        overlap_geom = face_shadow_wgs84.intersection(other_geom)
                        if not overlap_geom.is_empty:
                            # Convert to UTM to get accurate area
                            overlap_utm = transform(proj_to_utm, overlap_geom)
                            overlap_area_m2 = (
                                overlap_utm.area
                                if isinstance(overlap_utm, Polygon)
                                else sum(g.area for g in overlap_utm.geoms)
                            )

                            if overlap_area_m2 > 0.1:  # Ignore tiny overlaps
                                other_utm = transform(proj_to_utm, other_geom)
                                overlap_pct_target = (
                                    (overlap_area_m2 / other_utm.area) * 100
                                    if other_utm.area > 0
                                    else 0
                                )

                                overlaps.append(
                                    {
                                        "target_building_id": other_id,
                                        "overlap_area_m2": round(overlap_area_m2, 2),
                                        "overlap_pct_target": round(overlap_pct_target, 2),
                                    }
                                )
            except Exception as e:
                logger.debug(
                    f"Failed to compute overlaps for building {building_id} face {face_idx}: {str(e)}"
                )

        # Create shadow feature
        # Handle MultiPolygon case
        if isinstance(face_shadow_wgs84, MultiPolygon):
            # For MultiPolygon, create separate features or use the largest piece
            geom_coords = [[list(coord) for coord in face_shadow_wgs84.geoms[0].exterior.coords]]
        elif isinstance(face_shadow_wgs84, Polygon) and not face_shadow_wgs84.is_empty:
            geom_coords = [[list(coord) for coord in face_shadow_wgs84.exterior.coords]]
        else:
            geom_coords = [[]]

        shadow_feature = {
            "type": "Feature",
            "geometry": {"type": "Polygon", "coordinates": geom_coords},
            "properties": {
                "building_id": building_id,
                "face_index": face_idx,
                "shadow_length_m": round(shadow_length_m, 2),
                "shadow_area_m2": round(shadow_area_m2, 2),
                "height_m": round(height, 2),
                "height_source": height_source,
                "warnings": [],
                "overlaps": overlaps,
                "was_fully_overlapped_by_self": was_fully_overlapped,
            },
        }

        face_shadows.append(shadow_feature)

    return face_shadows
