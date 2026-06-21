# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

"""Sunlight-hours grid — ground sunshine duration.

Method adapted from **pybdshadow** (BSD-3-Clause, © ni1o1): per-cell accumulation
of un-shadowed daylight time across a grid over a day. Re-implemented here driven
by **pvlib NREL SPA** solar angles (pybdshadow uses suncalc) for consistency with
the rest of the service. See `THIRD_PARTY_LICENSES.md`.

Resolution is hourly (one SolarEngine range call per request). Building shadows are
optional: when building footprints+heights are supplied, cells inside any building's
shadow at a given hour do not accrue that hour; with no buildings it reports open-sky
daylight hours.
"""

from __future__ import annotations

import datetime as dt
import math
from typing import Any

from app.core.logging import get_logger
from app.services.shadow_engine import ShadowEngine
from app.services.solar_engine import SolarEngine
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

logger = get_logger(__name__)

solar_engine = SolarEngine()
shadow_engine = ShadowEngine(gee_service=None)


def _grid(lat: float, lon: float, radius_m: float, n: int) -> list[tuple[float, float]]:
    """n×n lat/lon grid covering ±radius_m around the centre."""
    dlat = radius_m / 111_320.0
    dlon = radius_m / (111_320.0 * math.cos(math.radians(lat)) or 1e-9)
    cells: list[tuple[float, float]] = []
    for i in range(n):
        fy = (i / (n - 1)) * 2 - 1 if n > 1 else 0.0
        for j in range(n):
            fx = (j / (n - 1)) * 2 - 1 if n > 1 else 0.0
            cells.append((lat + fy * dlat, lon + fx * dlon))
    return cells


def compute_sunlight_hours(
    lat: float,
    lon: float,
    day: dt.date,
    radius_meters: float = 250.0,
    buildings: list[dict[str, Any]] | None = None,
    grid_n: int = 9,
) -> list[dict[str, float]]:
    """Return per-cell sunshine hours for `day`.

    `buildings`: optional list of ``{"footprint": [[lon, lat], ...], "height": m, "id": str}``.
    """
    start = dt.datetime.combine(day, dt.time(0, 0))
    end = dt.datetime.combine(day, dt.time(23, 0))
    rows = solar_engine.calculate_solar_position(lat, lon, start, end)  # hourly

    cells = _grid(lat, lon, radius_meters, grid_n)
    points = [Point(clon, clat) for clat, clon in cells]
    hours = [0.0] * len(cells)

    for r in rows:
        if r.elevation <= 0:  # sun below horizon → no sunshine this hour
            continue

        shadow_union = None
        if buildings:
            polys: list[Polygon] = []
            for b in buildings:
                footprint = b.get("footprint")
                height = b.get("height")
                if not footprint or not height:
                    continue
                shadows = shadow_engine.generate_shadow_polygon(
                    building_footprint=footprint,
                    building_height=float(height),
                    solar_elevation=r.elevation,
                    solar_azimuth=r.azimuth,
                    centroid_lon=lon,
                    building_id=str(b.get("id", "b")),
                )
                for s in shadows or []:
                    try:
                        polys.append(Polygon(s["coordinates"][0]))
                    except (KeyError, IndexError, ValueError):
                        continue
            if polys:
                shadow_union = unary_union(polys)

        for idx, pt in enumerate(points):
            if shadow_union is not None and shadow_union.contains(pt):
                continue
            hours[idx] += 1.0  # hourly resolution

    return [
        {"lat": round(clat, 6), "lon": round(clon, 6), "sunlight_hours": round(hours[idx], 2)}
        for idx, (clat, clon) in enumerate(cells)
    ]
