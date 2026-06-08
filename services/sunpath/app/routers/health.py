"""Health check API endpoints."""

import time
from datetime import datetime

from fastapi import APIRouter, status

from app.core.config import settings
from app.models.common import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])

# Store application start time
_start_time = time.time()


@router.get(
    "",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check the health status of the API service.",
)
async def health_check() -> HealthResponse:
    """
    Perform a health check.

    Returns:
        HealthResponse with service status and metadata
    """
    uptime = time.time() - _start_time

    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.APP_VERSION,
        uptime_seconds=round(uptime, 2),
    )


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness Check",
    description="Check if the service is ready to accept requests.",
)
async def readiness_check() -> dict:
    """
    Check if the service is ready.

    Returns:
        Dictionary with readiness status
    """
    return {
        "ready": True,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness Check",
    description="Check if the service is alive.",
)
async def liveness_check() -> dict:
    """
    Check if the service is alive.

    Returns:
        Dictionary with liveness status
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat(),
    }
