"""
Wind Cyclone Hazard service smoke tests.

Run:
    pytest tests/wind_cyclone_smoke.py -v
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


@skip_no_app
def test_wind_cyclone_health():
    resp = CLIENT.get("/api/v1/wind-cyclone/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "ok"
    assert body.get("service") == "wind-cyclone"


@skip_no_app
def test_analyze_flag_off(monkeypatch):
    monkeypatch.setenv("FLAGS", "")
    resp = CLIENT.post(
        "/api/v1/wind-cyclone/analyze",
        json={"latitude": 13.0827, "longitude": 80.2707, "buffer_radius_km": 100.0},
    )
    assert resp.status_code == 403


@skip_no_app
def test_analyze_chennai_coastal(monkeypatch):
    monkeypatch.setenv("FLAGS", "feature.wind.cyclone-hazard")
    resp = CLIENT.post(
        "/api/v1/wind-cyclone/analyze",
        json={"latitude": 13.0827, "longitude": 80.2707, "buffer_radius_km": 100.0},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_within_india"] is True
    assert body["statutory_v_b_ms"] == 50.0
    assert "Very High Wind Hazard" in body["damage_risk_category"]
    assert body["is_coastal_buffer"] is True
    assert "terrain_wind_profile" in body
    assert "10m" in body["terrain_wind_profile"]
    assert "metrics" in body
    metrics = body["metrics"]
    assert metrics["total_historical_events"] > 0
    assert metrics["annual_rate_50yr"] > 0
    assert metrics["period_years"] == 50
    assert metrics["max_recorded_wind_speed_ms"] > 0
    assert "decadal_trend" in body
    assert "intensity_distribution" in body
    assert body["tracks"]["type"] == "FeatureCollection"
    assert len(body["tracks"]["features"]) > 0


@skip_no_app
def test_analyze_dynamic_date_range(monkeypatch):
    monkeypatch.setenv("FLAGS", "feature.wind.cyclone-hazard")
    # Test 10-year span 2010 to 2020
    resp = CLIENT.post(
        "/api/v1/wind-cyclone/analyze",
        json={
            "latitude": 13.0827,
            "longitude": 80.2707,
            "buffer_radius_km": 100.0,
            "start_date": "2010-01-01",
            "end_date": "2020-12-31",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    metrics = body["metrics"]
    assert metrics["period_years"] == 10
    assert metrics["annual_rate_50yr"] == round(metrics["total_historical_events"] / 10.0, 2)
    # Check that all returned tracks are within 2010-2020
    for feat in body["tracks"]["features"]:
        season = feat["properties"]["season"]
        assert 2010 <= season <= 2020

    # Test single-year span (period_years minimum 1)
    resp_1yr = CLIENT.post(
        "/api/v1/wind-cyclone/analyze",
        json={
            "latitude": 13.0827,
            "longitude": 80.2707,
            "buffer_radius_km": 100.0,
            "start_date": "2020-01-01",
            "end_date": "2020-12-31",
        },
    )
    assert resp_1yr.status_code == 200
    metrics_1yr = resp_1yr.json()["metrics"]
    assert metrics_1yr["period_years"] == 1
    assert metrics_1yr["annual_rate_50yr"] == round(metrics_1yr["total_historical_events"] / 1.0, 2)


@skip_no_app
def test_analyze_out_of_bounds(monkeypatch):
    monkeypatch.setenv("FLAGS", "feature.wind.cyclone-hazard")
    resp = CLIENT.post(
        "/api/v1/wind-cyclone/analyze",
        json={"latitude": 51.5074, "longitude": -0.1278, "buffer_radius_km": 100.0},
    )
    assert resp.status_code == 400
    assert "currently available only for locations within India" in resp.json()["detail"]


@skip_no_app
def test_recommendations_endpoint(monkeypatch):
    monkeypatch.setenv("FLAGS", "feature.wind.cyclone-hazard")
    resp = CLIENT.post(
        "/api/v1/wind-cyclone/recommendations",
        json={"latitude": 13.0827, "longitude": 80.2707, "buffer_radius_km": 100.0},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "recommended_design_wind_speed_ms" in body
    assert "statutory_wind_speed_ms" in body
    assert "is_design_speed_elevated" in body
    assert "prioritized_mitigations" in body
    assert len(body["prioritized_mitigations"]) > 0
    assert "early_warning_checklist" in body
    assert len(body["early_warning_checklist"]) > 0
