# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ComfortLevel = Literal["Poor", "Fair", "Good", "Excellent"]
WindLoadRisk = Literal["Low", "Moderate", "High", "Very High"]
Orientation = Literal[
    "North", "Northeast", "East", "Southeast", "South", "Southwest", "West", "Northwest"
]


class WindRequest(BaseModel):
    latitude: float = Field(..., description="Latitude in decimal degrees")
    longitude: float = Field(..., description="Longitude in decimal degrees")
    radius_meters: float = Field(1000.0, gt=0, description="Analysis radius in meters")


class SeasonalAnalysis(BaseModel):
    summer: float
    monsoon: float
    winter: float


class ComfortAnalysis(BaseModel):
    pedestrian_comfort: ComfortLevel
    natural_ventilation_potential: ComfortLevel
    outdoor_usability: ComfortLevel


class BuildingImpact(BaseModel):
    cross_ventilation_score: float
    wind_load_risk: WindLoadRisk
    recommended_orientation: Orientation


class WindMetadata(BaseModel):
    latitude: float
    longitude: float
    radius_meters: float
    data_source: str


class WindAnalysis(BaseModel):
    average_wind_speed: float
    max_wind_speed: float
    prevailing_direction: Orientation
    wind_category: str
    gust_risk: str
    seasonal_analysis: SeasonalAnalysis
    comfort_analysis: ComfortAnalysis
    building_impact: BuildingImpact
    recommendations: list[str]
    metadata: WindMetadata
