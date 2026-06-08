# Rainfall Service — Agent Context

**Port:** 8004
**Contract:** `contracts/rainfall.yaml` (v2.0.0)
**Feature flags:**
- `feature.rainfall.archive` — historical daily data
- `feature.rainfall.summary` — period summaries
- `feature.rainfall.climate-profile` — 30-year climate analysis
- `feature.rainfall.anomaly` — anomaly detection
- `feature.rainfall.seasonality` — seasonal patterns
- `feature.rainfall.site-analysis` — SAT-specific comprehensive analysis
**FVD:** `docs/feature-validation/SAT-18_rainfall-analysis.md`

## Architecture

### Data Pipeline
1. **Primary source:** CHIRPS Daily (UCSB-CHG/CHIRPS/DAILY) via Google Earth Engine
2. **Query strategy:**
   - Point queries: `ee.Geometry.Point([lon, lat])` → reduceRegion at scale 5000
   - Polygon queries: centroid calculation from GeoJSON
   - Date range filtering: `.filterDate(start_iso, end_iso)`
3. **Fallback:** Deterministic synthetic rainfall (testing only; production requires live GEE)

### Service Layer (rainfall_service.py)

**Public methods:**
- `get_archive(lat, lon, start_date, end_date)` → RainfallArchiveResponse (daily series)
- `get_summary(request)` → RainfallSummaryResponse (aggregates)
- `get_climate_profile(lat, lon)` → ClimateProfileResponse (30-year analysis)
- `get_anomaly(lat, lon, days)` → AnomalyResponse (vs 10-year average)
- `get_seasonality(lat, lon)` → SeasonalityResponse (seasonal breakdown)
- `get_site_analysis(lat, lon, radius_m)` → SiteAnalysisResponse (comprehensive SAT analysis)

**Private analytics methods:**
- `_aggregate_to_monthly()` — aggregates daily to monthly
- `_aggregate_to_seasonal()` — aggregates to summer/monsoon/winter/spring (Northern Hemisphere)
- `_calculate_concentration_index()` — seasonality index (0=uniform, 1=extreme)
- `_calculate_trend_percent_per_year()` — linear regression trend
- `_classify_climate()` — Köppen-Geiger classification
- `_assess_drought_risk()` — drought severity (very_low to very_high)
- `_calculate_runoff_potential()` — runoff score (0–100)
- `_calculate_flood_susceptibility()` — flood risk contribution (0–100)
- `_calculate_water_availability()` — water score (0–100)
- `_calculate_suitability_scores()` — multi-factor suitability (SuitabilityScores)
- `_generate_recommendations()` — site-specific recommendations

### Router (routers/rainfall.py)

All endpoints:
1. Check feature flag via `_require_flag(flag_name)` → 403 if disabled
2. Call service method
3. Catch ValueError → 503 (GEE service unavailable)
4. Catch validation errors → 422

**New endpoints (v2.0.0):**
- `GET /rainfall/climate-profile?lat&lon`
- `GET /rainfall/anomaly?lat&lon&days=30`
- `GET /rainfall/seasonality?lat&lon`
- `POST /rainfall/site-analysis` with SiteAnalysisRequest body

### Models (models/rainfall.py)

**New Pydantic models:**
- `ClimateProfileResponse`
- `AnomalyResponse`
- `SeasonalityResponse`
- `SiteAnalysisRequest`, `SiteAnalysisResponse`
- `SuitabilityScores`

All models use v2 Pydantic syntax with strict validation.

## GEE Credentials & Production Mode

### Required Environment Variables
```bash
GEE_PROJECT_ID=<project-id>
GEE_SERVICE_ACCOUNT_EMAIL=<service-account@project.iam.gserviceaccount.com>
GEE_SERVICE_ACCOUNT_KEY_PATH=/path/to/service-account-key.json
```

### Production Behavior
- **If credentials present:** Initialize GEE on service startup; use CHIRPS Daily
- **If credentials missing:** Log warning; return 503 on any endpoint that tries GEE
- **No synthetic fallback in production** — misconfigurations should fail fast and visibly

### Testing Behavior
- Mock all service methods in tests using `@patch`
- Never make live GEE calls in CI
- Use synthetic fallback only if GEE fails in tests (verify mocks work correctly first)

## Testing Strategy

**File:** `tests/rainfall_smoke.py`

**Tests (5 total):**
1. `test_health` — health check endpoint
2. `test_archive_flag_off` — 403 when flag disabled
3. `test_summary_flag_off` — 403 when flag disabled
4. `test_archive_flag_on` — 200 with mocked data when flag enabled
5. `test_summary_flag_on` — 200 with mocked data when flag enabled

**Mocking pattern:**
```python
@patch("app.services.rainfall_service.RainfallService._fetch_chirps_daily_series")
def test_archive_flag_on(mock_fetch):
    mock_fetch.return_value = DailySeries(
        dates=["2023-01-01", "2023-01-02"],
        precipitation_mm=[2.5, 3.1],
    )
    # ... test code
```

**New tests needed** (for v2.0.0 endpoints):
- `test_climate_profile_flag_on/off`
- `test_anomaly_flag_on/off`
- `test_seasonality_flag_on/off`
- `test_site_analysis_flag_on/off`
- Response shape validation for all new endpoints

## Implementation Notes

### Trend Calculation
Linear regression on daily series:
- Slope extracted in units of mm/day
- Scaled to years (× 365.25)
- Expressed as % change per year relative to mean daily value

### Drought Risk Assessment
Multi-factor scoring:
```
if annual < 250 or dry_freq > 70 or trend < -5: very_high
elif annual < 500 or dry_freq > 60 or trend < -2: high
elif annual < 750 or dry_freq > 40 or trend < 0: moderate
elif annual < 1000 or dry_freq > 20: low
else: very_low
```

### Runoff Potential
Combines peak seasonal rainfall with annual total:
```
runoff = (peak_season_mm / annual_mm × 100) + (annual_mm / 100)
```
Capped at 0–100.

### Suitability Scores
- **Water availability** = (annual / 500) × 0.7 + (reliability) × 0.3
- **Agriculture** = (annual / 600) × trend_adjusted − drought_penalty
- **Drainage** = (dry_freq / 0.7) × 100 (higher = drier = better drainage)
- **Groundwater recharge** = (annual / 800) × monsoon_damping
- **Infiltration** = ((100 − dry_freq) / 2) + ((annual − winter) / 10)

## File Structure
```
services/rainfall/
├── app/
│   ├── main.py              — FastAPI app, CORS, router mount
│   ├── settings.py          — Pydantic BaseSettings, GEE config
│   ├── models/
│   │   └── rainfall.py      — all Pydantic request/response models
│   ├── routers/
│   │   └── rainfall.py      — endpoint definitions, flag gates
│   └── services/
│       └── rainfall_service.py  — business logic, analytics, GEE integration
├── requirements.txt
├── Dockerfile
├── README.md                — user-facing docs
├── AGENTS.md                — this file
└── tests/                   — handled in tests/ root
