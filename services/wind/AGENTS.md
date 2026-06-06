# Wind Service — Agent Context

**Port:** 8003
**Contract:** `contracts/wind.yaml`
**Feature flag:** `feature.wind.analysis`
**FVD:** `docs/feature-validation/SAT-09_wind-analysis.md`

## Architecture

- Historical wind speed and direction analysis for point + polygon summary stats
- Deterministic synthetic wind generator (deterministic fallback)
- TODO: Replace with ERA5-Land or GEE wind climatology integration
- Seasonal breakdown (summer/monsoon/winter for Indian context)
- Comfort and building impact analysis

## Endpoints

```
POST /wind/analyze
  body: {latitude, longitude, radius_meters}
GET  /health
```

## Gotchas

- Feature flag is required for /wind/analyze
- All endpoints must enforce feature flag gating
- Wind direction uses 8-point compass (N, NE, E, SE, S, SW, W, NW)
- Seasonal analysis is for Indian climatic context (summer/monsoon/winter)
