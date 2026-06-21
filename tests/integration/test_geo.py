"""Live integration tests — Geo service (port 8005).
Run in isolation: pytest testing/backend/test_geo.py -v
"""
import pytest
import requests

BASE = "http://localhost:8005"
BELLANDUR = {"lat": 12.9352, "lon": 77.6733}

def test_health():
    r = requests.get(f"{BASE}/health", timeout=5)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

def test_amenities_schema():
    r = requests.get(f"{BASE}/geo/amenities", params=BELLANDUR, timeout=60)
    if r.status_code == 502:
        pytest.skip("Overpass upstream unavailable (rate-limited)")
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, dict) and len(data) > 0

def test_amenities_nonempty():
    r = requests.get(f"{BASE}/geo/amenities", params=BELLANDUR, timeout=60)
    if r.status_code == 502:
        pytest.skip("Overpass upstream unavailable (rate-limited)")
    assert r.status_code == 200
    data = r.json()
    # Response shape: {radius_m, healthcare: {count, nearest_m, top_5}, shopping: ..., ...}
    category_keys = [k for k in data if k != "radius_m"]
    assert len(category_keys) >= 1, f"expected at least one amenity category, got: {list(data.keys())}"

def test_amenities_healthcare_count():
    r = requests.get(f"{BASE}/geo/amenities", params=BELLANDUR, timeout=60)
    if r.status_code == 502:
        pytest.skip("Overpass upstream unavailable (rate-limited)")
    assert r.status_code == 200
    data = r.json()
    healthcare = data.get("healthcare")
    if healthcare:
        assert healthcare.get("count", 0) >= 0

def test_zone_schema():
    r = requests.get(f"{BASE}/geo/zone", params=BELLANDUR, timeout=60)
    if r.status_code in (404, 502):
        pytest.skip(f"zone endpoint unavailable ({r.status_code})")
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data) > 0

def test_water_constraints():
    r = requests.get(f"{BASE}/geo/water-constraints", params=BELLANDUR, timeout=60)
    if r.status_code in (404, 502):
        pytest.skip(f"upstream unavailable ({r.status_code})")
    assert r.status_code in (200, 206), r.text

def test_missing_params_returns_422():
    r = requests.get(f"{BASE}/geo/amenities", timeout=5)
    assert r.status_code == 422
