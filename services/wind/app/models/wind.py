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


class SeasonData(BaseModel):
    average_wind_speed: float
    prevailing_direction: str
    direction_distribution: dict[str, float]
    # Add these 4 new fields:
    max_wind_speed: float | None = None
    gust_risk: str | None = None
    recommended_orientation: str | None = None


class SeasonalAnalysis(BaseModel):
    summer: SeasonData
    monsoon: SeasonData
    winter: SeasonData


class ComfortAnalysis(BaseModel):
    pedestrian_comfort: ComfortLevel
    natural_ventilation_potential: ComfortLevel
    outdoor_usability: ComfortLevel


class BuildingImpact(BaseModel):
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
    direction_distribution: dict[str, float] = Field(
        ..., description="Overall percentage frequency for each 8-point compass direction"
    )
    wind_category: str
    gust_risk: str
    seasonal_analysis: SeasonalAnalysis
    comfort_analysis: ComfortAnalysis
    building_impact: BuildingImpact
    recommendations: list[str]
    metadata: WindMetadata
