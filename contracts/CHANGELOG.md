# Contract Changelog

## 1.5.1 — 2026-06-09

### Fixed — sunpath service (`osm_extractor.py`)
- Added `User-Agent` header to all Overpass API `requests.post()` calls.
  Overpass API rejects headerless requests with `406 Not Acceptable`, which
  caused `POST /shadow/calculate/*` to fail for every request.
  No contract change; shadow endpoints behave identically.
## 2.0.0 — 2026-06-08

### Changed — rainfall.yaml (production-grade climate intelligence)
- **Version**: 1.1.0 → 2.0.0
- **New endpoints**:
  - `GET /rainfall/climate-profile` → 30-year climate analysis (Köppen-Geiger, reliability, monsoon strength)
  - `GET /rainfall/anomaly` → rainfall anomaly detection (vs 10-year average)
  - `GET /rainfall/seasonality` → seasonal distribution analysis (summer/monsoon/winter/spring)
  - `POST /rainfall/site-analysis` → SAT-specific comprehensive site analysis
- **Enhanced schemas**: ClimateProfileResponse, AnomalyResponse, SeasonalityResponse, SiteAnalysisResponse, SuitabilityScores
- **Production requirements**: Missing GEE credentials now returns HTTP 503 (no synthetic fallback in production)
- **Analytics**: Trend analysis (5yr/10yr), drought risk, runoff potential, flood susceptibility, multi-factor suitability scoring
- **Data sources**: CHIRPS Daily (primary), with documented fallback strategy for testing

## 1.7.0 — 2026-06-08

### Changed — rainfall.yaml
- Updated rainfall data source from synthetic to CHIRPS Daily via Google Earth Engine
- Updated service description to note GEE as primary source with synthetic fallback
- Version bumped to 1.1.0

## 1.6.0 — 2026-06-07

### Added — flood.yaml (SAT-07 service delivered)
- Flood service now in the monorepo (`services/flood`); `flood.yaml` updated to the
  expanded contract the earlier `1.3.0` entry described: 0–100 component scoring
  (`elevation`, `hydrology`, `flood_history`, `llai`), `metadata`, and the
  `feature.flood.risk-analysis` 403 gate on `POST /flood/analyze`.

## 1.5.0 — 2026-06-07

### Added (sunpath.yaml — SAT-226 migration)
- `GET /sunpath/diagram.svg` → Andrew Marsh-style polar diagram as `image/svg+xml`
- `GET /sunpath/orientation` → `OrientationResponse` (optimal facade azimuth + overhang projection factor)
- `POST /shadow/calculate/{polygon,radius}` → `ShadowResponse` (buildings + shadow FeatureCollections)
- `POST /shadow/timeseries/polygon` → `ShadowTimeseriesResponse`
- `GET /shadow/sunlight-hours` → `SunlightHoursResponse` (ground/roof sunshine grid; method ported from pybdshadow, BSD-3, pvlib-driven)
- `POST /buildings/extract` → building `FeatureCollection` (OSM/GEE)
- Schemas: `OrientationResponse`, `ShadowPolygonRequest`, `ShadowRadiusRequest`, `ShadowTimeseriesRequest`, `ShadowResponse`, `ShadowTimeseriesResponse`, `SunlightHoursResponse`, `FeatureCollection`

### Note
- Existing `GET /sunpath/{summer|winter|annual|events}` unchanged. Service moves from prototype `POST /api/v1/solar/*` to these root GET paths; `hour` field sourced from tz-aware local time.

## 1.4.0 — 2026-06-06

### Changed — wind.yaml
- Updated wind response schema: simplified to POST `/wind/analyze` endpoint
- Added comfort_analysis and building_impact sections
- Added seasonal breakdown (summer/monsoon/winter)
- Added 403 response for feature-flag gating

## 1.3.0 — 2026-06-04

### Changed — flood.yaml
- Expanded flood response schema (0-100 scoring, component analyses, metadata)
- Updated request shape to latitude/longitude + radius_meters
- Added 403 response for feature-flag gating

## 1.2.0 — 2026-06-03

### Added — rainfall.yaml
- Added `GET /rainfall/archive`, `POST /rainfall/summary`, and `GET /health`
- Added schemas for `RainfallArchiveResponse`, `RainfallSummaryRequest`, `RainfallSummaryResponse`

## 1.1.0 — 2026-06-02

### Changed — temperature.yaml
- Added live endpoints: `GET /weather/climate-archive`, `POST /weather/thermal-grid`, `GET /weather/analyze-wind`
- Added `GET /health` endpoint
- Marked `GET /weather/thermal-profile` as **deprecated** (zero frontend call sites; use `climate-archive` instead)
- Extended `ClimateRecommendations` schema: added optional `climate_zone` and `cdd_hdd_ratio` fields
- Extended `thermal_comfort_status` enum to include estimated-fallback variants (`Hot / Estimated`, etc.)
- Added `ThermalGridRequest`, `ThermalGridResponse`, `OpenMeteoArchiveResponse` schemas
- Corrected `year` parameter default: `today.year - 1` (was incorrectly documented as `2023`)
- Relaxed `ClimateReport.monthly_data` array constraint: `minItems: 1` (was `12`, too strict for estimated fallback)

## 1.0.0 — 2026-05-25

### Added
- `temperature.yaml` — `GET /weather/thermal-profile` → `ClimateReport` (12 months, summary, recommendations)
- `sunpath.yaml` — `GET /sunpath/{summer|winter|annual|events}` → pvlib SPA solar position data
- `flood.yaml` — `POST /flood/analyze` → 4-component flood risk score + risk tier
- `wind.yaml` — `GET /analysis/wind/climatology` → 16-sector wind rose, 4 IMD seasons, orientation advice