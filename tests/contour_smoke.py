"""
Contour service smoke tests.

Run:
    pytest tests/contour_smoke.py -v
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest
from affine import Affine

_CONTOUR_SERVICE = Path(__file__).resolve().parents[1] / "services" / "contour"
_CONTOUR_PATH = str(_CONTOUR_SERVICE)
if _CONTOUR_PATH in sys.path:
    sys.path.remove(_CONTOUR_PATH)
sys.path.insert(0, _CONTOUR_PATH)

sys.modules.pop("app", None)
sys.modules.pop("app.main", None)

APP_AVAILABLE = False
CLIENT = None  # type: ignore[assignment]
_APP_IMPORT_ERROR: str = ""

try:
    from app.main import app  # noqa: E402
    from fastapi.testclient import TestClient

    CLIENT = TestClient(app)
    APP_AVAILABLE = True
except Exception as _exc:  # noqa: BLE001
    _APP_IMPORT_ERROR = f"{type(_exc).__name__}: {_exc}"


skip_no_app = pytest.mark.skipif(
    not APP_AVAILABLE, reason=f"app/ not importable: {_APP_IMPORT_ERROR}"
)

BENGALURU_TEST_POLYGON = {
    "type": "Feature",
    "geometry": {
        "type": "Polygon",
        "coordinates": [
            [
                [77.5800, 12.9700],
                [77.5900, 12.9700],
                [77.5900, 12.9800],
                [77.5800, 12.9800],
                [77.5800, 12.9700],
            ]
        ],
    },
}

BENGALURU_TRANSECT = {
    "type": "LineString",
    "coordinates": [[77.5810, 12.9710], [77.5890, 12.9790]],
}


def _fake_dem():
    y, x = np.mgrid[0:48, 0:48]
    array = (900 + x * 1.8 + y * 0.9 + np.sin(x / 4) * 2).astype("float32")
    return {
        "array": array,
        "transform": Affine(30, 0, 779000, 0, -30, 1436000),
        "crs": "EPSG:32643",
        "resolution_m": 30,
        "nodata": np.nan,
        "source": "copernicus",
        "vertical_rmse_m": 4.0,
    }


@pytest.fixture(autouse=True)
def _patch_dem(monkeypatch):
    from app.services import dem_service

    async def fake_fetch_dem(*_args, **_kwargs):
        return _fake_dem()

    monkeypatch.setenv("FLAGS", "feature.contour.analysis")
    monkeypatch.setattr(dem_service, "fetch_dem", fake_fetch_dem)
    monkeypatch.setattr(dem_service, "site_area_ha", lambda *_args, **_kwargs: 1.25)


@skip_no_app
def test_health():
    resp = CLIENT.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "ok"
    assert body.get("service") == "contour"


@skip_no_app
def test_analyze_returns_contours():
    resp = CLIENT.post(
        "/contour/analyze",
        json={"polygon": BENGALURU_TEST_POLYGON, "contour_interval": 10},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["dem_metadata"]["source"] == "copernicus"
    assert len(body["contour_geojson"]["features"]) > 0
    assert len(body["slope_geojson"]["features"]) > 0
    assert len(body["buildability_geojson"]["features"]) > 0
    assert body["hillshade_png_b64"]
    bounds = body["hillshade_bounds"]
    assert bounds is not None
    assert len(bounds) == 2
    assert len(bounds[0]) == 2 and len(bounds[1]) == 2
    south, west = bounds[0]
    north, east = bounds[1]
    assert south < north
    assert west < east


@skip_no_app
def test_transect_returns_points():
    resp = CLIENT.post(
        "/contour/transect",
        json={"polygon": BENGALURU_TEST_POLYGON, "transect_line": BENGALURU_TRANSECT},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_length_m"] > 0
    assert len(body["points"]) > 0
    for pt in body["points"]:
        assert math.isfinite(pt["lat"])
        assert math.isfinite(pt["lng"])
    start_lng, start_lat = BENGALURU_TRANSECT["coordinates"][0]
    end_lng, end_lat = BENGALURU_TRANSECT["coordinates"][-1]
    first, last = body["points"][0], body["points"][-1]
    # Fake DEM is a 1.44 km UTM window; samples outside it are skipped, so last
    # included point can sit a few hundred metres short of the requested end.
    assert abs(first["lat"] - start_lat) < 0.01
    assert abs(first["lng"] - start_lng) < 0.01
    assert abs(last["lat"] - end_lat) < 0.01
    assert abs(last["lng"] - end_lng) < 0.01


@skip_no_app
def test_interval_below_min_returns_422():
    resp = CLIENT.post(
        "/contour/analyze",
        json={"polygon": BENGALURU_TEST_POLYGON, "contour_interval": 5},
    )
    assert resp.status_code == 422


@skip_no_app
def test_interval_above_max_returns_422():
    resp = CLIENT.post(
        "/contour/analyze",
        json={"polygon": BENGALURU_TEST_POLYGON, "contour_interval": 70},
    )
    assert resp.status_code == 422


@skip_no_app
def test_buffer_m_accepted_and_echoed():
    resp = CLIENT.post(
        "/contour/analyze",
        json={"polygon": BENGALURU_TEST_POLYGON, "contour_interval": 20, "buffer_m": 100},
    )
    assert resp.status_code == 200
    assert resp.json()["dem_metadata"]["buffer_m"] == 100


@skip_no_app
def test_buffer_m_default_is_zero():
    resp = CLIENT.post(
        "/contour/analyze",
        json={"polygon": BENGALURU_TEST_POLYGON, "contour_interval": 20},
    )
    assert resp.status_code == 200
    assert resp.json()["dem_metadata"]["buffer_m"] == 0


@skip_no_app
def test_buffer_m_above_max_returns_422():
    resp = CLIENT.post(
        "/contour/analyze",
        json={"polygon": BENGALURU_TEST_POLYGON, "contour_interval": 20, "buffer_m": 600},
    )
    assert resp.status_code == 422


@skip_no_app
def test_transect_accepts_buffer_m():
    resp = CLIENT.post(
        "/contour/transect",
        json={
            "polygon": BENGALURU_TEST_POLYGON,
            "transect_line": BENGALURU_TRANSECT,
            "buffer_m": 50,
        },
    )
    assert resp.status_code == 200
    assert len(resp.json()["points"]) > 0


@skip_no_app
def test_empty_contours_sets_warning(monkeypatch):
    import app.routers.contour as contour_router

    monkeypatch.setattr(
        contour_router,
        "generate_contours",
        lambda *_args, **_kwargs: {"type": "FeatureCollection", "features": []},
    )
    resp = CLIENT.post(
        "/contour/analyze",
        json={"polygon": BENGALURU_TEST_POLYGON, "contour_interval": 20},
    )
    assert resp.status_code == 200
    warning = resp.json()["dem_metadata"]["warning"] or ""
    assert "No contour lines" in warning


def test_buffered_geometry_expands():
    from shapely.geometry import shape

    from app.services.dem_service import buffered_geometry, extract_polygon_geometry

    orig = shape(extract_polygon_geometry(BENGALURU_TEST_POLYGON))
    same = shape(buffered_geometry(BENGALURU_TEST_POLYGON, 0))
    assert abs(same.area - orig.area) < 1e-12
    expanded = shape(buffered_geometry(BENGALURU_TEST_POLYGON, 100))
    assert expanded.area > orig.area


def test_raster_mask_from_polygon_excludes_outside():
    from shapely.geometry import shape
    from shapely.ops import transform as shapely_transform
    from pyproj import Transformer

    from app.services.dem_service import (
        _utm_epsg,
        extract_polygon_geometry,
        raster_mask_from_polygon,
    )

    geom = shape(extract_polygon_geometry(BENGALURU_TEST_POLYGON))
    centroid = geom.centroid
    crs = _utm_epsg(centroid.y, centroid.x)
    to_utm = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    projected = shapely_transform(to_utm.transform, geom)
    minx, miny, maxx, maxy = projected.bounds
    pad = 200
    west = minx - pad
    north = maxy + pad
    width, height = 40, 40
    transform = Affine(30, 0, west, 0, -30, north)
    dem = {
        "array": np.ones((height, width), dtype="float32"),
        "transform": transform,
        "crs": crs,
    }
    mask = raster_mask_from_polygon(dem, BENGALURU_TEST_POLYGON)
    assert mask.any()
    assert not mask.all()
