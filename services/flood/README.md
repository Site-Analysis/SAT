# Flood Service

4-component flood risk scoring — MERIT DEM elevation, flow accumulation, JRC water proximity, MODIS LULC imperviousness. Color-coded risk tiers + setback recommendations.

## Status
Backend complete. Source at `Site-Analysis-Tool/src/Backend/FloodPlains/` and `SiteAnalysis_GEE` commit `edd4c29`.

## Port
8002

## Contract
`contracts/flood.yaml` — `POST /flood/analyze`

## Feature flag
`feature.flood.risk-analysis`

## Run (current source)
```bash
cd Site-Analysis-Tool/src/Backend/FloodPlains
source venv/bin/activate
uvicorn app.main:app --reload --port 8002
```

## Integration checklist
- [ ] Copy `Site-Analysis-Tool/src/Backend/FloodPlains/app/` → `services/flood/app/`
- [ ] Add `pyproject.toml` + `requirements.txt`
- [ ] Wire feature flag via `packages/flags/src/flags.py`
- [ ] Add `Dockerfile`
- [ ] Add service block to root `docker-compose.yml`
- [ ] Add smoke test to `tests/flood_smoke.py`
- [ ] Update `contracts/CHANGELOG.md` if API shape changes
