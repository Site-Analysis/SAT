# Contract Changelog

## 1.1.0 — 2026-06-07

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

## 1.0.0 — 2026-05-25

### Added
- `temperature.yaml` — `GET /weather/thermal-profile` → `ClimateReport` (12 months, summary, recommendations)
- `sunpath.yaml` — `GET /sunpath/{summer|winter|annual|events}` → pvlib SPA solar position data
- `flood.yaml` — `POST /flood/analyze` → 4-component flood risk score + risk tier
- `wind.yaml` — `GET /analysis/wind/climatology` → 16-sector wind rose, 4 IMD seasons, orientation advice
