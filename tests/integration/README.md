# Live integration tests (Stage B)

Ported from SAT-Fallback (`testing/backend/`, commit `ed0a35a` + Overpass mirror fix
`3627633`). These are **live HTTP integration tests**: each file hits a *running* service
over `http://localhost:<port>` with `requests`, unlike the in-process `tests/*_smoke.py`
suite (FastAPI `TestClient`, no network).

They are **not part of the CI smoke gate.** CI runs `for f in tests/*_smoke.py` — a top-level
glob that does not descend into this directory. Run these manually against a live stack.

## What they cover

62 tests across 10 services (health, response schema, domain-plausibility ranges, dual-site
comparison). Per-service breakdown, mirror configuration, and the corrections found while
authoring them are in `docs/testing/matrix.md`. Results, latency baseline, and the concurrency
probe are in `docs/testing/results.md`. Site coordinates and plausibility ranges are in
`docs/testing/scenarios.md`.

| File | Service | Port |
|---|---|---|
| `test_temperature.py` | temperature | 8000 |
| `test_sunpath.py` | sunpath | 8001 |
| `test_flood.py` | flood | 8002 |
| `test_wind.py` | wind | 8003 |
| `test_rainfall.py` | rainfall | 8004 |
| `test_geo.py` | geo | 8005 |
| `test_planning.py` | planning | 8006 |
| `test_infrastructure.py` | infrastructure | 8007 |
| `test_future_infra.py` | future-infra | 8008 |
| `test_land_records.py` | land-records | 8009 |

## Running

The stack must be up first (services read `FLAGS` from the environment — set the full flag
string so gated endpoints return 200, not 403):

```bash
# 1. bring up the full stack (see infra/DEPLOY.md)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 2. install the client dep and run (one file at a time, or the whole dir)
pip install pytest requests
pytest tests/integration/ -v
```

Last recorded full run (SAT-Fallback, 2026-06-19, Overpass mirror restored): **62 collected ·
62 passed · 0 failed · 0 skipped**, ~113 s wall-clock. The earlier 2026-06-18 run was 54/62
(8 Overpass tests skipped under public rate-limiting); switching to a working Overpass mirror
resolved all skips. See `docs/testing/results.md`.

## Note on the SAT in-process smoke suite

For the fast, network-free gate used by CI and local pre-merge checks, see
`docs/testing/TEST-INVENTORY.md` (covers `tests/*_smoke.py`).
