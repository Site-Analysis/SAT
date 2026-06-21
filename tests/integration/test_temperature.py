"""Live integration tests — Temperature service (port 8000).
Run in isolation: pytest testing/backend/test_temperature.py -v
"""
import pytest
import requests

BASE = "http://localhost:8000"
BELLANDUR = {"latitude": 12.9352, "longitude": 77.6733}
HEBBAL    = {"latitude": 13.0358, "longitude": 77.5946}
DAILY_VARS = "temperature_2m_mean,temperature_2m_max,temperature_2m_min,precipitation_sum"

def test_health():
    r = requests.get(f"{BASE}/health", timeout=5)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

def test_climate_archive_schema():
    params = {**BELLANDUR, "start_date": "2023-01-01", "end_date": "2023-12-31", "daily": DAILY_VARS}
    r = requests.get(f"{BASE}/weather/climate-archive", params=params, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "daily" in data or "latitude" in data

def test_climate_archive_returns_data():
    params = {**BELLANDUR, "start_date": "2023-06-01", "end_date": "2023-06-30", "daily": "temperature_2m_mean"}
    r = requests.get(f"{BASE}/weather/climate-archive", params=params, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    daily = data.get("daily") or {}
    temps = daily.get("temperature_2m_mean") or []
    if temps:
        for t in temps:
            if t is not None:
                assert 15 <= t <= 40, f"temperature {t}°C out of plausible range"

def test_climate_archive_hebbal():
    params = {**HEBBAL, "start_date": "2023-06-01", "end_date": "2023-06-30", "daily": "temperature_2m_mean"}
    r = requests.get(f"{BASE}/weather/climate-archive", params=params, timeout=30)
    assert r.status_code == 200

def test_missing_daily_returns_422():
    params = {**BELLANDUR, "start_date": "2023-01-01", "end_date": "2023-12-31"}
    r = requests.get(f"{BASE}/weather/climate-archive", params=params, timeout=5)
    assert r.status_code == 422

def test_missing_coords_returns_422():
    r = requests.get(f"{BASE}/weather/climate-archive", timeout=5)
    assert r.status_code == 422

def test_thermal_grid_schema():
    # GeoJSON Polygon ~500m box around Bellandur
    payload = {
        "latitude": 12.9352, "longitude": 77.6733,
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [77.6683, 12.9302], [77.6783, 12.9302],
                [77.6783, 12.9402], [77.6683, 12.9402],
                [77.6683, 12.9302],
            ]]
        }
    }
    r = requests.post(f"{BASE}/weather/thermal-grid", json=payload, timeout=60)
    if r.status_code == 403:
        pytest.skip("thermal-grid flag not enabled")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "type" in data or "features" in data or "grid" in data
