# Contract Changelog

## 1.0.0 — 2026-05-25

### Added
- `temperature.yaml` — `GET /weather/thermal-profile` → `ClimateReport` (12 months, summary, recommendations)
- `sunpath.yaml` — `GET /sunpath/{summer|winter|annual|events}` → pvlib SPA solar position data
- `flood.yaml` — `POST /flood/analyze` → 4-component flood risk score + risk tier
- `wind.yaml` — `GET /analysis/wind/climatology` → 16-sector wind rose, 4 IMD seasons, orientation advice
