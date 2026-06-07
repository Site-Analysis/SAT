# Flood Service — Agent Context

**Port:** 8002
**Contract:** `contracts/flood.yaml`
**Feature flag:** `feature.flood.risk-analysis`
**FVD:** `docs/feature-validation/SAT-04_flood-risk-analysis.md`

## Source location
`/Volumes/LocalDrive/Site Analysis/Site-Analysis-Tool/src/Backend/FloodPlains/`
Also: `Site-Analysis/SiteAnalysis_GEE/app/gee_utils.py` (canonical GEE flood scoring)

## Architecture
- Google Earth Engine — MERIT Hydro + ALOS DEM + JRC Global Surface Water
- Composite flood risk score: low-lying area index (LLAI) + slope + proximity to water
- Returns risk score (0–100) + GeoTIFF visualization URL

## Endpoint
```
POST /flood/analyze
  body: {lat, lon, radius_meters}
GET  /flood/visualize?lat&lon  # returns tile URL
```

## Gotchas
- GEE auth: needs `gee-sa.json` service account JSON. Path from `GEE_SA_KEY_PATH` env var
- Earth Engine init must happen at app startup: `ee.Initialize(credentials)`
- GEE rate limits: cache visualizations by lat/lon for 1 hour
- CORS for `http://localhost:3000`

## Migration checklist
- [ ] Copy `app/` directory
- [ ] requirements: earthengine-api, geemap, fastapi, uvicorn, pydantic
- [ ] Wire flag check
- [ ] Dockerfile mounts `gee-sa.json` at `/app/gee-sa.json`
- [ ] Smoke test with mocked ee.Initialize (don't hit real GEE in CI)
