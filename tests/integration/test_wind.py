"""Live integration tests — Wind service (port 8003).
Run in isolation: pytest testing/backend/test_wind.py -v
"""
import requests

BASE = "http://localhost:8003"
BELLANDUR = {"latitude": 12.9352, "longitude": 77.6733}
WHITEFIELD = {"latitude": 12.9698, "longitude": 77.7500}

def test_health():
    r = requests.get(f"{BASE}/health", timeout=5)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

def test_analyze_schema():
    r = requests.post(f"{BASE}/wind/analyze", json=BELLANDUR, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data) > 0

def test_wind_speed_domain():
    r = requests.post(f"{BASE}/wind/analyze", json=BELLANDUR, timeout=30)
    assert r.status_code == 200
    data = r.json()
    speed = (
        data.get("mean_wind_speed")
        or data.get("annual_mean_speed")
        or data.get("wind_speed_mean")
    )
    if speed is not None:
        assert 0.5 <= speed <= 15, f"annual mean wind speed {speed} m/s implausible"

def test_whitefield():
    r = requests.post(f"{BASE}/wind/analyze", json=WHITEFIELD, timeout=30)
    assert r.status_code == 200

def test_missing_body_returns_422():
    r = requests.post(f"{BASE}/wind/analyze", json={}, timeout=5)
    assert r.status_code == 422
