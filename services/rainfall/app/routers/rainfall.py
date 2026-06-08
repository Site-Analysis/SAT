from __future__ import annotations

import os
from datetime import date

from app.models.rainfall import (
    AnomalyResponse,
    ClimateProfileResponse,
    RainfallArchiveResponse,
    RainfallSummaryRequest,
    RainfallSummaryResponse,
    SeasonalityResponse,
    SiteAnalysisRequest,
    SiteAnalysisResponse,
)
from app.services.rainfall_service import RainfallService
from fastapi import APIRouter, HTTPException, Query

_ARCHIVE_FLAG = "feature.rainfall.archive"
_SUMMARY_FLAG = "feature.rainfall.summary"


def _require_flag(flag: str) -> None:
    enabled = {f.strip() for f in os.getenv("FLAGS", "").split(",") if f.strip()}
    if flag not in enabled:
        raise HTTPException(status_code=403, detail=f"Feature flag disabled: {flag}")


def _parse_date(value: str, label: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"{label} must be YYYY-MM-DD") from exc


service = RainfallService()
router = APIRouter(prefix="/rainfall", tags=["rainfall"])
rainfall_router = router


@router.get("/archive", response_model=RainfallArchiveResponse)
def get_rainfall_archive(
    latitude: float = Query(..., description="Latitude in decimal degrees"),
    longitude: float = Query(..., description="Longitude in decimal degrees"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    source: str | None = Query(None, description="Dataset source (open-meteo or gee)"),
) -> RainfallArchiveResponse:
    _require_flag(_ARCHIVE_FLAG)
    parsed_start = _parse_date(start_date, "start_date")
    parsed_end = _parse_date(end_date, "end_date")
    if parsed_start > parsed_end:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date")

    return service.get_archive(
        latitude=latitude,
        longitude=longitude,
        start_date=parsed_start,
        end_date=parsed_end,
        source=source,
    )


@router.post("/summary", response_model=RainfallSummaryResponse)
def get_rainfall_summary(request: RainfallSummaryRequest) -> RainfallSummaryResponse:
    _require_flag(_SUMMARY_FLAG)
    try:
        parsed_start = _parse_date(request.start_date, "start_date")
        parsed_end = _parse_date(request.end_date, "end_date")
    except HTTPException:
        raise

    if parsed_start > parsed_end:
        raise HTTPException(status_code=422, detail="start_date must be on or before end_date")

    try:
        return service.get_summary(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


_CLIMATE_PROFILE_FLAG = "feature.rainfall.climate-profile"
_ANOMALY_FLAG = "feature.rainfall.anomaly"
_SEASONALITY_FLAG = "feature.rainfall.seasonality"
_SITE_ANALYSIS_FLAG = "feature.rainfall.site-analysis"


@router.get("/climate-profile", response_model=ClimateProfileResponse)
def get_climate_profile(
    latitude: float = Query(..., description="Latitude in decimal degrees"),
    longitude: float = Query(..., description="Longitude in decimal degrees"),
) -> ClimateProfileResponse:
    _require_flag(_CLIMATE_PROFILE_FLAG)
    try:
        return service.get_climate_profile(latitude, longitude)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/anomaly", response_model=AnomalyResponse)
def get_anomaly(
    latitude: float = Query(..., description="Latitude in decimal degrees"),
    longitude: float = Query(..., description="Longitude in decimal degrees"),
    days: int = Query(30, description="Number of days to analyze"),
) -> AnomalyResponse:
    _require_flag(_ANOMALY_FLAG)
    if days < 1 or days > 365:
        raise HTTPException(status_code=422, detail="days must be between 1 and 365")
    try:
        return service.get_anomaly(latitude, longitude, days)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/seasonality", response_model=SeasonalityResponse)
def get_seasonality(
    latitude: float = Query(..., description="Latitude in decimal degrees"),
    longitude: float = Query(..., description="Longitude in decimal degrees"),
) -> SeasonalityResponse:
    _require_flag(_SEASONALITY_FLAG)
    try:
        return service.get_seasonality(latitude, longitude)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/site-analysis", response_model=SiteAnalysisResponse)
def get_site_analysis(request: SiteAnalysisRequest) -> SiteAnalysisResponse:
    _require_flag(_SITE_ANALYSIS_FLAG)
    if request.radius_meters < 500 or request.radius_meters > 50000:
        raise HTTPException(status_code=422, detail="radius_meters must be between 500 and 50000")
    try:
        return service.get_site_analysis(request.latitude, request.longitude, request.radius_meters)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
