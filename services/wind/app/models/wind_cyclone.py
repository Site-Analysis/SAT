# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class WindCycloneRequest(BaseModel):
    latitude: float = Field(..., description="Latitude in decimal degrees")
    longitude: float = Field(..., description="Longitude in decimal degrees")
    buffer_radius_km: float = Field(100.0, description="Buffer search radius in km (50, 100, 250)")


class TerrainWindProfile(BaseModel):
    profile_10m: float = Field(..., alias="10m")
    profile_50m: float = Field(..., alias="50m")
    profile_100m: float = Field(..., alias="100m")
    profile_150m: float = Field(..., alias="150m")
    profile_200m: float = Field(..., alias="200m")

    class Config:
        populate_by_name = True


class SummaryMetrics(BaseModel):
    total_historical_events: int
    annual_rate_50yr: float
    max_recorded_wind_speed_ms: float
    max_recorded_wind_speed_kmh: float
    closest_recorded_distance_km: float


class WindCycloneAnalysis(BaseModel):
    is_within_india: bool
    statutory_v_b_ms: float
    damage_risk_category: str
    is_coastal_buffer: bool
    coastal_penalty_applied: bool
    terrain_wind_profile: dict[str, float]
    metrics: SummaryMetrics
    decadal_trend: dict[str, int]
    intensity_distribution: dict[str, int]
    tracks: dict[str, Any]
    wind_zones: dict[str, Any] = Field(default_factory=lambda: {"type": "FeatureCollection", "features": []})
    eye_points: dict[str, Any] = Field(default_factory=lambda: {"type": "FeatureCollection", "features": []})


class PrioritizedMitigation(BaseModel):
    priority: Literal["CRITICAL", "HIGH", "ADVISORY"]
    category: str
    standard_reference: str
    recommendation_text: str


class SiteResilienceReport(BaseModel):
    recommended_design_wind_speed_ms: float
    statutory_wind_speed_ms: float
    is_design_speed_elevated: bool
    elevation_reason: str
    prioritized_mitigations: list[PrioritizedMitigation]
    early_warning_checklist: list[str]
