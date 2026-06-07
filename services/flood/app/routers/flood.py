from __future__ import annotations

import os

from app.models.flood import FloodReport, FloodRequest
from app.services.flood_service import FloodRiskService
from fastapi import APIRouter, HTTPException

_FLOOD_FLAG = "feature.flood.risk-analysis"


def _require_flag() -> None:
    enabled = {f.strip() for f in os.getenv("FLAGS", "").split(",") if f.strip()}
    if _FLOOD_FLAG not in enabled:
        raise HTTPException(status_code=403, detail=f"Feature flag disabled: {_FLOOD_FLAG}")


service = FloodRiskService()
router = APIRouter(prefix="/flood", tags=["flood"])
flood_router = router


@router.post("/analyze", response_model=FloodReport)
def analyze_flood(request: FloodRequest) -> FloodReport:
    _require_flag()
    return service.analyze(request)
