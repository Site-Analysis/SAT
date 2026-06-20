"""
Land-records service smoke tests.

Run:
    pytest tests/land_records_smoke.py -v

The service performs no network I/O (portal-only: empty placeholders + deterministic
deep links), so the flag-on path exercises the real service.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure services/land-records is on sys.path so 'app' package is importable.
_LR_SERVICE = Path(__file__).resolve().parents[1] / "services" / "land-records"
_LR_PATH = str(_LR_SERVICE)
if _LR_PATH in sys.path:
    sys.path.remove(_LR_PATH)
sys.path.insert(0, _LR_PATH)

# Ensure we import the land-records app, not another service's app.
sys.modules.pop("app", None)
sys.modules.pop("app.main", None)

APP_AVAILABLE = False
CLIENT = None  # type: ignore[assignment]
_APP_IMPORT_ERROR: str = ""

try:
    from app.main import app  # noqa: E402
    from fastapi.testclient import TestClient

    CLIENT = TestClient(app)
    APP_AVAILABLE = True
except Exception as _exc:  # noqa: BLE001
    _APP_IMPORT_ERROR = f"{type(_exc).__name__}: {_exc}"


skip_no_app = pytest.mark.skipif(
    not APP_AVAILABLE, reason=f"app/ not importable: {_APP_IMPORT_ERROR}"
)

_REQ = {
    "district": "Bengaluru Urban",
    "taluk": "Bengaluru North",
    "hobli": "Jala",
    "village": "Yelahanka",
    "survey_number": "123/4",
}


@skip_no_app
def test_health():
    resp = CLIENT.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "ok"
    assert body.get("service") == "land-records"


@skip_no_app
def test_lookup_flag_off(monkeypatch):
    monkeypatch.setenv("FLAGS", "")
    resp = CLIENT.post("/land-records/lookup", json=_REQ)
    assert resp.status_code == 403


@skip_no_app
def test_lookup_flag_on(monkeypatch):
    monkeypatch.setenv("FLAGS", "feature.land.records")
    resp = CLIENT.post("/land-records/lookup", json=_REQ)
    assert resp.status_code == 200
    body = resp.json()
    # Portal-only: no scraped data, deterministic deep links present.
    assert body["bhoomi"]["raw_data_available"] is False
    assert body["severity"] == "none"
    assert len(body["deep_links"]) >= 3
    labels = {dl["label"] for dl in body["deep_links"]}
    assert any("Bhoomi" in label for label in labels)
