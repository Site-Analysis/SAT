# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager

from app.routers.contour import contour_router
from app.services.dem_service import initialize_gee_client
from app.settings import ContourSettings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("contour")


def _parse_cors_origins(raw_value: str) -> list[str]:
    stripped = (raw_value or "").strip()
    if not stripped:
        return ["*"]
    if stripped.startswith("["):
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, list):
                origins = [str(origin).strip() for origin in parsed if str(origin).strip()]
                return origins or ["*"]
        except json.JSONDecodeError:
            pass
    origins = [origin.strip() for origin in stripped.split(",") if origin.strip()]
    return origins or ["*"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Contour API")
    logger.info("Copernicus DEM GLO-30 2024 source configured")
    initialize_gee_client()
    logger.info("Google Earth Engine initialized for contour service")
    yield
    logger.info("Shutting down Contour API")


settings = ContourSettings()
app = FastAPI(title="SAT Contour Analysis API", lifespan=lifespan)

cors_origins = _parse_cors_origins(settings.cors_origins)
allow_credentials = os.getenv("CORS_ALLOW_CREDENTIALS", "false").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
if "*" in cors_origins:
    allow_credentials = False
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(contour_router)


@app.get("/")
def root() -> dict:
    return {"message": "SAT Contour Analysis API is running"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "contour"}
