# Temperature Service — Agent Context

**Port:** 8000
**Contract:** `contracts/temperature.yaml`
**Feature flag:** `feature.temperature.thermal-profile`
**FVD:** `docs/feature-validation/SAT-09_annual-temperature-analysis.md`
**Jira:** SAT-9 (Done, 2026-03-26)

## Source location
`/Volumes/LocalDrive/Site Analysis/Site-Analysis-Tool/src/Backend/Temperature/`

## Architecture
- Primary data: IMD gridded (1° × 1°) — `data/imd_*.grd` files
- Fallback: Open-Meteo Archive API (`https://archive-api.open-meteo.com/v1/archive`)
- No external API keys required

## Endpoint
```
GET /weather/thermal-profile?lat={lat}&lon={lon}&year={year}
```
Returns monthly tmax/tmin, annual summary, material/insulation recommendations.

## Gotchas
- IMD data is large (~MB per year) — don't commit to git; mount via volume in docker-compose
- Open-Meteo fallback triggers when IMD file missing OR location outside India bounds
- CORS must allow `http://localhost:3000` for dev

## Migration checklist
- [ ] Copy `app/` directory
- [ ] Add `pyproject.toml` + `requirements.txt` (pin: fastapi, uvicorn, requests, xarray, netcdf4)
- [ ] Wire flag check: `require_flag(FeatureFlag.TEMPERATURE_THERMAL_PROFILE)` at endpoint
- [ ] Add `Dockerfile` with IMD data volume mount
- [ ] Add `tests/temperature_smoke.py` hitting `/health` + one valid coord
- [ ] Bump `contracts/CHANGELOG.md` if schema changes
