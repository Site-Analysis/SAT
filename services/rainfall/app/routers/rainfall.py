from __future__ import annotations

import os
from datetime import date

from app.models.rainfall import (
    RainfallArchiveResponse,
    RainfallSummaryRequest,
    RainfallSummaryResponse,
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
