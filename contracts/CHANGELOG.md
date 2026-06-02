# Contract Changelog

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
