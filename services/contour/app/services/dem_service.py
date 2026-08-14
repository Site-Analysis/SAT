# Copyright (c) 2026 Qnit. All rights reserved.
# SPDX-License-Identifier: LicenseRef-Proprietary

from __future__ import annotations

import logging
import math
import os
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import numpy as np


def _configure_proj_data_dir() -> None:
    proj_data_dir = Path(sys.prefix) / "Lib" / "site-packages" / "pyproj" / "proj_dir" / "share" / "proj"
    if proj_data_dir.exists():
        os.environ["PROJ_DATA"] = str(proj_data_dir)
        os.environ["PROJ_LIB"] = str(proj_data_dir)


_configure_proj_data_dir()

import rasterio
import pyproj.datadir
from pyproj import Transformer
from rasterio.io import MemoryFile
from rasterio.mask import mask
from rasterio.warp import Resampling, calculate_default_transform, reproject
from scipy import ndimage
from shapely.geometry import mapping, shape
from shapely.ops import transform as shapely_transform

logger = logging.getLogger(__name__)
pyproj.datadir.set_data_dir(os.environ["PROJ_DATA"])

COPERNICUS_COLLECTION_ID = "COPERNICUS/DEM/GLO30_2024_1"
COPERNICUS_BAND = "DEM"
_GEE_CLIENT: Any | None = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _ensure_settings_path() -> None:
    settings_src = _repo_root() / "packages" / "settings" / "src"
    if settings_src.exists() and str(settings_src) not in sys.path:
        sys.path.append(str(settings_src))


def extract_polygon_geometry(geojson: dict) -> dict:
    if geojson.get("type") == "FeatureCollection":
        for feature in geojson.get("features", []):
            geometry = feature.get("geometry")
            if geometry and geometry.get("type") in {"Polygon", "MultiPolygon"}:
                return geometry
    if geojson.get("type") == "Feature":
        geometry = geojson.get("geometry")
        if geometry and geometry.get("type") in {"Polygon", "MultiPolygon"}:
            return geometry
    if geojson.get("type") in {"Polygon", "MultiPolygon"}:
        return geojson
    raise ValueError("A GeoJSON Polygon or MultiPolygon is required")


def site_area_ha(polygon_geojson: dict) -> float:
    geometry = shape(extract_polygon_geometry(polygon_geojson))
    centroid = geometry.centroid
    crs = _utm_epsg(centroid.y, centroid.x)
    transformer = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    projected = shapely_transform(transformer.transform, geometry)
    return projected.area / 10_000


def compute_centroid(polygon_geojson: dict) -> dict[str, float]:
    centroid = shape(extract_polygon_geometry(polygon_geojson)).centroid
    return {"lat": float(centroid.y), "lon": float(centroid.x)}


def select_dem_source(_polygon_geojson: dict) -> str:
    return "copernicus"


def _utm_epsg(lat: float, lon: float) -> str:
    zone = int(math.floor((lon + 180) / 6) + 1)
    return f"EPSG:{32600 + zone if lat >= 0 else 32700 + zone}"


def _fill_sinks(array: np.ndarray) -> np.ndarray:
    valid = np.isfinite(array)
    if not valid.any():
        return array
    filled = array.copy()
    min_value = float(np.nanmin(filled))
    filled[~valid] = min_value
    floor = ndimage.grey_closing(filled, size=(3, 3))
    return np.maximum(filled, floor).astype("float32")


def _smooth_dem(array: np.ndarray) -> np.ndarray:
    filled = _fill_sinks(array)
    return ndimage.gaussian_filter(filled, sigma=0.8).astype("float32")


def initialize_gee_client() -> Any:
    global _GEE_CLIENT
    if _GEE_CLIENT is not None:
        return _GEE_CLIENT

    _ensure_settings_path()
    try:
        from gee import initialize_gee

        _GEE_CLIENT = initialize_gee()
        return _GEE_CLIENT
    except Exception as exc:
        logger.exception("Shared GEE service-account initialization failed")
        raise RuntimeError("Shared GEE service-account initialization failed") from exc


