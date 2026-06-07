# SunPath Service

Solar position & sun path diagrams (pvlib NREL SPA), Andrew Marsh-style polar SVG,
building shadow analysis, orientation recommendations, and a sunshine-hours grid.

**Port:** 8001 · **Flag:** `feature.sunpath.diagram` · **Contract:** `contracts/sunpath.yaml` (v1.1.0)
**Jira:** SAT-226 · migrated from `Site-Analysis-Tool/src/Backend/SunPath/`.

## Run
```bash
cd services/sunpath
pip install -r requirements.txt
MPLBACKEND=Agg FLAGS=feature.sunpath.diagram uvicorn app.main:app --port 8001
# or from repo root:
docker-compose up sunpath
```

## Endpoints
See `AGENTS.md` for the full list. Health is at `GET /health` (ungated); all
sun-path / shadow / building routes require the feature flag (403 when off).

```bash
curl "localhost:8001/sunpath/summer?lat=12.9716&lon=77.5946"
curl "localhost:8001/sunpath/diagram.svg?lat=12.97&lon=77.59" -o sunpath.svg
curl "localhost:8001/sunpath/orientation?lat=12.97&lon=77.59"
curl "localhost:8001/shadow/sunlight-hours?lat=12.97&lon=77.59&date=2025-06-21"
```

## Notes
- pvlib NREL SPA solar angles (±0.0003°); hours are tz-localized from the site's IANA zone.
- GEE is optional — building extraction degrades gracefully if unavailable.
- `sunlight_hours.py` adapts pybdshadow (BSD-3) — see `THIRD_PARTY_LICENSES.md`.
- Tests: `tests/sunpath_smoke.py` (from repo root: `pytest tests/sunpath_smoke.py -v`).
