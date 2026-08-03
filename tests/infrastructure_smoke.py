"""
Infrastructure service smoke tests.

Run:
    pytest tests/infrastructure_smoke.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure services/infrastructure is on sys.path so 'app' package is importable.
_INFRA_SERVICE = Path(__file__).resolve().parents[1] / "services" / "infrastructure"
_INFRA_PATH = str(_INFRA_SERVICE)
if _INFRA_PATH in sys.path:
    sys.path.remove(_INFRA_PATH)
sys.path.insert(0, _INFRA_PATH)

# Ensure we import the infrastructure app, not another service's app.
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
    assert body.get("service") == "infrastructure"


@skip_no_app
def test_analyze_flag_off(monkeypatch):
    monkeypatch.setenv("FLAGS", "")
    resp = CLIENT.post(
        "/infrastructure/analyze",
        json={"latitude": 12.97, "longitude": 77.59, "radius_m": 2000},
    )
    assert resp.status_code == 403


@skip_no_app
def test_analyze_flag_on(monkeypatch):
    from app.models.infrastructure import (
        InfraResult,
        InfraSubScores,
        RoadAccess,
        TransitStop,
        UtilityPresence,
    )
    from app.routers import infrastructure as infra_router

    monkeypatch.setenv("FLAGS", "feature.infrastructure.connectivity")

    async def _fake_analyze(_lat, _lon, _radius_m=2000):
        return InfraResult(
            road_access=RoadAccess(nearest_road_m=25.0, road_type="residential", frontage_present=True),
            transit=[TransitStop(type="metro", name="MG Road", distance_m=400.0)],
            utilities=UtilityPresence(
                water_supply_nearby=False,
                power_substation_nearby=True,
                storm_drainage_nearby=False,
                sewage_works_nearby=False,
            ),
            sub_scores=InfraSubScores(road=45.0, transit=25.0, power=15.0, water=0.0, telecom=0.0),
            score=85.0,
            severity="low",
            data_source="OpenStreetMap (Overpass API) — roads, transit, power",
        )

    monkeypatch.setattr(infra_router._service, "analyze", _fake_analyze)

    resp = CLIENT.post(
        "/infrastructure/analyze",
        json={"latitude": 12.97, "longitude": 77.59, "radius_m": 2000},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["score"] == 85.0
    assert body["sub_scores"]["road"] == 45.0
    assert body["transit"][0]["type"] == "metro"


@skip_no_app
def test_overpass_request_sets_user_agent(monkeypatch):
    """Public Overpass mirrors 406 the default httpx UA — the header must be sent.

    Without it every /infrastructure/analyze call fails 502 at the upstream.
    """
    import httpx

    from app.services import infrastructure_service as svc

    seen = {}

    class _FakeAsyncClient:
        def __init__(self, *a, **kwargs):
            seen["headers"] = kwargs.get("headers") or {}

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def post(self, url, **kwargs):
            seen["url"] = url
            return httpx.Response(200, json={"elements": []})

    monkeypatch.setattr(svc.httpx, "AsyncClient", _FakeAsyncClient)

    import asyncio

    asyncio.run(svc.InfrastructureService().analyze(12.97, 77.59, 2000))

    ua = seen["headers"].get("User-Agent", "")
    assert "overpass" in seen["url"].lower()
    assert ua, "no User-Agent sent to Overpass"
    assert "httpx" not in ua.lower(), f"default httpx UA leaked: {ua!r}"
