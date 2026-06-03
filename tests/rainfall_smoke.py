"""
Rainfall service smoke tests.

Run:
    pytest tests/rainfall_smoke.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure services/rainfall is on sys.path so 'app' package is importable.
_RAINFALL_SERVICE = Path(__file__).resolve().parents[1] / "services" / "rainfall"
_RAIN_PATH = str(_RAINFALL_SERVICE)
if _RAIN_PATH in sys.path:
    sys.path.remove(_RAIN_PATH)
sys.path.insert(0, _RAIN_PATH)

# Ensure we import the rainfall app, not the temperature app.
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
    assert body.get("service") == "rainfall"


@skip_no_app
def test_archive_flag_off(monkeypatch):
    monkeypatch.setenv("FLAGS", "")
    resp = CLIENT.get(
        "/rainfall/archive",
        params={
            "latitude": 19.07,
            "longitude": 72.87,
            "start_date": "2023-01-01",
            "end_date": "2023-01-10",
        },
    )
    assert resp.status_code == 403


@skip_no_app
def test_summary_flag_off(monkeypatch):
    monkeypatch.setenv("FLAGS", "")
    resp = CLIENT.post(
        "/rainfall/summary",
        json={
            "latitude": 19.07,
            "longitude": 72.87,
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",
        },
    )
    assert resp.status_code == 403


@skip_no_app
def test_archive_flag_on(monkeypatch):
    from app.models.rainfall import RainfallArchiveDaily, RainfallArchiveDailyUnits
    from app.routers import rainfall as rainfall_router

    monkeypatch.setenv("FLAGS", "feature.rainfall.archive")

    def _fake_archive(*args, **kwargs):
        return rainfall_router.RainfallArchiveResponse(  # type: ignore[attr-defined]
            latitude=19.07,
            longitude=72.87,
            timezone="UTC",
            daily_units=RainfallArchiveDailyUnits(),
            daily=RainfallArchiveDaily(
                time=["2023-01-01", "2023-01-02"],
                precipitation_sum=[2.0, 0.0],
            ),
            source="open-meteo",
        )

    monkeypatch.setattr(rainfall_router.service, "get_archive", _fake_archive)

    resp = CLIENT.get(
        "/rainfall/archive",
        params={
            "latitude": 19.07,
            "longitude": 72.87,
            "start_date": "2023-01-01",
            "end_date": "2023-01-02",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["daily"]["precipitation_sum"] == [2.0, 0.0]


@skip_no_app
def test_summary_flag_on(monkeypatch):
    from app.models.rainfall import RainfallDateRange, RainfallSummaryResponse
    from app.routers import rainfall as rainfall_router

    monkeypatch.setenv("FLAGS", "feature.rainfall.summary")

    def _fake_summary(*args, **kwargs):
        return RainfallSummaryResponse(
            total_rainfall_mm=10.0,
            mean_daily_rainfall_mm=1.0,
            max_daily_rainfall_mm=3.0,
            rainy_days=6,
            dry_days=4,
            date_range=RainfallDateRange(start_date="2023-01-01", end_date="2023-01-10"),
            source="open-meteo",
        )

    monkeypatch.setattr(rainfall_router.service, "get_summary", _fake_summary)

    resp = CLIENT.post(
        "/rainfall/summary",
        json={
            "latitude": 19.07,
            "longitude": 72.87,
            "start_date": "2023-01-01",
            "end_date": "2023-01-10",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_rainfall_mm"] == 10.0
