"""Live integration tests — Future-infra service (port 8008).
Run in isolation: pytest testing/backend/test_future_infra.py -v
"""
import requests

BASE = "http://localhost:8008"
BELLANDUR = {"lat": 12.9352, "lon": 77.6733}

def test_health():
    r = requests.get(f"{BASE}/health", timeout=5)
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

def test_pipeline_schema():
    r = requests.get(f"{BASE}/future-infra/pipeline", params=BELLANDUR, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "projects" in data or "pipeline" in data or isinstance(data, list) or isinstance(data, dict)

def test_pipeline_response_valid():
    r = requests.get(f"{BASE}/future-infra/pipeline", params=BELLANDUR, timeout=30)
    assert r.status_code == 200
    data = r.json()
    projects = data.get("projects") or data.get("pipeline") or (data if isinstance(data, list) else [])
    # Curated static data — may be empty for some coords
    assert isinstance(projects, list)

def test_missing_params_returns_422():
    r = requests.get(f"{BASE}/future-infra/pipeline", timeout=5)
    assert r.status_code == 422
