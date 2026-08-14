# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

import math

import numpy as np
from affine import Affine
from pyproj import Transformer
from shapely.geometry import LineString, shape
from shapely.ops import transform as shapely_transform

from app.services.slope_engine import SLOPE_CLASSES


def _line_geometry(transect_geojson: dict):
    if transect_geojson.get("type") == "Feature":
        transect_geojson = transect_geojson.get("geometry", {})
    if transect_geojson.get("type") != "LineString":
        raise ValueError("Transect must be a GeoJSON LineString")
    return shape(transect_geojson)


def _slope_class(value: float) -> str:
    for name, low, high, _color, _label in SLOPE_CLASSES:
        if low <= value < high:
            return name
    return "HAZARD"


async def compute_transect(
    transect_geojson: dict,
    dem_array: np.ndarray,
    dem_transform: Affine,
    slope_array: np.ndarray,
    slope_class_array: np.ndarray,
    crs: str,
    dem_source: str,
    sample_interval_m: float = 5.0,
) -> dict:
    line_wgs84 = _line_geometry(transect_geojson)
    transformer = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    line: LineString = shapely_transform(transformer.transform, line_wgs84)
    total = float(line.length)
    distances = np.arange(0, total + sample_interval_m, sample_interval_m)
    if distances[-1] > total:
        distances[-1] = total

    inverse = ~dem_transform
    points = []
    for distance in distances:
        point = line.interpolate(float(distance))
        col, row = inverse * (point.x, point.y)
        r = int(round(row))
        c = int(round(col))
        if r < 0 or c < 0 or r >= dem_array.shape[0] or c >= dem_array.shape[1]:
            continue
        elev = float(dem_array[r, c])
        slope_pct = float(slope_array[r, c])
        if not math.isfinite(elev) or not math.isfinite(slope_pct):
            continue
        class_idx = int(slope_class_array[r, c])
        slope_class = SLOPE_CLASSES[class_idx - 1][0] if class_idx > 0 else _slope_class(slope_pct)
        points.append(
            {
                "distance_m": round(float(distance), 2),
                "elevation_m": round(elev, 2),
                "slope_pct": round(slope_pct, 2),
                "slope_class": slope_class,
            }
        )

    elevations = [p["elevation_m"] for p in points] or [0.0]
    return {
        "total_length_m": round(total, 2),
        "min_elevation_m": round(min(elevations), 2),
        "max_elevation_m": round(max(elevations), 2),
        "relief_m": round(max(elevations) - min(elevations), 2),
        "dem_source": dem_source,
        "points": points,
    }
