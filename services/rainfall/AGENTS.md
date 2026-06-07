# Rainfall Service — Agent Context

**Port:** 8004
**Contract:** `contracts/rainfall.yaml`
**Feature flags:**
- `feature.rainfall.archive`
- `feature.rainfall.summary`
**FVD:** `docs/feature-validation/SAT-18_rainfall-analysis.md`

## Source location
Unknown in this repo. FVD references `Site-Analysis/SiteAnalysisToolV3` `backend/Rainfall/`.

## Architecture
- Historical rainfall archive for point + polygon summary stats
- Deterministic synthetic rainfall generator (deterministic fallback)
- TODO: Replace with Open-Meteo API calls for real historical data

## Endpoints
```
GET  /rainfall/archive
POST /rainfall/summary
GET  /health
```

## Gotchas
- All non-health endpoints must enforce feature flags
- Do not call external APIs in tests
- Keep response shapes aligned with contracts/rainfall.yaml
