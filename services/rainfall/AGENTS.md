# Rainfall Service — Agent Context

**Port:** 8004
**Contract:** `contracts/rainfall.yaml`
**Feature flags:**
- `feature.rainfall.archive`
- `feature.rainfall.summary`
**FVD:** `docs/feature-validation/SAT-18_rainfall-analysis.md`

## Architecture
- Primary: CHIRPS Daily rainfall data via Google Earth Engine (UCSB-CHG/CHIRPS/DAILY)
- Fallback: Deterministic synthetic rainfall generator (if GEE unavailable)
- Point queries: reduceRegion at point geometry
- Polygon queries: reduceRegion over polygon centroid
- Summary stats: total, mean, max daily, rainy days, dry days

## GEE Credentials

Requires environment variables:
- `GEE_PROJECT_ID`: GEE project ID
- `GEE_SERVICE_ACCOUNT_EMAIL`: service account email
- `GEE_SERVICE_ACCOUNT_KEY_PATH` or `GEE_SA_KEY_PATH`: path to service account JSON key

If credentials missing, falls back to synthetic fallback.

## Testing

All tests use mocked service methods; no live GEE calls in CI.
