# SunPath Service — Agent Notes

**Port:** 8001 · **Flag:** `feature.sunpath.diagram` · **Contract:** `contracts/sunpath.yaml` (v1.1.0)
**Jira:** SAT-226 (migration) · **Source:** `Site-Analysis-Tool/src/Backend/SunPath/` (superset; NOT V3)

## Endpoints (root-mounted, no /api/v1 prefix)
- `GET /health`, `/health/ready`, `/health/live` — **ungated**
- `GET /sunpath/{summer,winter,annual,events}?lat&lon` — solar position JSON
- `GET /sunpath/diagram.svg?lat&lon&date?` — Andrew Marsh polar diagram (SVG)
- `GET /sunpath/orientation?lat&lon` — facade + overhang recommendation
- `POST /shadow/calculate/{bbox,radius,polygon,address}` — building shadows
- `POST /shadow/timeseries/{bbox,radius,polygon}` — shadow over time
- `GET /shadow/sunlight-hours?lat&lon&date&radius_meters` — sunshine-hours grid
- `POST /buildings/*` — OSM/GEE building extraction

All non-health routes enforce the flag (403 when off) via `app/core/flags.py` (reads `FLAGS` env directly — `packages/flags` is outside the Docker build context).

## Migration fixes (do not regress — covered by smoke tests)
- **tz arg order:** `solar_engine.detect_timezone` → `tzfpy.get_tz(longitude, latitude)`. Wrong order sent Bangalore to `Arctic/Longyearbyen`.
- **hour source:** `/sunpath/*` derives `hour` from the tz-aware UTC `timestamp` converted via `zoneinfo`, NOT the unparseable `local_time` abbrev string.
- **pandas 3:** `freq='h'` (not `'H'`); never `pd.Timestamp(local_time_with_IST)`.

## Run
```bash
cd services/sunpath && pip install -r requirements.txt
MPLBACKEND=Agg FLAGS=feature.sunpath.diagram uvicorn app.main:app --port 8001
```

## Notes
- GEE optional — building/shadow-via-GEE degrades gracefully if init fails; `/health` stays 200.
- `app/services/sunlight_hours.py` adapts pybdshadow (BSD-3) — see `THIRD_PARTY_LICENSES.md`.
- Celery `workers/` from source intentionally **dropped** (placeholders).
- Smoke tests: `tests/sunpath_smoke.py`. CI smoke installs only `pytest httpx` → app-import tests skip there unless service requirements are installed.
