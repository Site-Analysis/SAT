"""
Flood service smoke tests.

Run:
    pytest tests/flood_smoke.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_FLOOD_SERVICE = Path(__file__).resolve().parents[1] / "services" / "flood"
_FLOOD_PATH = str(_FLOOD_SERVICE)
if _FLOOD_PATH in sys.path:
    sys.path.remove(_FLOOD_PATH)
sys.path.insert(0, _FLOOD_PATH)

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
def test_health():
    resp = CLIENT.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "ok"
    assert body.get("service") == "flood"


@skip_no_app
def test_analyze_flag_off(monkeypatch):
    monkeypatch.setenv("FLAGS", "")
    resp = CLIENT.post(
        "/flood/analyze",
        json={"latitude": 19.07, "longitude": 72.87, "radius_meters": 1000},
    )
    assert resp.status_code == 403


@skip_no_app
def test_analyze_flag_on(monkeypatch):
    # The service fetches live Open-Meteo + Overpass data; stub the fetchers so the
    # real risk scoring runs deterministically without network access.
    from app.routers import flood as flood_router

    monkeypatch.setenv("FLAGS", "feature.flood.risk-analysis")
    monkeypatch.setattr(flood_router.service, "_fetch_elevation", lambda *a, **k: 8.0)
    monkeypatch.setattr(
        flood_router.service,
        "_fetch_rain",
        lambda *a, **k: {"annual_mean_mm": 2400.0, "max_daily_mm": 180.0, "high_rain_days": 22},
    )
    monkeypatch.setattr(flood_router.service, "_fetch_water_distance", lambda *a, **k: 150.0)

    resp = CLIENT.post(
        "/flood/analyze",
        json={"latitude": 19.07, "longitude": 72.87, "radius_meters": 1000},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert 0 <= body["overall_score"] <= 100
    components = body.get("component_scores")
    assert components is not None
    for key in ("elevation_risk", "hydrology_risk", "historical_risk", "llai_risk"):
        assert key in components
    # Coastal (8 m) + near water (150 m) + heavy rain → elevated risk.
    assert body["overall_score"] > 40
    assert body["metadata"]["gee_enabled"] is False
    assert "Open-Meteo" in body["metadata"]["data_source"]


@skip_no_app
def test_overpass_request_sets_user_agent():
    """Public Overpass mirrors 406 the default httpx UA — the header must be sent.

    Guards a silent failure: _fetch_water_distance swallows the error and returns
    the search radius, so a rejected request looks like "no water nearby" and
    quietly flattens hydrology risk for every site.
    """
    from app.routers import flood as flood_router

    sent = {}

    class _FakeResp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"elements": []}

    class _FakeClient:
        def post(self, url, **kwargs):
            sent["url"] = url
            sent["headers"] = kwargs.get("headers") or {}
            return _FakeResp()

    flood_router.service._fetch_water_distance(_FakeClient(), 19.07, 72.87, 1000.0)

    ua = sent["headers"].get("User-Agent", "")
    assert "overpass" in sent["url"].lower()
    assert ua, "no User-Agent sent to Overpass"
    assert "httpx" not in ua.lower(), f"default httpx UA leaked: {ua!r}"
