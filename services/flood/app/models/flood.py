# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

RiskCategory = Literal["Very Low", "Low", "Moderate", "High", "Very High"]


class FloodRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    radius_meters: float = Field(1000.0, gt=0, description="Analysis radius in meters")


class FloodComponentScores(BaseModel):
    elevation_risk: float
    hydrology_risk: float
    historical_risk: float
    llai_risk: float


class ElevationAnalysis(BaseModel):
    mean_m: float
    min_m: float
    max_m: float
    range_m: float
    slope_degrees: float
    low_lying_area_pct: float
    terrain_classification: str


class HydrologyAnalysis(BaseModel):
    flow_accumulation: float
    nearest_river_distance_m: float
    water_occurrence_pct: float
    drainage_density: float
    river_proximity_risk: str


class FloodHistory(BaseModel):
    historical_events_count: int
    annual_rainfall_mm: float
    flood_history_score: float


class LowLyingAreaIndex(BaseModel):
    mean: float
    min: float
    max: float
    primary_risk_category: str


class FloodMetadata(BaseModel):
    latitude: float
    longitude: float
    radius_meters: float
    data_source: str
    gee_enabled: bool


class FloodReport(BaseModel):
    overall_score: float
    risk_category: RiskCategory
    component_scores: FloodComponentScores
    elevation: ElevationAnalysis
    hydrology: HydrologyAnalysis
    flood_history: FloodHistory
    llai: LowLyingAreaIndex
    recommendations: list[str]
    visualization_urls: dict[str, str]
    metadata: FloodMetadata
