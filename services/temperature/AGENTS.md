# Temperature Service — Agent Context

**Port:** 8000
**Contract:** `contracts/temperature.yaml`
**Feature flag:** `feature.temperature.thermal-profile`

## Source location
`/Volumes/LocalDrive/SiteAnalysisToolV3/backend/Temperature/`

## Data source
**Primary:** Open-Meteo Archive API (ERA5 reanalysis, `https://archive-api.open-meteo.com/v1/archive`)
**Enhancement-Later:** IMD imdlib — requires `.grd` data files not in repository; adapter needs rewrite before use.

## Live endpoints (frontend uses these)
```
GET  /weather/climate-archive   — disk-cached proxy → Open-Meteo (main panel data)
POST /weather/thermal-grid      — spatial temperature heatmap for polygon ROI
GET  /weather/analyze-wind      — ERA5 5-year wind rose data (disk-cached)
GET  /health                    — service health check
```

## Deprecated endpoint (zero frontend call sites)
```
GET  /weather/thermal-profile   — dead code; no component calls this
```

## Architecture note
`TemperatureAnalysisPanel` → `fetchClimateAnalysis()` → `/weather/climate-archive` → Open-Meteo  
`TemperatureResultView` → `getThermalGrid()` → `/weather/thermal-grid`  
`temperatureApi.getThermalProfile()` → **never called** — zero callers in codebase.

## CORS
Set `CORS_ORIGINS=http://localhost:5173` (Vite dev port) in env. Do NOT use `:3000`.

## Gotchas
- Open-Meteo responses cached to `_climate_cache/` on disk — survives server restarts
- IMD `.grd` files would live in `data/` — mount as Docker volume; never commit to git
- Estimated fallback profile triggers when both IMD and Open-Meteo fail — returns valid `ClimateReport` with status suffixed `/ Estimated`

## Migration checklist
- [x] Contract updated to reflect live endpoints (v1.1.0)
- [x] Copy `SiteAnalysisToolV3/backend/Temperature/app/` → `services/temperature/app/`
- [x] Add `GET /health` endpoint returning `{"status": "ok", "service": "temperature"}`
- [x] Pin `requirements.txt` to exact versions
- [x] Wire flag check: `_require_flag()` at all 4 endpoints in `app/routers/weather.py` — reads `FLAGS` env var directly (packages/flags outside Docker build context)
- [x] Add `Dockerfile` (Python 3.11-slim, `data/` volume mount)
- [x] Add service block to root `docker-compose.yml` (already present; healthcheck updated to `/health`)
- [ ] Add `tests/temperature_smoke.py` covering `/health`, `climate-archive`, `thermal-grid`
- [ ] Add `tests/temperature_imd_validation.py` (marked xfail — documents Enhancement-Later)
