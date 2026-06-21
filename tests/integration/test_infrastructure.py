"""Live integration tests — Infrastructure service (port 8007).
Run in isolation: pytest testing/backend/test_infrastructure.py -v

NOTE: test_analyze_* may return 502 if Overpass API is rate-limiting or down.
      This is an upstream dependency issue, not a service bug.
"""
import pytest
import requests

BASE = "http://localhost:8007"
BELLANDUR   = {"latitude": 12.9352, "longitude": 77.6733}
DEVANAHALLI = {"latitude": 13.2437, "longitude": 77.7117}

def test_health():
    r = requests.get(f"{BASE}/health", timeout=5)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

def test_analyze_schema():
    r = requests.post(f"{BASE}/infrastructure/analyze", json=BELLANDUR, timeout=90)
    if r.status_code == 502:
        pytest.skip("Overpass upstream unavailable (rate-limited or down)")
    assert r.status_code == 200, r.text
    data = r.json()
    assert "connectivity_score" in data or "score" in data or "road_access" in data

def test_connectivity_score_range():
    r = requests.post(f"{BASE}/infrastructure/analyze", json=BELLANDUR, timeout=90)
    if r.status_code == 502:
        pytest.skip("Overpass upstream unavailable")
    assert r.status_code == 200
    data = r.json()
    score = data.get("connectivity_score") or data.get("score")
    if score is not None:
        assert 0 <= score <= 100, f"connectivity score {score} out of [0,100]"

def test_second_site_schema():
    """Devanahalli (near KIAL) has major highway access — scores independently of Bellandur."""
    r = requests.post(f"{BASE}/infrastructure/analyze", json=DEVANAHALLI, timeout=90)
    if r.status_code == 502:
        pytest.skip("Overpass upstream unavailable")
    assert r.status_code == 200, r.text
    data = r.json()
    score = data.get("connectivity_score") or data.get("score")
    if score is not None:
        assert 0 <= score <= 100, f"score {score} out of range"

def test_missing_body_returns_422():
    r = requests.post(f"{BASE}/infrastructure/analyze", json={}, timeout=5)
    assert r.status_code == 422
