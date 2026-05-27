# Wind Service — Agent Context

**Port:** 8003
**Contract:** `contracts/wind.yaml`
**Feature flag:** `feature.wind.climatology`
**FVD:** `docs/feature-validation/SAT-04_wind-climatology.md` (verify path)

## Source location
Multiple candidates — check git log:
- `Vishwas721/sat` repo (rewrite reference from FVD-09)
- Open-Meteo Wind Climatology endpoint

## Architecture
- Open-Meteo Wind API (free, no key)
- Returns wind speed/direction frequency rose, monthly averages
- Optional: NBC compliance flags for site wind loads

## Endpoint
```
GET /wind/climatology?lat={lat}&lon={lon}&years={N}
```

## Gotchas
- Open-Meteo rate limit: 10,000 req/day free tier — cache responses by lat/lon (rounded to 0.1°)
- Wind direction convention: meteorological (FROM) not vector (TO) — confirm in contract
- NBC compliance is India-specific; only run if location in India bounds

## Migration checklist
- [ ] Identify canonical source (FVD-09 has clues)
- [ ] requirements: requests, fastapi, uvicorn, pandas, numpy
- [ ] Wire flag check
- [ ] Smoke test with mocked Open-Meteo response
