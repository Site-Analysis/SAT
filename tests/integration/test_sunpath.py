"""Live integration tests — Sunpath service (port 8001).
Run in isolation: pytest testing/backend/test_sunpath.py -v
"""
import pytest
import requests

BASE = "http://localhost:8001"
BELLANDUR = {"lat": 12.9352, "lon": 77.6733}

def test_health():
    r = requests.get(f"{BASE}/health", timeout=5)
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") in ("ok", "healthy")

def test_annual_schema():
    r = requests.get(f"{BASE}/sunpath/annual", params=BELLANDUR, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    for field in ("latitude", "longitude", "hourly_data"):
        assert field in data, f"missing field: {field}"
    assert len(data["hourly_data"]) > 0

def test_annual_elevation_domain():
    r = requests.get(f"{BASE}/sunpath/annual", params=BELLANDUR, timeout=30)
    assert r.status_code == 200
    hourly = r.json()["hourly_data"]
    elevations = [h["elevation"] for h in hourly if h.get("elevation") is not None]
    max_elev = max(elevations)
    assert 60 <= max_elev <= 90, f"peak solar elevation {max_elev}° implausible for Bengaluru (12°N)"

def test_annual_hour_field():
    r = requests.get(f"{BASE}/sunpath/annual", params=BELLANDUR, timeout=30)
    data = r.json()
    sample = data["hourly_data"][0]
    assert "hour" in sample or "local_hour" in sample or "timestamp" in sample

def test_summer_solstice():
    r = requests.get(f"{BASE}/sunpath/summer", params=BELLANDUR, timeout=30)
    assert r.status_code == 200, r.text

def test_winter_solstice():
    r = requests.get(f"{BASE}/sunpath/winter", params=BELLANDUR, timeout=30)
    assert r.status_code == 200, r.text

def test_diagram_svg():
    r = requests.get(f"{BASE}/sunpath/diagram.svg", params=BELLANDUR, timeout=30)
    if r.status_code == 403:
        pytest.skip("diagram flag not enabled")
    assert r.status_code == 200
    assert "svg" in r.headers.get("content-type", "").lower() or b"<svg" in r.content[:200]

def test_missing_params_returns_422():
    r = requests.get(f"{BASE}/sunpath/annual", timeout=5)
    assert r.status_code == 422

def test_orientation():
    r = requests.get(f"{BASE}/sunpath/orientation", params=BELLANDUR, timeout=30)
    if r.status_code == 404:
        pytest.skip("orientation endpoint not implemented")
    assert r.status_code == 200
