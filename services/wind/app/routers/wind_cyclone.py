# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException

from app.models.wind_cyclone import (
    SiteResilienceReport,
    WindCycloneAnalysis,
    WindCycloneRequest,
)
from app.services.wind_cyclone_service import WindCycloneService

_WIND_CYCLONE_FLAG = "feature.wind.cyclone-hazard"


def _require_flag() -> None:
    enabled = {f.strip() for f in os.getenv("FLAGS", "").split(",") if f.strip()}
    if _WIND_CYCLONE_FLAG not in enabled:
        raise HTTPException(
            status_code=403,
            detail=f"Feature flag disabled: {_WIND_CYCLONE_FLAG}",
        )


service = WindCycloneService()
router = APIRouter(prefix="/api/v1/wind-cyclone", tags=["wind-cyclone"])
wind_cyclone_router = router


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "wind-cyclone"}


@router.post("/analyze", response_model=WindCycloneAnalysis)
def analyze_wind_cyclone(request: WindCycloneRequest) -> WindCycloneAnalysis:
    _require_flag()
    result = service.analyze(request)
    if not result.is_within_india:
        raise HTTPException(
            status_code=400,
            detail="Cyclone frequency and IS 875 wind hazard data is currently available only for locations within India.",
        )
    return result


@router.post("/recommendations", response_model=SiteResilienceReport)
def get_recommendations(request: WindCycloneRequest) -> SiteResilienceReport:
    _require_flag()
    return service.generate_recommendations(request)


@router.get("/wind-zones-geojson")
def get_wind_zones_geojson() -> dict:
    _require_flag()
    from app.services.wind_cyclone_service import get_is_875_wind_zones_geojson
    return get_is_875_wind_zones_geojson()
