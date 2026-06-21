# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

"""Shared dependencies for dependency injection."""

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from fastapi import Depends, Request

logger = get_logger(__name__)


def get_app_settings() -> Settings:
    """Dependency to get application settings."""
    return get_settings()


def get_request_id(request: Request) -> str:
    """Extract or generate request ID for tracking."""
    return request.headers.get("X-Request-ID", "unknown")


def log_request(request: Request, request_id: str = Depends(get_request_id)) -> None:
    """Log incoming request details."""
    logger.info(
        f"Incoming request: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_host": request.client.host if request.client else "unknown",
        },
    )