def _download_copernicus_dem(ee: Any, polygon_geojson: dict) -> bytes:
    geometry = extract_polygon_geometry(polygon_geojson)
    ee_geom = ee.Geometry(geometry)
    collection = ee.ImageCollection(COPERNICUS_COLLECTION_ID)
    native_projection = collection.first().projection()
    image = collection.mosaic().setDefaultProjection(native_projection).select(COPERNICUS_BAND)
    image = image.clip(ee_geom)
    url = image.getDownloadURL(
        {
            "region": ee_geom,
            "scale": 30,
            "format": "GEO_TIFF",
            "crs": "EPSG:4326",
        }
    )
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def _read_downloaded_tiff(data: bytes) -> tuple[np.ndarray, Any, Any, float | None]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "dem_download"
        path.write_bytes(data)
        candidate = path
        if data[:2] == b"PK":
            with ZipFile(path) as archive:
                archive.extractall(tmp)
            tiffs = list(Path(tmp).glob("*.tif")) + list(Path(tmp).glob("*.tiff"))
            if not tiffs:
                raise RuntimeError("GEE DEM download did not contain a GeoTIFF")
            candidate = tiffs[0]
        with rasterio.open(candidate) as src:
            array = src.read(1).astype("float32")
            nodata = src.nodata
            if nodata is not None:
                array[array == nodata] = np.nan
            return array, src.transform, src.crs, nodata


def _project_raster(
    array: np.ndarray,
    transform: Any,
    source_crs: Any,
    polygon_geojson: dict,
) -> dict[str, Any]:
    centroid = compute_centroid(polygon_geojson)
    dest_crs = _utm_epsg(centroid["lat"], centroid["lon"])
    geometry = shape(extract_polygon_geometry(polygon_geojson))
    transformer = Transformer.from_crs("EPSG:4326", dest_crs, always_xy=True)
    projected_geometry = shapely_transform(transformer.transform, geometry)

    bounds = rasterio.transform.array_bounds(array.shape[0], array.shape[1], transform)
    dest_transform, width, height = calculate_default_transform(
        source_crs, dest_crs, array.shape[1], array.shape[0], *bounds, resolution=30
    )
    dest = np.full((height, width), np.nan, dtype="float32")
    reproject(
        source=array,
        destination=dest,
        src_transform=transform,
        src_crs=source_crs,
        dst_transform=dest_transform,
        dst_crs=dest_crs,
        resampling=Resampling.bilinear,
        src_nodata=np.nan,
        dst_nodata=np.nan,
    )

    profile = {
        "driver": "GTiff",
        "height": dest.shape[0],
        "width": dest.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": dest_crs,
        "transform": dest_transform,
        "nodata": np.nan,
    }
    with MemoryFile() as memfile:
        with memfile.open(**profile) as dataset:
            dataset.write(dest, 1)
            clipped, clipped_transform = mask(
                dataset, [mapping(projected_geometry)], crop=True, filled=True, nodata=np.nan
            )
    return {
        "array": _smooth_dem(clipped[0].astype("float32")),
        "transform": clipped_transform,
        "crs": dest_crs,
        "resolution_m": 30,
        "nodata": np.nan,
        "source": "copernicus",
        "vertical_rmse_m": 4.0,
    }


async def fetch_dem(polygon_geojson: dict, source: str = "copernicus") -> dict[str, Any]:
    if source != "copernicus":
        logger.warning("Unsupported DEM source %s requested; using Copernicus", source)
    ee = initialize_gee_client()
    data = _download_copernicus_dem(ee, polygon_geojson)
    array, transform, source_crs, _nodata = _read_downloaded_tiff(data)
    return _project_raster(array, transform, source_crs, polygon_geojson)
