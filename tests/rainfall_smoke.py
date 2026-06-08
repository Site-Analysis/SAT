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


@skip_no_app
def test_climate_profile_flag_on(monkeypatch):
    from app.models.rainfall import ClimateProfileResponse
    from app.routers import rainfall as rainfall_router

    monkeypatch.setenv("FLAGS", "feature.rainfall.climate-profile")

    def _fake_climate(*args, **kwargs):
        return ClimateProfileResponse(
            latitude=19.07,
            longitude=72.87,
            annual_rainfall_mm=720.5,
            wettest_month="9",
            driest_month="4",
            rainfall_variability=0.42,
            monsoon_strength=65.3,
            climate_classification="Cw (Temperate Monsoon)",
            rainfall_reliability_score=82.4,
            datasets=["CHIRPS Daily (UCSB-CHG)"],
        )

    monkeypatch.setattr(rainfall_router.service, "get_climate_profile", _fake_climate)

    resp = CLIENT.get(
        "/rainfall/climate-profile",
        params={"latitude": 19.07, "longitude": 72.87},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["annual_rainfall_mm"] == 720.5
    assert body["climate_classification"] == "Cw (Temperate Monsoon)"
    assert body["monsoon_strength"] == 65.3


@skip_no_app
def test_anomaly_flag_on(monkeypatch):
    from app.models.rainfall import AnomalyResponse
    from app.routers import rainfall as rainfall_router

    monkeypatch.setenv("FLAGS", "feature.rainfall.anomaly")

    def _fake_anomaly(*args, **kwargs):
        return AnomalyResponse(
            latitude=19.07,
            longitude=72.87,
            period_label="Last 30 days",
            current_period_rainfall_mm=85.2,
            long_term_average_mm=62.1,
            anomaly_percent=37.2,
            anomaly_category="Wet",
            datasets=["CHIRPS Daily (UCSB-CHG)"],
        )

    monkeypatch.setattr(rainfall_router.service, "get_anomaly", _fake_anomaly)

    resp = CLIENT.get(
        "/rainfall/anomaly",
        params={"latitude": 19.07, "longitude": 72.87, "days": 30},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["anomaly_category"] == "Wet"
    assert body["anomaly_percent"] == 37.2


@skip_no_app
def test_seasonality_flag_on(monkeypatch):
    from app.models.rainfall import SeasonalityResponse
    from app.routers import rainfall as rainfall_router

    monkeypatch.setenv("FLAGS", "feature.rainfall.seasonality")

    def _fake_seasonality(*args, **kwargs):
        return SeasonalityResponse(
            latitude=19.07,
            longitude=72.87,
            summer_rainfall_mm=125.3,
            monsoon_rainfall_mm=470.2,
            winter_rainfall_mm=95.1,
            spring_rainfall_mm=29.9,
            seasonal_distribution={
                "summer": 17.4,
                "monsoon": 65.3,
                "winter": 13.2,
                "spring": 4.1,
            },
            rainfall_concentration_index=0.58,
            datasets=["CHIRPS Daily (UCSB-CHG)"],
        )

    monkeypatch.setattr(rainfall_router.service, "get_seasonality", _fake_seasonality)

    resp = CLIENT.get(
        "/rainfall/seasonality",
        params={"latitude": 19.07, "longitude": 72.87},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["monsoon_rainfall_mm"] == 470.2
    assert body["rainfall_concentration_index"] == 0.58


@skip_no_app
def test_site_analysis_flag_on(monkeypatch):
    from app.models.rainfall import SiteAnalysisResponse, SuitabilityScores
    from app.routers import rainfall as rainfall_router

    monkeypatch.setenv("FLAGS", "feature.rainfall.site-analysis")

    def _fake_site_analysis(*args, **kwargs):
        return SiteAnalysisResponse(
            latitude=19.07,
            longitude=72.87,
            radius_meters=5000,
            annual_rainfall_mm=720.5,
            summer_rainfall_mm=125.3,
            monsoon_rainfall_mm=470.2,
            winter_rainfall_mm=95.1,
            spring_rainfall_mm=29.9,
            rainfall_trend_5yr_percent=1.2,
            rainfall_trend_10yr_percent=-0.8,
            trend_direction="stable",
            drought_risk_level="low",
            dry_day_frequency=35.6,
            runoff_potential=68.4,
            flood_susceptibility_contribution=52.3,
            water_availability_score=76.2,
            suitability_scores=SuitabilityScores(
                water_availability_score=76.2,
                agriculture_score=72.1,
                drainage_score=58.9,
                groundwater_recharge_score=68.5,
                infiltration_suitability_score=65.3,
            ),
            recommendations=[
                "Strong monsoon influence: plan for seasonal flooding and water abundance",
                "Water availability suitable for irrigation and water-dependent activities",
            ],
            datasets=["CHIRPS Daily (UCSB-CHG)"],
        )

    monkeypatch.setattr(rainfall_router.service, "get_site_analysis", _fake_site_analysis)

    resp = CLIENT.post(
        "/rainfall/site-analysis",
        json={"latitude": 19.07, "longitude": 72.87, "radius_meters": 5000},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["drought_risk_level"] == "low"
    assert body["trend_direction"] == "stable"
    assert len(body["recommendations"]) >= 2
    assert body["suitability_scores"]["agriculture_score"] == 72.1
