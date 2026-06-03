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
