# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

import numpy as np
import rasterio.features
from rasterio.warp import transform_geom

SLOPE_CLASSES = [
    ("FLAT", 0, 5, "#2d6a4f", "0-5%"),
    ("GENTLE", 5, 10, "#52b788", "5-10%"),
    ("MODERATE", 10, 15, "#ffd166", "10-15%"),
    ("STEEP", 15, 25, "#f4a261", "15-25%"),
    ("VERY_STEEP", 25, 33, "#e76f51", "25-33%"),
    ("HAZARD", 33, float("inf"), "#c1121f", ">33%"),
]

BUILDABILITY = {
    "BUILDABLE_FLAT": "#2d6a4f",
    "BUILDABLE_WITH_GRADING": "#52b788",
    "CONSTRAINED_RETAINING": "#ffd166",
    "NON_BUILDABLE_REGULATED": "#e76f51",
    "NON_BUILDABLE_HAZARD": "#c1121f",
}


def classify_buildability(slope_pct: float) -> str:
    if slope_pct > 33:
        return "NON_BUILDABLE_HAZARD"
    if slope_pct > 25:
        return "NON_BUILDABLE_REGULATED"
    if slope_pct > 15:
        return "CONSTRAINED_RETAINING"
    if slope_pct > 5:
        return "BUILDABLE_WITH_GRADING"
    return "BUILDABLE_FLAT"


def compute_slope_aspect(dem: np.ndarray, cellsize: float) -> tuple[np.ndarray, np.ndarray]:
    padded = np.pad(dem, 1, mode="edge")
    a = padded[:-2, :-2]
    b = padded[:-2, 1:-1]
    c = padded[:-2, 2:]
    d = padded[1:-1, :-2]
    f = padded[1:-1, 2:]
    g = padded[2:, :-2]
    h = padded[2:, 1:-1]
    i = padded[2:, 2:]

    dz_dx = ((c + 2 * f + i) - (a + 2 * d + g)) / (8 * cellsize)
    dz_dy = ((g + 2 * h + i) - (a + 2 * b + c)) / (8 * cellsize)
    slope_rad = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    slope_pct = np.tan(slope_rad) * 100
    aspect_math = np.arctan2(dz_dy, -dz_dx)
    aspect_compass = (90 - np.degrees(aspect_math)) % 360
    return slope_pct.astype("float32"), aspect_compass.astype("float32")


def slope_class_array(slope_pct: np.ndarray) -> np.ndarray:
    classes = np.zeros(slope_pct.shape, dtype="uint8")
    for idx, (_name, low, high, _color, _label) in enumerate(SLOPE_CLASSES, start=1):
        classes[(slope_pct >= low) & (slope_pct < high)] = idx
    return classes


def slope_stats(slope_pct: np.ndarray) -> dict:
    valid = slope_pct[np.isfinite(slope_pct)]
    total = max(int(valid.size), 1)

    def pct(low: float, high: float) -> float:
        return round(float(((valid >= low) & (valid < high)).sum() / total * 100), 2)

    return {
        "mean_slope_pct": round(float(np.nanmean(valid)), 2),
        "max_slope_pct": round(float(np.nanmax(valid)), 2),
        "flat_area_pct": pct(0, 5),
        "gentle_area_pct": pct(5, 10),
        "moderate_area_pct": pct(10, 15),
        "steep_area_pct": pct(15, 25),
        "very_steep_area_pct": pct(25, 33),
        "hazard_area_pct": pct(33, float("inf")),
    }


def aspect_stats(aspect: np.ndarray) -> dict:
    valid = aspect[np.isfinite(aspect)]
    if valid.size == 0:
        return {
            "dominant_aspect_deg": 0.0,
            "dominant_aspect_label": "N",
            "north_facing_pct": 0.0,
            "south_facing_pct": 0.0,
        }
    bins = np.arange(0, 361, 45)
    hist, edges = np.histogram(valid, bins=bins)
    idx = int(np.argmax(hist))
    deg = float((edges[idx] + edges[idx + 1]) / 2) % 360
    labels = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    label = labels[int(((deg + 22.5) % 360) // 45)]
    north = ((valid >= 315) | (valid <= 45)).sum() / valid.size * 100
    south = ((valid >= 135) & (valid <= 225)).sum() / valid.size * 100
    return {
        "dominant_aspect_deg": round(deg, 2),
        "dominant_aspect_label": label,
        "north_facing_pct": round(float(north), 2),
        "south_facing_pct": round(float(south), 2),
    }


def _features_from_classes(class_array: np.ndarray, transform, crs: str, mode: str) -> dict:
    features = []
    for geom, value in rasterio.features.shapes(class_array, transform=transform):
        class_idx = int(value)
        if class_idx <= 0:
            continue
        name, _low, _high, color, label = SLOPE_CLASSES[class_idx - 1]
        props = (
            {"slope_class": name, "color": color, "slope_range_label": label}
            if mode == "slope"
            else {
                "buildability_class": classify_buildability({"FLAT": 2, "GENTLE": 6, "MODERATE": 12, "STEEP": 20, "VERY_STEEP": 28, "HAZARD": 40}[name]),
                "color": BUILDABILITY[classify_buildability({"FLAT": 2, "GENTLE": 6, "MODERATE": 12, "STEEP": 20, "VERY_STEEP": 28, "HAZARD": 40}[name])],
            }
        )
        features.append(
            {
                "type": "Feature",
                "properties": props,
                "geometry": transform_geom(crs, "EPSG:4326", geom),
            }
        )
    return {"type": "FeatureCollection", "features": features}


def slope_geojson(class_array: np.ndarray, transform, crs: str) -> dict:
    return _features_from_classes(class_array, transform, crs, "slope")


def buildability_geojson(class_array: np.ndarray, transform, crs: str) -> dict:
    return _features_from_classes(class_array, transform, crs, "buildability")
