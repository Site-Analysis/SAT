"""Live integration tests — Rainfall service (port 8004).
Run in isolation: pytest testing/backend/test_rainfall.py -v
"""
import requests

BASE = "http://localhost:8004"
BELLANDUR = {"latitude": 12.9352, "longitude": 77.6733, "start_date": "2023-01-01", "end_date": "2023-12-31"}

def test_health():
    r = requests.get(f"{BASE}/health", timeout=5)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

def test_archive_schema():
    r = requests.get(f"{BASE}/rainfall/archive", params=BELLANDUR, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, dict) and len(data) > 0

def test_annual_total_domain():
    r = requests.get(f"{BASE}/rainfall/archive", params=BELLANDUR, timeout=30)
    assert r.status_code == 200
    data = r.json()
    total = data.get("annual_total_mm") or data.get("total_mm") or data.get("annual_rainfall_mm")
    if total is not None:
        assert 400 <= total <= 1600, f"annual rainfall {total} mm implausible for Bengaluru"

def test_monthly_breakdown():
    r = requests.get(f"{BASE}/rainfall/archive", params=BELLANDUR, timeout=30)
    data = r.json()
    monthly = data.get("monthly") or data.get("monthly_data")
    if monthly:
        assert len(monthly) == 12, "expected 12 monthly buckets"

def test_missing_dates_returns_422():
    r = requests.get(f"{BASE}/rainfall/archive", params={"latitude": 12.9352, "longitude": 77.6733}, timeout=5)
    assert r.status_code == 422

def test_missing_coords_returns_422():
    r = requests.get(f"{BASE}/rainfall/archive", timeout=5)
    assert r.status_code == 422
