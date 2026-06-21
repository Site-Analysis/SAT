"""Live integration tests — Land records service (port 8009).
Run in isolation: pytest testing/backend/test_land_records.py -v

Land records uses Karnataka admin hierarchy (not lat/lon):
POST /land-records/lookup { district, taluk, hobli, village, survey_number }
"""
import requests

BASE = "http://localhost:8009"

SAMPLE_REQUEST = {
    "district": "Bengaluru Urban",
    "taluk": "Bengaluru South",
    "hobli": "Begur",
    "village": "Bellandur",
    "survey_number": "100",
    "state": "Karnataka",
}

def test_health():
    r = requests.get(f"{BASE}/health", timeout=5)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

def test_lookup_schema():
    r = requests.post(f"{BASE}/land-records/lookup", json=SAMPLE_REQUEST, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, dict)
    assert "bhoomi" in data or "deep_links" in data or "score" in data

def test_lookup_has_deep_links():
    r = requests.post(f"{BASE}/land-records/lookup", json=SAMPLE_REQUEST, timeout=30)
    assert r.status_code == 200
    data = r.json()
    links = data.get("deep_links") or []
    assert isinstance(links, list)

def test_score_range():
    r = requests.post(f"{BASE}/land-records/lookup", json=SAMPLE_REQUEST, timeout=30)
    assert r.status_code == 200
    score = r.json().get("score")
    if score is not None:
        assert 0 <= score <= 100, f"score {score} out of [0, 100]"

def test_missing_body_returns_422():
    r = requests.post(f"{BASE}/land-records/lookup", json={}, timeout=5)
    assert r.status_code == 422

def test_missing_survey_number_returns_422():
    body = {k: v for k, v in SAMPLE_REQUEST.items() if k != "survey_number"}
    r = requests.post(f"{BASE}/land-records/lookup", json=body, timeout=5)
    assert r.status_code == 422
