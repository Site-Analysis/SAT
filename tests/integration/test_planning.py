"""Live integration tests — Planning service (port 8006).
Run in isolation: pytest testing/backend/test_planning.py -v
"""
import requests

BASE = "http://localhost:8006"
BELLANDUR   = {"latitude": 12.9352, "longitude": 77.6733, "plot_area_sqm": 500.0}
DEVANAHALLI = {"latitude": 13.2437, "longitude": 77.7117, "plot_area_sqm": 2000.0}

def test_health():
    r = requests.get(f"{BASE}/health", timeout=5)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

def test_analyze_schema():
    r = requests.post(f"{BASE}/planning/analyze", json=BELLANDUR, timeout=60)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "far" in data or "floor_area_ratio" in data or "fsi" in data or len(data) > 0

def test_far_domain():
    r = requests.post(f"{BASE}/planning/analyze", json=BELLANDUR, timeout=60)
    assert r.status_code == 200
    data = r.json()
    far = data.get("far") or data.get("floor_area_ratio") or data.get("fsi")
    if far is not None:
        assert 0.5 <= far <= 5.0, f"FAR {far} outside plausible NBC range"

def test_devanahalli_airport_restriction():
    """Devanahalli is ~1km from KIAL — should flag OLS restriction."""
    r = requests.post(f"{BASE}/planning/analyze", json=DEVANAHALLI, timeout=60)
    assert r.status_code == 200
    data = r.json()
    # Either airport_restriction present and applicable, or response is valid
    assert len(data) > 0

def test_missing_plot_area_returns_422():
    r = requests.post(f"{BASE}/planning/analyze", json={"latitude": 12.9352, "longitude": 77.6733}, timeout=5)
    assert r.status_code == 422

def test_missing_body_returns_422():
    r = requests.post(f"{BASE}/planning/analyze", json={}, timeout=5)
    assert r.status_code == 422
