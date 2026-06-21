# Backend Service Map

Ten FastAPI services in `services/<svc>/`, each a self-contained app (own `app/` package, own
venv, own `requirements.txt`, own contract in `contracts/<svc>.yaml`, own feature flag(s)). All
ship behind flags that **default off** — a disabled endpoint returns **403**. Ports below are
authoritative from `deployment-plan.md` and match `infra/DEPLOY.md` and
`docker-compose.prod.yml`.

| Service | Port | Caddy route (`api.qnit.site`) | Contract ver | Flag(s) | External deps |
|---|---|---|---|---|---|
| temperature | 8000 | `/temperature/*` | 1.1.0 | `feature.temperature.thermal-profile` | Open-Meteo Archive (ERA5); IMD `.grd` (optional, `IMD_DATA_DIR`) |
| sunpath | 8001 | `/sunpath/*` | 1.6.0 | `feature.sunpath.diagram`, `feature.sunpath.solar-day` | pvlib (SPA, local); GEE + Overpass (buildings/shadows) |
| flood | 8002 | `/flood/*` | 1.7.0 | `feature.flood.risk-analysis` | Open-Meteo (SRTM elevation + ERA5 precip); OSM Overpass (water proximity). `gee_enabled=false` |
| wind | 8003 | `/wind/*` | 1.2.0 | `feature.wind.analysis` | Open-Meteo Archive (ERA5 10 m wind, 5-yr) |
| rainfall | 8004 | `/rainfall/*` | 2.0.0 | `feature.rainfall.{archive,summary,climate-profile,anomaly,seasonality,site-analysis}` | Open-Meteo Archive (GEE/CHIRPS path optional, 503 if creds missing in prod) |
| geo | 8005 | `/geo/*` | 1.0.0 | `feature.zoning.land-use`, `feature.geo.amenities`, `feature.geo.kgis-context`, `feature.environment.soil`, `feature.environment.water-constraints` | OSM Overpass; ISRO Bhuvan LULC; KGIS admin layers |
| planning | 8006 | `/planning/*` | 1.0.0 | `feature.planning.site-capacity` | OSM Overpass (road width / metro). Ruleset: NBC 2016, BDA CDP 2031, TOD 2020, ICAO Annex 14 |
| infrastructure | 8007 | `/infrastructure/*` | 1.0.0 | `feature.infrastructure.connectivity` | OSM Overpass (roads, transit, power) |
| future-infra | 8008 | `/future-infra/*` | 1.0.0 | `feature.context.growth-pipeline` | None — curated public-announcement JSON (BMRCL/BDA/NHAI/KIADB, 2024-Q4) |
| land-records | 8009 | `/land-records/*` | 1.0.0 | `feature.land.records` | None — portal-only deep links (Bhoomi/KAVERI/eCourts); no scraping |
| overpass | self-hosted | internal only | — | n/a (infra) | `wiktorn/overpass-api`, Southern Zone PBF |

Full per-version contract history: `contracts/CHANGELOG.md`. Flag registry (source of truth, 20
flags): `packages/flags/src/flags.py` (Python `FeatureFlag` enum) + `packages/flags/src/index.ts`
(TS, frontend subset).

## Endpoints (from each contract)

| Service | Endpoints |
|---|---|
| temperature | `GET /health` · `GET /weather/climate-archive` · `POST /weather/thermal-grid` · `GET /weather/analyze-wind` · `GET /weather/thermal-profile` *(deprecated — zero FE callers; use climate-archive)* |
| sunpath | `GET /sunpath/{summer,winter,annual,solar-day,events,orientation}` · `GET /sunpath/diagram.svg` · `POST /shadow/calculate/{polygon,radius}` · `POST /shadow/timeseries/polygon` · `GET /shadow/sunlight-hours` · `POST /buildings/extract` · `GET /health` |
| flood | `GET /health` · `POST /flood/analyze` |
| wind | `GET /health` · `POST /wind/analyze` |
| rainfall | `GET /health` · `GET /rainfall/archive` · `POST /rainfall/summary` · `GET /rainfall/climate-profile` · `GET /rainfall/anomaly` · `GET /rainfall/seasonality` · `POST /rainfall/site-analysis` |
| geo | `GET /health` · `GET /geo/zone` · `GET /geo/soil` · `GET /geo/water-constraints` · `GET /geo/amenities` |
| planning | `GET /health` · `POST /planning/analyze` |
| infrastructure | `GET /health` · `POST /infrastructure/analyze` |
| future-infra | `GET /health` · `GET /future-infra/pipeline` |
| land-records | `GET /health` · `POST /land-records/lookup` |

## Shared packages

- `packages/flags/` — feature-flag registry + `is_enabled`/`require_flag` (Python) and
  `isEnabled`/`requireFlag` (TS). Flags read from the `FLAGS` env var (comma-separated).
- `packages/settings/` — shared settings incl. GEE service-account loading (`gee.py`).

## Resource & sizing notes

Idle RAM, per-analysis latency, concurrency ceilings and the AWS instance-sizing analysis (B6)
are in `docs/deployment/utilization-estimate.md`. Headlines: full stack idle ≈ 1.3 GiB (10
services) / ≈ 1.8 GiB with Next.js + Overpass → **does not fit AWS free-tier t2.micro**;
recommended beta is **t3.medium**. Overpass is the dominant latency bottleneck on the public API
(~23 s geo/planning) → self-hosted mirror collapses it to <500 ms. Flood has a hard concurrency
wall at N≥10 — needs a semaphore before scaling.
