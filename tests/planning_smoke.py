"""
Planning service smoke tests.

Run:
    pytest tests/planning_smoke.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure services/planning is on sys.path so 'app' package is importable.
_PLANNING_SERVICE = Path(__file__).resolve().parents[1] / "services" / "planning"
_PLAN_PATH = str(_PLANNING_SERVICE)
if _PLAN_PATH in sys.path:
    sys.path.remove(_PLAN_PATH)
sys.path.insert(0, _PLAN_PATH)

# Ensure we import the planning app, not another service's app.
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
    assert body.get("service") == "planning"


@skip_no_app
def test_analyze_flag_off(monkeypatch):
    monkeypatch.setenv("FLAGS", "")
    resp = CLIENT.post(
        "/planning/analyze",
        json={
            "latitude": 12.97,
            "longitude": 77.59,
            "plot_area_sqm": 300.0,
            "zone_class": "Residential",
            "road_width_m": 12.0,
        },
    )
    assert resp.status_code == 403


@skip_no_app
def test_analyze_flag_on(monkeypatch):
    from app.models.planning import AirportRestriction, PlanningResult
    from app.routers import planning as planning_router

    monkeypatch.setenv("FLAGS", "feature.planning.site-capacity")

    async def _fake_analyze(_request):
        return PlanningResult(
            far_applicable=2.0,
            far_source="NBC 2016 Table 15 (Residential, road 12.0m)",
            ground_coverage_max=0.55,
            setback_front_m=3.0,
            setback_rear_m=3.0,
            setback_side_m=1.5,
            max_height_m=45.0,
            height_limiting_factor="NBC 2016 zone height limit",
            buildable_area_sqm=600.0,
            road_width_used_m=12.0,
            road_width_source="user_input",
            tod_applicable=False,
            airport_restriction=AirportRestriction(
                nearest_airport="Kempegowda International",
                iata_code="BLR",
                distance_km=30.0,
                max_height_m=None,
                restriction_surface="No restriction",
                dgca_noc_required=False,
            ),
            score=80.0,
            severity="low",
            data_source="NBC 2016 + BDA CDP 2031 + BDA TOD 2020 + ICAO Annex 14 + AAI airports + OSM road width",
        )

    monkeypatch.setattr(planning_router._service, "analyze", _fake_analyze)

    resp = CLIENT.post(
        "/planning/analyze",
        json={
            "latitude": 12.97,
            "longitude": 77.59,
            "plot_area_sqm": 300.0,
            "zone_class": "Residential",
            "road_width_m": 12.0,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["far_applicable"] == 2.0
    assert body["buildable_area_sqm"] == 600.0
    assert body["severity"] == "low"
