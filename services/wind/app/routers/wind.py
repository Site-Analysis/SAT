from __future__ import annotations

import os

from app.models.wind import WindAnalysis, WindRequest
from app.services.wind_service import WindAnalysisService
from fastapi import APIRouter, HTTPException

_WIND_FLAG = "feature.wind.analysis"


def _require_flag() -> None:
    enabled = {f.strip() for f in os.getenv("FLAGS", "").split(",") if f.strip()}
    if _WIND_FLAG not in enabled:
        raise HTTPException(status_code=403, detail=f"Feature flag disabled: {_WIND_FLAG}")


service = WindAnalysisService()
router = APIRouter(prefix="/wind", tags=["wind"])
wind_router = router


@router.post("/analyze", response_model=WindAnalysis)
def analyze_wind(request: WindRequest) -> WindAnalysis:
    _require_flag()
    return service.analyze(request)
