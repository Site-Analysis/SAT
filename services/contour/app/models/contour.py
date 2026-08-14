# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ContourRequest(BaseModel):
    polygon: dict
    contour_interval: int = Field(
        default=20,
        ge=10,
        le=60,
        description="Contour interval in metres. Min 10m, max 60m.",
    )


class TransectRequest(BaseModel):
    polygon: dict
    transect_line: dict


class DEMMetadata(BaseModel):
    source: Literal["copernicus"] = "copernicus"
    resolution_m: int
    vertical_rmse_m: float
    contour_interval_m: int
    warning: str | None = None


class SlopeStats(BaseModel):
    mean_slope_pct: float
    max_slope_pct: float
    flat_area_pct: float
    gentle_area_pct: float
    moderate_area_pct: float
    steep_area_pct: float
    very_steep_area_pct: float
    hazard_area_pct: float


class AspectStats(BaseModel):
    dominant_aspect_deg: float
    dominant_aspect_label: str
    north_facing_pct: float
    south_facing_pct: float


class ContourResponse(BaseModel):
    dem_metadata: DEMMetadata
    slope_stats: SlopeStats
    aspect_stats: AspectStats
    contour_geojson: dict
    slope_geojson: dict
    buildability_geojson: dict
    hillshade_png_b64: str


class TransectPoint(BaseModel):
    distance_m: float
    elevation_m: float
    slope_pct: float
    slope_class: str


class TransectResponse(BaseModel):
    total_length_m: float
    min_elevation_m: float
    max_elevation_m: float
    relief_m: float
    dem_source: str
    points: list[TransectPoint]
