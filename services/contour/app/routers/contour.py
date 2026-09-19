# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

import os

import numpy as np
from fastapi import APIRouter, HTTPException
from rasterio.transform import array_bounds
from rasterio.warp import transform_bounds

from app.models.contour import ContourRequest, ContourResponse, TransectRequest, TransectResponse
from app.services import dem_service
from app.services.contour_engine import compute_hillshade, encode_png_b64, generate_contours
from app.services.slope_engine import (
    aspect_stats,
    buildability_geojson,
    compute_slope_aspect,
    slope_class_array,
    slope_geojson,
    slope_stats,
)
from app.services.transect_service import compute_transect

_CONTOUR_FLAG = "feature.contour.analysis"

router = APIRouter(prefix="/contour", tags=["contour"])
contour_router = router


def _require_flag() -> None:
    enabled = {f.strip() for f in os.getenv("FLAGS", "").split(",") if f.strip()}
    if _CONTOUR_FLAG not in enabled:
        raise HTTPException(status_code=403, detail=f"Feature flag disabled: {_CONTOUR_FLAG}")


def _cellsize(transform) -> float:
    return abs(float(transform.a)) or 30.0


def _hillshade_bounds(dem: dict) -> list[list[float]]:
    h, w = dem["array"].shape
    west, south, east, north = transform_bounds(
        dem["crs"], "EPSG:4326", *array_bounds(h, w, dem["transform"])
    )
    return [[float(south), float(west)], [float(north), float(east)]]


_EMPTY_CONTOURS_WARNING = (
    "No contour lines pass through the selected area at this interval. "
    "Try a smaller contour interval or add an analysis offset around the polygon."
)
_INTERVAL_10_WARNING = "Minimum reliable contour interval for Copernicus GLO-30 is 10m."


async def _analysis_arrays(polygon: dict, buffer_m: float = 0) -> tuple[dict, object, object, object]:
    if dem_service.site_area_ha(polygon) < 0.5:
        raise HTTPException(
            status_code=422,
            detail="Site polygon too small for DEM analysis at 30m resolution",
        )
    try:
        source = dem_service.select_dem_source(polygon)
        dem = await dem_service.fetch_dem(polygon, source, buffer_m=buffer_m)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"DEM fetch failed: {exc}") from exc

    cellsize = _cellsize(dem["transform"])
    slope_pct, aspect = compute_slope_aspect(dem["array"], cellsize)
    classes = slope_class_array(slope_pct)
    return dem, slope_pct, aspect, classes


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "contour"}


@router.post("/analyze", response_model=ContourResponse)
async def analyze_contour(request: ContourRequest) -> ContourResponse:
    _require_flag()
    dem, slope_pct, aspect, classes = await _analysis_arrays(request.polygon, request.buffer_m)
    interval = request.contour_interval
    site_mask = dem_service.raster_mask_from_polygon(dem, request.polygon)
    if not np.any(site_mask):
        site_mask = np.isfinite(dem["array"])
    slope_site = np.where(site_mask, slope_pct, np.nan)
    aspect_site = np.where(site_mask, aspect, np.nan)
    classes_site = np.where(site_mask, classes, 0).astype(classes.dtype)
    contour_geojson = generate_contours(dem["array"], dem["transform"], dem["crs"], interval)
    warning = _EMPTY_CONTOURS_WARNING if not contour_geojson.get("features") else (
        _INTERVAL_10_WARNING if interval == 10 else None
    )
    hillshade, _slope_rad, _aspect_rad = compute_hillshade(dem["array"], _cellsize(dem["transform"]))
    return ContourResponse(
        dem_metadata={
            "source": "copernicus",
            "resolution_m": dem.get("resolution_m", 30),
            "vertical_rmse_m": dem.get("vertical_rmse_m", 4.0),
            "contour_interval_m": interval,
            "warning": warning,
            "buffer_m": request.buffer_m,
        },
        slope_stats=slope_stats(slope_site),
        aspect_stats=aspect_stats(aspect_site),
        contour_geojson=contour_geojson,
        slope_geojson=slope_geojson(classes_site, dem["transform"], dem["crs"]),
        buildability_geojson=buildability_geojson(classes_site, dem["transform"], dem["crs"]),
        hillshade_png_b64=encode_png_b64(hillshade),
        hillshade_bounds=_hillshade_bounds(dem),
    )


@router.post("/transect", response_model=TransectResponse)
async def analyze_transect(request: TransectRequest) -> TransectResponse:
    _require_flag()
    dem, slope_pct, _aspect, classes = await _analysis_arrays(request.polygon, request.buffer_m)
    return await compute_transect(
        request.transect_line,
        dem["array"],
        dem["transform"],
        slope_pct,
        classes,
        dem["crs"],
        dem.get("source", "copernicus"),
    )
