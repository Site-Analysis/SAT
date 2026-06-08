from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class RainfallArchiveDailyUnits(BaseModel):
    time: Literal["iso8601"] = "iso8601"
    precipitation_sum: Literal["mm"] = "mm"


class RainfallArchiveDaily(BaseModel):
    time: list[str]
    precipitation_sum: list[float]


class RainfallArchiveResponse(BaseModel):
    latitude: float
    longitude: float
    timezone: str | None = None
    daily_units: RainfallArchiveDailyUnits
    daily: RainfallArchiveDaily
    source: str


class RainfallSummaryRequest(BaseModel):
    geometry: dict[str, Any] | None = None
    latitude: float | None = None
    longitude: float | None = None
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")


class RainfallDateRange(BaseModel):
    start_date: str
    end_date: str


class RainfallSummaryResponse(BaseModel):
    total_rainfall_mm: float
    mean_daily_rainfall_mm: float
    max_daily_rainfall_mm: float
    rainy_days: int
    dry_days: int
    date_range: RainfallDateRange
    source: str


class ClimateProfileResponse(BaseModel):
    latitude: float
    longitude: float
    annual_rainfall_mm: float = Field(..., description="Mean annual rainfall")
    wettest_month: str = Field(..., description="Month with highest average rainfall (1-12)")
    driest_month: str = Field(..., description="Month with lowest average rainfall (1-12)")
    rainfall_variability: float = Field(..., description="Coefficient of variation (0-1)")
    monsoon_strength: float = Field(
        ..., description="Monsoon contribution % to annual rainfall (0-100)"
    )
    climate_classification: str = Field(..., description="Köppen-Geiger classification")
    rainfall_reliability_score: float = Field(
        ..., description="Reliability score (0-100, higher=more reliable)"
    )
    datasets: list[str] = Field(default_factory=list, description="Datasets used for analysis")


class AnomalyResponse(BaseModel):
    latitude: float
    longitude: float
    period_label: str = Field(..., description="Analysis period (e.g., 'Last 30 days')")
    current_period_rainfall_mm: float = Field(..., description="Rainfall in current period")
    long_term_average_mm: float = Field(..., description="Long-term average for same period")
    anomaly_percent: float = Field(..., description="% deviation from normal (-100 to 200+)")
    anomaly_category: Literal["Very Dry", "Dry", "Normal", "Wet", "Very Wet"]
    datasets: list[str] = Field(default_factory=list)


class SeasonalityResponse(BaseModel):
    latitude: float
    longitude: float
    summer_rainfall_mm: float = Field(..., description="Jun-Aug rainfall")
    monsoon_rainfall_mm: float = Field(..., description="Sep-Nov rainfall")
    winter_rainfall_mm: float = Field(..., description="Dec-Feb rainfall")
    spring_rainfall_mm: float = Field(..., description="Mar-May rainfall")
    seasonal_distribution: dict[str, float] = Field(..., description="% distribution by season")
    rainfall_concentration_index: float = Field(
        ..., description="Seasonality index (0=uniform, 1=extreme)"
    )
    datasets: list[str] = Field(default_factory=list)


class SiteAnalysisRequest(BaseModel):
    latitude: float
    longitude: float
    radius_meters: int = Field(default=5000, description="Analysis radius (500-50000 m)")


class SuitabilityScores(BaseModel):
    water_availability_score: float = Field(..., description="Score 0-100")
    agriculture_score: float = Field(..., description="Score 0-100")
    drainage_score: float = Field(..., description="Score 0-100, lower=better drainage")
    groundwater_recharge_score: float = Field(..., description="Score 0-100")
    infiltration_suitability_score: float = Field(..., description="Score 0-100")


class SiteAnalysisResponse(BaseModel):
    latitude: float
    longitude: float
    radius_meters: int
    annual_rainfall_mm: float
    summer_rainfall_mm: float
    monsoon_rainfall_mm: float
    winter_rainfall_mm: float
    spring_rainfall_mm: float
    rainfall_trend_5yr_percent: float = Field(..., description="5-year trend (% change per year)")
    rainfall_trend_10yr_percent: float = Field(..., description="10-year trend (% change per year)")
    trend_direction: Literal["increasing", "decreasing", "stable"]
    drought_risk_level: Literal["very_low", "low", "moderate", "high", "very_high"]
    dry_day_frequency: float = Field(..., description="% of days with <0.1mm rainfall")
    runoff_potential: float = Field(..., description="Score 0-100")
    flood_susceptibility_contribution: float = Field(..., description="Score 0-100")
    water_availability_score: float
    suitability_scores: SuitabilityScores
    recommendations: list[str]
    datasets: list[str] = Field(default_factory=list)
