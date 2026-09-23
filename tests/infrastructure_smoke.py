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
            # `request=` is required: the service now calls raise_for_status() to
            # detect rate-limit statuses, and httpx refuses that on a response with
            # no request attached. Real httpx always sets it.
            return httpx.Response(200, json={"elements": []}, request=httpx.Request("POST", url))

    monkeypatch.setattr(svc.httpx, "AsyncClient", _FakeAsyncClient)

    import asyncio

    asyncio.run(svc.InfrastructureService().analyze(12.97, 77.59, 2000))

    ua = seen["headers"].get("User-Agent", "")
    assert "overpass" in seen["url"].lower()
    assert ua, "no User-Agent sent to Overpass"
    assert "httpx" not in ua.lower(), f"default httpx UA leaked: {ua!r}"


@skip_no_app
def test_overpass_rate_limit_is_retried_before_502(monkeypatch):
    """A rate-limited query must be retried, not collapsed straight into a 502.

    Regression guard for #91: analyze() fires five Overpass queries back to back,
    which exhausts the per-IP slots. The old code called .json() without checking
    the status, so a 429/504 HTML body raised and every upstream condition became
    one opaque 502 — 0/6 requests succeeded in production.
    """
    import asyncio

    from app.services import infrastructure_service as isvc

    monkeypatch.setattr(isvc, "_OVERPASS_ATTEMPTS", 2)
    monkeypatch.setattr(isvc, "_OVERPASS_BACKOFF_S", 0.0)
    calls = {"n": 0}

    class _Resp:
        def __init__(self, status):
            self.status_code = status
            self.request = None

        def raise_for_status(self):
            return None

        def json(self):
            return {"elements": []}

    class _Client:
        async def post(self, url, **kwargs):
            calls["n"] += 1
            return _Resp(429 if calls["n"] == 1 else 200)

    out = asyncio.run(isvc._overpass_post(_Client(), "[out:json];", "road"))

    assert calls["n"] == 2, "the 429 was not retried"
    assert out == {"elements": []}


@skip_no_app
def test_overpass_gives_up_after_attempts(monkeypatch):
    """Persistent failure still raises, so analyze() can surface its 502."""
    import asyncio

    import pytest as _pytest
    from app.services import infrastructure_service as isvc

    monkeypatch.setattr(isvc, "_OVERPASS_ATTEMPTS", 2)
    monkeypatch.setattr(isvc, "_OVERPASS_BACKOFF_S", 0.0)
    calls = {"n": 0}

    class _Resp:
        status_code = 504
        request = None

        def raise_for_status(self):
            return None

        def json(self):
            return {}

    class _Client:
        async def post(self, url, **kwargs):
            calls["n"] += 1
            return _Resp()

    with _pytest.raises(Exception):
        asyncio.run(isvc._overpass_post(_Client(), "[out:json];", "road"))
    assert calls["n"] == 2, "did not use every allotted attempt"


@skip_no_app
def test_merged_response_splits_back_into_the_original_five_groups():
    """The single merged query must reconstruct exactly what five queries returned.

    This is the whole risk of collapsing the five requests into one (#91 option 2):
    Overpass returns one flat element list, and `road_access` picks the *nearest*
    element from its group — so if a bus stop leaked into the road group it would win
    the "nearest road" slot and silently change every road score.

    One representative element per original query clause, plus two deliberate traps.
    """
    from app.services import infrastructure_service as isvc

    elements = [
        # road_query — way with a road highway value
        {"type": "way", "id": 1, "tags": {"highway": "primary", "name": "MG Rd"}},
        # transit_query — all three clauses
        {"type": "node", "id": 2, "tags": {"railway": "station", "name": "Majestic"}},
        {
            "type": "node",
            "id": 3,
            "tags": {"public_transport": "stop_position", "network": "BMTC"},
        },
        {"type": "node", "id": 4, "tags": {"highway": "bus_stop", "name": "Stop"}},
        # utility_query — node clauses and the way clause
        {"type": "node", "id": 5, "tags": {"amenity": "water_works"}},
        {"type": "node", "id": 6, "tags": {"man_made": "water_tower"}},
        {"type": "node", "id": 7, "tags": {"power": "substation"}},
        {"type": "node", "id": 8, "tags": {"man_made": "sewage_works"}},
        {"type": "way", "id": 9, "tags": {"waterway": "drain"}},
        # power_query
        {"type": "way", "id": 10, "tags": {"power": "line"}},
        {"type": "way", "id": 11, "tags": {"power": "cable"}},
        # telecom_query — including the tower:type clause
        {"type": "node", "id": 12, "tags": {"man_made": "mast"}},
        {"type": "node", "id": 13, "tags": {"man_made": "communications_tower"}},
        {
            "type": "node",
            "id": 14,
            "tags": {"man_made": "tower", "tower:type": "communication"},
        },
        # Trap 1: a bus stop is a node, and must NEVER land in the road group even
        # though it carries a `highway` tag.
        {"type": "node", "id": 15, "tags": {"highway": "bus_stop"}},
        # Trap 2: a plain tower is NOT telecom without tower:type=communication.
        {"type": "node", "id": 16, "tags": {"man_made": "tower"}},
        # Trap 3: stop_position without a network did not match the original filter.
        {"type": "node", "id": 17, "tags": {"public_transport": "stop_position"}},
    ]

    split = isvc._split_by_group(elements)
    ids = {g: sorted(e["id"] for e in payload["elements"]) for g, payload in split.items()}

    assert ids["road"] == [1], f"road group wrong: {ids['road']}"
    assert ids["transit"] == [2, 3, 4, 15], f"transit group wrong: {ids['transit']}"
    assert ids["utility"] == [5, 6, 7, 8, 9], f"utility group wrong: {ids['utility']}"
    assert ids["power"] == [10, 11], f"power group wrong: {ids['power']}"
    assert ids["telecom"] == [12, 13, 14], f"telecom group wrong: {ids['telecom']}"


@skip_no_app
def test_element_matching_two_queries_appears_in_both_groups():
    """Multi-membership is intentional — five separate queries returned it twice.

    A substation mapped as a node with a power tag matched utility_query; were it also
    to match another clause, both responses contained it. Dropping it from one group
    to make the split tidy would be a behaviour change.
    """
    from app.services import infrastructure_service as isvc

    # A way that is both a drain (utility) and carries a road highway value (road).
    el = {"type": "way", "id": 99, "tags": {"waterway": "drain", "highway": "service"}}
    groups = isvc._groups_for(el)
    assert groups == {"road", "utility"}, groups

    split = isvc._split_by_group([el])
    assert [e["id"] for e in split["road"]["elements"]] == [99]
    assert [e["id"] for e in split["utility"]["elements"]] == [99]


@skip_no_app
def test_split_deduplicates_within_a_group():
    """Two `out` statements can print the same element; it must count once per group."""
    from app.services import infrastructure_service as isvc

    el = {"type": "way", "id": 42, "tags": {"highway": "primary"}}
    split = isvc._split_by_group([el, dict(el)])
    assert [e["id"] for e in split["road"]["elements"]] == [42]
