"""Live integration tests — Flood service (port 8002).
Run in isolation: pytest testing/backend/test_flood.py -v
"""
import requests

BASE = "http://localhost:8002"
BELLANDUR   = {"latitude": 12.9352, "longitude": 77.6733}
DEVANAHALLI = {"latitude": 13.2437, "longitude": 77.7117}

def test_health():
    r = requests.get(f"{BASE}/health", timeout=5)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

def test_analyze_schema():
    r = requests.post(f"{BASE}/flood/analyze", json=BELLANDUR, timeout=60)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "overall_score" in data, f"missing overall_score, got keys: {list(data.keys())}"
    assert "risk_category" in data

def test_overall_score_range():
    r = requests.post(f"{BASE}/flood/analyze", json=BELLANDUR, timeout=60)
    assert r.status_code == 200
    score = r.json()["overall_score"]
    assert 0.0 <= score <= 100.0, f"overall_score {score} out of [0,100]"

def test_bellandur_elevated_risk():
    """Bellandur is a historic flood zone — score should be non-trivial."""
    r = requests.post(f"{BASE}/flood/analyze", json=BELLANDUR, timeout=60)
    assert r.status_code == 200
    score = r.json()["overall_score"]
    assert score >= 20, f"Bellandur flood score {score} unexpectedly low"

def test_devanahalli_schema():
    r = requests.post(f"{BASE}/flood/analyze", json=DEVANAHALLI, timeout=60)
    assert r.status_code == 200
    assert "overall_score" in r.json()

def test_risk_category_valid():
    r = requests.post(f"{BASE}/flood/analyze", json=BELLANDUR, timeout=60)
    assert r.status_code == 200
    cat = r.json()["risk_category"]
    assert cat in ("Low", "Moderate", "High", "Very High", "low", "moderate", "high", "very_high")

def test_missing_body_returns_422():
    r = requests.post(f"{BASE}/flood/analyze", json={}, timeout=5)
    assert r.status_code == 422
