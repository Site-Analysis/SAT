"""
Wind service smoke tests.

Run:
    pytest tests/wind_smoke.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_WIND_SERVICE = Path(__file__).resolve().parents[1] / "services" / "wind"
_WIND_PATH = str(_WIND_SERVICE)
if _WIND_PATH in sys.path:
    sys.path.remove(_WIND_PATH)
sys.path.insert(0, _WIND_PATH)

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


def _install_fake_httpx(monkeypatch):
    """Stub the Open-Meteo archive call so the real parsing/scoring runs offline.

    Provides ~5 daily samples per month across a year (speed/gust/direction) so the
    seasonal means and prevailing-direction logic exercise real code paths.
    """
    times, speeds, gusts, dirs = [], [], [], []
    for month in range(1, 13):
        for day in (5, 10, 15, 20, 25):
            times.append(f"2024-{month:02d}-{day:02d}")
            speeds.append(4.0 + (month % 3))  # 4–6 m/s
            gusts.append(11.0 + (month % 4))  # ~11–14 m/s
            dirs.append(225.0)  # Southwest dominant

    payload = {
        "daily": {
            "time": times,
            "windspeed_10m_max": speeds,
            "windgusts_10m_max": gusts,
            "winddirection_10m_dominant": dirs,
        }
    }

    class _FakeResp:
        def raise_for_status(self):
            return None

        def json(self):
            return payload

    class _FakeClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def get(self, *a, **k):
            return _FakeResp()

    from app.services import wind_service

    monkeypatch.setattr(wind_service.httpx, "Client", _FakeClient)


@skip_no_app
def test_health():
    resp = CLIENT.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "ok"
    assert body.get("service") == "wind"


@skip_no_app
def test_analyze_flag_off(monkeypatch):
    monkeypatch.setenv("FLAGS", "")
    resp = CLIENT.post(
        "/wind/analyze",
        json={"latitude": 28.6139, "longitude": 77.2090, "radius_meters": 1000},
    )
    assert resp.status_code == 403


@skip_no_app
def test_analyze_flag_on(monkeypatch):
    monkeypatch.setenv("FLAGS", "feature.wind.analysis")
    _install_fake_httpx(monkeypatch)
    resp = CLIENT.post(
        "/wind/analyze",
        json={"latitude": 28.6139, "longitude": 77.2090, "radius_meters": 1000},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "average_wind_speed" in body
    assert "max_wind_speed" in body
    assert "prevailing_direction" in body
    assert "wind_category" in body
    assert "gust_risk" in body
    assert "seasonal_analysis" in body
    assert "comfort_analysis" in body
    assert "building_impact" in body
    assert "recommendations" in body
    assert "metadata" in body


@skip_no_app
def test_analyze_response_shape(monkeypatch):
    monkeypatch.setenv("FLAGS", "feature.wind.analysis")
    _install_fake_httpx(monkeypatch)
    resp = CLIENT.post(
        "/wind/analyze",
        json={"latitude": 19.07, "longitude": 72.87, "radius_meters": 1500},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert 0 < body["average_wind_speed"] < 25
    assert body["max_wind_speed"] > body["average_wind_speed"]
    assert body["prevailing_direction"] in [
        "North",
        "Northeast",
        "East",
        "Southeast",
        "South",
        "Southwest",
        "West",
        "Northwest",
    ]
    assert "comfort_analysis" in body
    comfort = body["comfort_analysis"]
    assert comfort["pedestrian_comfort"] in ["Poor", "Fair", "Good", "Excellent"]
    assert comfort["natural_ventilation_potential"] in ["Poor", "Fair", "Good", "Excellent"]
    assert comfort["outdoor_usability"] in ["Poor", "Fair", "Good", "Excellent"]
    building = body["building_impact"]
    assert 0 <= building["cross_ventilation_score"] <= 100
    assert building["wind_load_risk"] in ["Low", "Moderate", "High", "Very High"]
