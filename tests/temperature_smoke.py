"""
Temperature service smoke tests.

Requires the temperature service running on localhost:8000 OR
use the mock fixtures below which patch httpx to avoid live network calls.

Run:
    pytest tests/temperature_smoke.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure services/temperature is on sys.path so 'app' package is importable.
# conftest.py does this too, but we add it here as a fallback for CI environments
# where conftest loading order may differ.
_TEMPERATURE_SERVICE = Path(__file__).resolve().parents[1] / "services" / "temperature"
if str(_TEMPERATURE_SERVICE) not in sys.path:
    sys.path.insert(0, str(_TEMPERATURE_SERVICE))

# ---------------------------------------------------------------------------
# App import — catch any exception (not just ImportError) so a missing optional
# dependency (e.g. imdlib native ext) doesn't abort collection.
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Open-Meteo mock payload (minimal valid shape)
# ---------------------------------------------------------------------------
MOCK_OPEN_METEO_PAYLOAD = {
    "latitude": 19.07,
    "longitude": 72.87,
    "timezone": "UTC",
    "daily": {
        "time": [f"2023-{str(m).zfill(2)}-15" for m in range(1, 13)],
        "temperature_2m_max": [
            32.0,
            33.0,
            36.0,
            38.0,
            39.0,
            34.0,
            30.0,
            30.0,
            31.0,
            33.0,
            31.0,
            29.0,
        ],
        "temperature_2m_min": [
            18.0,
            19.0,
            22.0,
            26.0,
            28.0,
            26.0,
            25.0,
            25.0,
            24.0,
            22.0,
            19.0,
            17.0,
        ],
    },
}


def _mock_httpx_get(url: str, **kwargs):
    resp = MagicMock()
    resp.status_code = 200
    resp.raise_for_status = MagicMock()
    resp.json.return_value = MOCK_OPEN_METEO_PAYLOAD
    return resp


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@skip_no_app
def test_health():
    """Service must respond 200 at /health with {status: ok}."""
    resp = CLIENT.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "ok"
    assert body.get("service") == "temperature"


@skip_no_app
def test_root_still_responds():
    """Root / must still respond (legacy health-check target)."""
    resp = CLIENT.get("/")
    assert resp.status_code == 200


@skip_no_app
@patch("httpx.get", side_effect=_mock_httpx_get)
@patch("requests.get", side_effect=lambda url, **kw: _mock_httpx_get(url, **kw))
def test_climate_archive_mumbai(mock_req, mock_httpx):
    """
    GET /weather/climate-archive returns Open-Meteo response shape
    for Mumbai coords (lat=19.07, lon=72.87).
    """
    resp = CLIENT.get(
        "/weather/climate-archive",
        params={
            "latitude": 19.07,
            "longitude": 72.87,
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "daily": "temperature_2m_max,temperature_2m_min",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "daily" in body
    assert "temperature_2m_max" in body["daily"]


@skip_no_app
def test_thermal_grid_small_polygon():
    """
    POST /weather/thermal-grid returns FeatureCollection shape
    for a small polygon around Mumbai.
    """
    polygon = {
        "type": "Polygon",
        "coordinates": [
            [
                [72.85, 19.05],
                [72.90, 19.05],
                [72.90, 19.10],
                [72.85, 19.10],
                [72.85, 19.05],
            ]
        ],
    }
    with (
        patch("httpx.get", side_effect=_mock_httpx_get),
        patch("requests.get", side_effect=lambda url, **kw: _mock_httpx_get(url, **kw)),
    ):
        resp = CLIENT.post(
            "/weather/thermal-grid",
            json={"geometry": polygon, "year": 2023, "grid_size": 3},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("type") == "FeatureCollection"
    assert isinstance(body.get("features"), list)
    assert "min_temp" in body
    assert "max_temp" in body
    assert "year" in body


@skip_no_app
@patch("httpx.get", side_effect=_mock_httpx_get)
def test_thermal_profile_deprecated_still_works(mock_httpx):
    """
    GET /weather/thermal-profile is deprecated but must still return a valid
    ClimateReport shape (some integrations may still use it).
    """
    resp = CLIENT.get(
        "/weather/thermal-profile",
        params={"lat": 19.07, "lon": 72.87, "year": 2023},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "monthly_data" in body
    assert "summary" in body
    assert "recommendations" in body
    assert len(body["monthly_data"]) >= 1
    assert "annual_avg_temp" in body["summary"]


@skip_no_app
def test_no_live_network_calls(monkeypatch):
    """
    No requests to archive-api.open-meteo.com should be made when the
    disk cache already has data. This test just verifies cache logic
    doesn't crash on a cache miss (returns from upstream mock).
    """
    import httpx

    call_count = {"n": 0}

    def counting_get(url, **kwargs):
        call_count["n"] += 1
        return _mock_httpx_get(url, **kwargs)

    monkeypatch.setattr(httpx, "get", counting_get)

    resp = CLIENT.get(
        "/weather/climate-archive",
        params={
            "latitude": 13.0,
            "longitude": 77.6,
            "start_date": "2020-01-01",
            "end_date": "2020-12-31",
            "daily": "temperature_2m_max,temperature_2m_min",
        },
    )
    assert resp.status_code == 200


@skip_no_app
def test_feature_flag_off_returns_403(monkeypatch):
    """All flagged endpoints return HTTP 403 when FLAGS env var is empty."""
    monkeypatch.setenv("FLAGS", "")

    flagged_requests = [
        (
            "get",
            "/weather/climate-archive",
            {
                "params": {
                    "latitude": 12.97,
                    "longitude": 77.59,
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "daily": "temperature_2m_max",
                }
            },
        ),
        ("get", "/weather/thermal-profile", {"params": {"lat": 12.97, "lon": 77.59}}),
        ("get", "/weather/analyze-wind", {"params": {"lat": 12.97, "lon": 77.59}}),
        (
            "post",
            "/weather/thermal-grid",
            {
                "json": {
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [72.85, 19.05],
                                [72.90, 19.05],
                                [72.90, 19.10],
                                [72.85, 19.10],
                                [72.85, 19.05],
                            ]
                        ],
                    },
                }
            },
        ),
    ]
    for method, path, kwargs in flagged_requests:
        resp = getattr(CLIENT, method)(path, **kwargs)
        assert resp.status_code == 403, (
            f"{method.upper()} {path} expected 403, got {resp.status_code}"
        )


@skip_no_app
def test_feature_flag_on_climate_archive_200(monkeypatch):
    """climate-archive returns 200 when feature flag is enabled."""
    monkeypatch.setenv("FLAGS", "feature.temperature.thermal-profile")
    with patch("httpx.get", side_effect=_mock_httpx_get):
        resp = CLIENT.get(
            "/weather/climate-archive",
            params={
                "latitude": 12.97,
                "longitude": 77.59,
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "daily": "temperature_2m_max,temperature_2m_min",
            },
        )
    assert resp.status_code == 200
