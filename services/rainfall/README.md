# Rainfall Service

Multi-dataset climate and rainfall intelligence backend for the SAT monorepo. Provides historical archive, climate profiles, anomaly detection, seasonal analysis, and comprehensive site-specific suitability metrics for site analysis and planning.

## Port

8004

## Data Sources

**Primary:** CHIRPS Daily (Climate Hazards Group InfraRed Precipitation with Stations) via Google Earth Engine (`UCSB-CHG/CHIRPS/DAILY`)

**Analysis depth:**
- 30-year climate profile analysis for Köppen-Geiger classification
- 10-year seasonal and trend analysis
- Real-time anomaly detection

**Fallback (testing only):** Synthetic deterministic data (if GEE unavailable in non-production)

**Units:** mm/day, mm (aggregates)

**Production mode:** Missing GEE credentials returns HTTP 503; no synthetic fallback

## Contract

`contracts/rainfall.yaml` (v2.0.0)

## Feature Flags

All endpoints gate-checked via feature flags:
- `feature.rainfall.archive` — daily historical data
- `feature.rainfall.summary` — period summaries
- `feature.rainfall.climate-profile` — 30-year climate analysis
- `feature.rainfall.anomaly` — anomaly detection
- `feature.rainfall.seasonality` — seasonal patterns
- `feature.rainfall.site-analysis` — SAT-specific comprehensive analysis

Enable via env var:
```bash
FLAGS=feature.rainfall.archive,feature.rainfall.climate-profile
```

## Run (local)

```bash
cd services/rainfall
uvicorn app.main:app --reload --port 8004
```

## Run (docker)

```bash
cd /Volumes/LocalDrive/SAT
docker-compose up rainfall
```

## Swagger

- http://127.0.0.1:8004/docs

## Endpoints

### Archive & Summary
- `GET /health` — service health
- `GET /rainfall/archive` — historical daily rainfall (CHIRPS)
- `POST /rainfall/summary` — period summaries (total, mean, max, rainy days)

### Climate Analysis
- `GET /rainfall/climate-profile` — 30-year climate classification, monsoon strength, reliability
- `GET /rainfall/anomaly` — current period vs 10-year average anomaly detection
- `GET /rainfall/seasonality` — seasonal distribution, concentration index (summer/monsoon/winter/spring)

### Site Analysis (SAT-specific)
- `POST /rainfall/site-analysis` — comprehensive site suitability for planning

## Response Schemas

### ClimateProfileResponse
```json
{
  "latitude": 19.5,
  "longitude": 75.9,
  "annual_rainfall_mm": 720.5,
  "wettest_month": "9",
  "driest_month": "4",
  "rainfall_variability": 0.42,
  "monsoon_strength": 65.3,
  "climate_classification": "Cw (Temperate Monsoon)",
  "rainfall_reliability_score": 82.4,
  "datasets": ["CHIRPS Daily (UCSB-CHG)"]
}
```

### AnomalyResponse
```json
{
  "latitude": 19.5,
  "longitude": 75.9,
  "period_label": "Last 30 days",
  "current_period_rainfall_mm": 85.2,
  "long_term_average_mm": 62.1,
  "anomaly_percent": 37.2,
  "anomaly_category": "Wet",
  "datasets": ["CHIRPS Daily (UCSB-CHG)"]
}
```

### SeasonalityResponse
```json
{
  "latitude": 19.5,
  "longitude": 75.9,
  "summer_rainfall_mm": 125.3,
  "monsoon_rainfall_mm": 470.2,
  "winter_rainfall_mm": 95.1,
  "spring_rainfall_mm": 29.9,
  "seasonal_distribution": {
    "summer": 17.4,
    "monsoon": 65.3,
    "winter": 13.2,
    "spring": 4.1
  },
  "rainfall_concentration_index": 0.58,
  "datasets": ["CHIRPS Daily (UCSB-CHG)"]
}
```

### SiteAnalysisResponse
```json
{
  "latitude": 19.5,
  "longitude": 75.9,
  "radius_meters": 5000,
  "annual_rainfall_mm": 720.5,
  "summer_rainfall_mm": 125.3,
  "monsoon_rainfall_mm": 470.2,
  "winter_rainfall_mm": 95.1,
  "spring_rainfall_mm": 29.9,
  "rainfall_trend_5yr_percent": 1.2,
  "rainfall_trend_10yr_percent": -0.8,
  "trend_direction": "stable",
  "drought_risk_level": "low",
  "dry_day_frequency": 35.6,
  "runoff_potential": 68.4,
  "flood_susceptibility_contribution": 52.3,
  "water_availability_score": 76.2,
  "suitability_scores": {
    "water_availability_score": 76.2,
    "agriculture_score": 72.1,
    "drainage_score": 58.9,
    "groundwater_recharge_score": 68.5,
    "infiltration_suitability_score": 65.3
  },
  "recommendations": [
    "Strong monsoon influence: plan for seasonal flooding and water abundance",
    "Water availability suitable for irrigation and water-dependent activities"
  ],
  "datasets": ["CHIRPS Daily (UCSB-CHG)"]
}
```

## Analytics Implemented

### Rainfall Trend Analysis
- 5-year and 10-year linear regression trends (% change per year)
- Direction classification: increasing/decreasing/stable

### Rainfall Reliability
- Coefficient of variation (0–1) from 30-year data
- Interannual consistency scoring (0–100)

### Monsoon Analysis
- Monsoon onset/peak detection (Sep–Nov contribution)
- Monsoon strength as % of annual rainfall

### Drought Indicators
- Dry-day frequency (% days with <0.1mm rainfall)
- Rainfall deficit relative to normal
- Drought severity classification (very_low to very_high)

### Site Suitability Metrics
All scored 0–100:
- **water_availability_score** — based on annual rainfall + reliability
- **agriculture_score** — rainfall & trend-adjusted for crop suitability
- **drainage_score** — higher if drier; lower = better drainage
- **groundwater_recharge_score** — based on rainfall & monsoon influence
- **infiltration_suitability_score** — higher for consistent, moderate rainfall

### Climate Classification
Simplified Köppen-Geiger rules:
- **BW** — Desert (<250 mm/yr)
- **BS** — Steppe (250–500 mm/yr)
- **Am/Af** — Tropical (monsoon/wet)
- **Cw/Cfa** — Temperate monsoon/humid subtropical
- **Rainforest** (>2000 mm/yr)

## Example Requests

### Climate Profile (30-year analysis)

Archive:

```bash
curl "http://127.0.0.1:8004/rainfall/archive?latitude=19.07&longitude=72.87&start_date=2023-01-01&end_date=2023-01-10"
```

Summary (point):

```bash
curl -X POST "http://127.0.0.1:8004/rainfall/summary" \
  -H "Content-Type: application/json" \
  -d '{"latitude":19.07,"longitude":72.87,"start_date":"2023-01-01","end_date":"2023-01-31"}'
```

Summary (polygon):

```bash
curl -X POST "http://127.0.0.1:8004/rainfall/summary" \
  -H "Content-Type: application/json" \
  -d '{"geometry":{"type":"Polygon","coordinates":[[[72.85,19.05],[72.90,19.05],[72.90,19.10],[72.85,19.10],[72.85,19.05]]]},"start_date":"2023-01-01","end_date":"2023-01-31"}'
```

## FVD traceability

See `docs/feature-validation/SAT-18_rainfall-analysis.md`. Acceptance criteria mapping is TODO.
