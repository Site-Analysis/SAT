# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class MonthlyTemperature(BaseModel):
    """Average monthly temperature record."""

    month: int = Field(..., ge=1, le=12, description="Month number 1-12")
    avg_tmax: float = Field(..., description="Average monthly daily maximum temperature")
    avg_tmin: float = Field(..., description="Average monthly daily minimum temperature")


class ClimateSummary(BaseModel):
    """Summary statistics for an annual thermal profile."""

    annual_avg_temp: float = Field(..., description="Annual average temperature (°C)")
    peak_max_temp: float = Field(..., description="Highest observed daily maximum (°C)")
    lowest_min_temp: float = Field(..., description="Lowest observed daily minimum (°C)")


class ClimateRecommendations(BaseModel):
    """Recommendations derived from the climate summary."""

    material_suggestion: str = Field(..., description="Suggested building material approach")
    insulation_strategy: str = Field(..., description="Insulation or thermal strategy suggestion")
    thermal_comfort_status: str = Field(..., description="Qualitative comfort classification")
    climate_zone: str | None = Field(None, description="ECBC/Köppen climate zone label")
    cdd_hdd_ratio: float | None = Field(None, description="Annual CDD / HDD ratio")


class ClimateReport(BaseModel):
    """Top-level report combining monthly data, summary and recommendations."""

    monthly_data: list[MonthlyTemperature]
    summary: ClimateSummary
    recommendations: ClimateRecommendations


class ThermalGridRequest(BaseModel):
    """Request model for spatial thermal grid generation over a polygon."""

    geometry: dict[str, Any] = Field(
        ..., description="GeoJSON Polygon geometry in [lng, lat] format"
    )
    year: int | None = Field(None, description="Target year (defaults to last completed year)")
    grid_size: int = Field(8, ge=3, le=20, description="Grid resolution per axis (NxN)")


class ThermalGridResponse(BaseModel):
    """GeoJSON feature collection representing annual average temperature per grid cell."""

    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: list[dict[str, Any]]
    min_temp: float
    max_temp: float
    year: int
