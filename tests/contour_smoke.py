"""
Contour service smoke tests.

Run:
    pytest tests/contour_smoke.py -v
"""

from __future__ import annotations

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
