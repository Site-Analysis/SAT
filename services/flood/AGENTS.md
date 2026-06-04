# Flood Service — Agent Context

**Port:** 8002
**Contract:** `contracts/flood.yaml`
**Feature flag:** `feature.flood.risk-analysis`
**FVD:** `docs/feature-validation/SAT-07_flood-risk-analysis.md`

## Source location
`/Volumes/LocalDrive/Site Analysis/Site-Analysis-Tool/src/Backend/FloodPlains/`
Also: `Site-Analysis/SiteAnalysis_GEE/app/gee_utils.py` (canonical GEE flood scoring)

## Architecture
- Deterministic fallback scoring (no external calls)
- GEE integration TODO: MERIT Hydro + ALOS DEM + JRC Global Surface Water + CHIRPS + MODIS
- Returns risk score (0–100) + placeholder visualization URLs

## Endpoint
```
POST /flood/analyze
  body: {latitude, longitude, radius_meters}
```

## Gotchas
- Feature flag is required for /flood/analyze
- GEE auth (future): service account JSON via `GEE_SA_KEY_PATH`

## Migration checklist
- [ ] Copy `app/` directory
- [ ] requirements: earthengine-api, geemap, fastapi, uvicorn, pydantic
- [ ] Wire flag check
- [ ] Dockerfile mounts `gee-sa.json` at `/app/gee-sa.json`
- [ ] Smoke test with mocked ee.Initialize (don't hit real GEE in CI)
