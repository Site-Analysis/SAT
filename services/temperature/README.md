# Temperature Service

Annual thermal profile — IMD gridded data (primary) → Open-Meteo fallback. Monthly tmax/tmin, annual summary, material + insulation recommendations.

## Status
Backend complete. Source at `Site-Analysis-Tool/src/Backend/Temperature/` — Jira SAT-9, resolved 2026-03-26.

## Port
8000

## Contract
`contracts/temperature.yaml` — `GET /weather/thermal-profile?lat&lon&year`

## Feature flag
`feature.temperature.thermal-profile`

## Run (current source)
```bash
cd Site-Analysis-Tool/src/Backend/Temperature
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

## Integration checklist
- [ ] Copy `Site-Analysis-Tool/src/Backend/Temperature/app/` → `services/temperature/app/`
- [ ] Add `pyproject.toml` + `requirements.txt`
- [ ] Wire feature flag via `packages/flags/src/flags.py`
- [ ] Add `Dockerfile`
- [ ] Add service block to root `docker-compose.yml`
- [ ] Add smoke test to `tests/temperature_smoke.py`
- [ ] Update `contracts/CHANGELOG.md` if API shape changes
