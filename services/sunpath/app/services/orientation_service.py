# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

"""Building orientation & shading recommendation from annual solar geometry.

Derives the equator-facing optimal facade and a window-overhang projection factor
from summer/winter solar-noon altitudes (pvlib NREL SPA).
"""

from __future__ import annotations

import datetime as dt
import math

from app.services.solar_engine import SolarEngine

solar_engine = SolarEngine()


def _noon_altitude(lat: float, lon: float, day: dt.date) -> float:
    """Max solar elevation (apparent) over the given day."""
    start = dt.datetime.combine(day, dt.time(0, 0))
    end = dt.datetime.combine(day, dt.time(23, 0))
    rows = solar_engine.calculate_solar_position(lat, lon, start, end)
    return max((r.elevation for r in rows), default=0.0)


def orientation_recommendation(lat: float, lon: float) -> dict:
    year = dt.date.today().year
    summer_alt = _noon_altitude(lat, lon, dt.date(year, 6, 21))
    winter_alt = _noon_altitude(lat, lon, dt.date(year, 12, 21))

    northern = lat >= 0
    facade = "south" if northern else "north"
    facade_azimuth = 180.0 if northern else 0.0

    # Projection factor PF = overhang depth / window height that fully shades the
    # equator-facing window at summer solar noon: depth D shades D·tan(alt) of wall,
    # so to shade window height H → D = H / tan(alt) → PF = 1 / tan(alt).
    # Provisional design heuristic; validate against a passive-shading reference.
    pf = None
    if summer_alt > 0:
        pf = round(1.0 / math.tan(math.radians(summer_alt)), 3)

    return {
        "latitude": lat,
        "longitude": lon,
        "optimal_facade_orientation": facade,
        "optimal_facade_azimuth_deg": facade_azimuth,
        "summer_noon_altitude_deg": round(summer_alt, 1),
        "winter_noon_altitude_deg": round(winter_alt, 1),
        "overhang_projection_factor": pf,
        "notes": (
            f"Orient the main glazed facade to {facade} (azimuth {facade_azimuth:.0f}°). "
            f"A horizontal overhang of depth ≈ {pf}× the window height shades the "
            f"summer-noon sun (altitude {summer_alt:.1f}°) while admitting the lower "
            f"winter sun (altitude {winter_alt:.1f}°). Projection factor is a provisional "
            "heuristic — validate against project shading criteria."
        )
        if pf is not None
        else "Sun does not rise above the horizon at summer solstice; overhang N/A.",
    }
