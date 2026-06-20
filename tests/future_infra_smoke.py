"""
Future-infra (growth pipeline) service smoke tests.

Run:
    pytest tests/future_infra_smoke.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure services/future-infra is on sys.path so 'app' package is importable.
_FI_SERVICE = Path(__file__).resolve().parents[1] / "services" / "future-infra"
_FI_PATH = str(_FI_SERVICE)
if _FI_PATH in sys.path:
    sys.path.remove(_FI_PATH)
sys.path.insert(0, _FI_PATH)

# Ensure we import the future-infra app, not another service's app.
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
    assert body.get("service") == "future-infra"


@skip_no_app
def test_pipeline_flag_off(monkeypatch):
    monkeypatch.setenv("FLAGS", "")
    resp = CLIENT.get(
        "/future-infra/pipeline",
        params={"lat": 12.97, "lon": 77.59, "radius_km": 10.0},
    )
    assert resp.status_code == 403


@skip_no_app
def test_pipeline_flag_on(monkeypatch):
    from app.models.future_infra import PipelineItem, PipelineResult
    from app.routers import future_infra as fi_router

    monkeypatch.setenv("FLAGS", "feature.context.growth-pipeline")

    def _fake_pipeline(_lat, _lon, _radius_km):
        return PipelineResult(
            within_radius_km=10.0,
            pipeline_items=[
                PipelineItem(
                    type="metro",
                    name="Namma Metro Phase 3",
                    status="Approved",
                    distance_km=2.4,
                    source="BMRCL",
                    source_date="2024-Q4",
                )
            ],
            score=72.0,
            severity="low",
            data_source="Curated — BMRCL, BDA, NHAI, KIADB, MoCI (2024)",
            data_as_of="2024-Q4",
        )

    monkeypatch.setattr(fi_router._service, "get_pipeline", _fake_pipeline)

    resp = CLIENT.get(
        "/future-infra/pipeline",
        params={"lat": 12.97, "lon": 77.59, "radius_km": 10.0},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["score"] == 72.0
    assert body["pipeline_items"][0]["type"] == "metro"
