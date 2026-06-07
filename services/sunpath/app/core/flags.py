"""Feature-flag gating.

Reads the FLAGS env var directly (comma-separated) — `packages/flags` is
outside the Docker build context, so services enforce flags in-process.
Mirrors the temperature service convention.
"""

from __future__ import annotations

import os

from fastapi import HTTPException

SUNPATH_FLAG = "feature.sunpath.diagram"


def is_enabled(flag: str) -> bool:
    enabled = {f.strip() for f in os.getenv("FLAGS", "").split(",") if f.strip()}
    return flag in enabled


def require_sunpath_flag() -> None:
    """FastAPI dependency — 403 when the sunpath flag is off."""
    if not is_enabled(SUNPATH_FLAG):
        raise HTTPException(status_code=403, detail=f"Feature flag disabled: {SUNPATH_FLAG}")
