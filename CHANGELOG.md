# Changelog

All notable product-level changes to the SAT (Site Analysis Tool / Qnit) monorepo are
documented here. This is the **release / product** changelog (frontend, services, infra,
deployment). For the API **contract** history see [`contracts/CHANGELOG.md`](contracts/CHANGELOG.md).

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). No git release
tags have been cut yet; version headers below mark product milestones, not tagged releases.

## [1.0.0] — 2026-06-21 — Beta Go-Live 🚀

First public Beta. Frontend live at **qnit.site** (tool) + **qnit.in** (landing); backend at
**api.qnit.site** (single EC2 t3.medium, Mumbai, behind Caddy). Go-live confirmed 2026-06-21 —
all 10 analysis modules verified rendering end-to-end over HTTPS. See `deployment/` (phases 0–6)
and `deployment/POST-GOLIVE-TODO.md`.

### Added

#### Frontend — `apps/web` (Next.js 16 + React 19, deployed on Vercel)
Single-page project workspace (`app/project/[id]`): a Leaflet map with draw tools and a right
panel of analysis module sections; plus dashboard, project-new, settings, and an email +
Google-OAuth login (Supabase auth). Persistence is client-side (localStorage) by design.

Ten analysis modules wired in `lib/api/analysis.ts`, each with a panel and/or map overlay:
- **Temperature** — monthly climate profile + annual stats + ECBC envelope cards
  (`TemperaturePanel`), plus a real annual-mean spatial heatmap over the site polygon
  (`ThermalField` / `TemperatureOverlay`, via `POST /weather/thermal-grid`).
- **Sun path** — annual sun-path + optimal-orientation readout, an interactive 3D study
  (`Scene3D`) driven by the per-date `GET /sunpath/solar-day` endpoint, and `SunPathArc` /
  `SunOverlay` map layers.
- **Flood** — risk score, component breakdown, and flood-zone map rings/overlay
  (`FloodRiskPanel`, `FloodZoneRings`, `FloodZoneOverlay`).
- **Wind** — speed/direction analysis with wind rose (`WindPanel`, `WindRose`, `WindOverlay`).
- **Rainfall** — climate/anomaly readout with rainfall radar + rose
  (`RainfallPanel`, `RainfallRadar`, `RainfallRose`, `RainfallOverlay`).
- **Geo** — land-use zone, soil, water-constraints, and amenities, with zoning context map
  overlays and legend (`ZoningContextOverlay`, `ZoningMapLegend`).
- **Planning / zoning capacity** — FAR, buildable area, setbacks, height envelope and
  compliance HUDs (`components/zoning/*`: `FarGauge`, `BuildableDonut`, `HeightEnvelopeBar`,
  `SetbackPlanDiagram`, `ComplianceMatrix`, …).
- **Infrastructure** — connectivity (road / transit / utility) scoring.
- **Future-infra** — nearby planned-infrastructure growth pipeline.
- **Land records** — `LandRecordsPanel` surfacing Bhoomi/court-case portal deep links.
- Client-side report export (`app/project/[id]/export`, `components/export/ReportDocument`,
  `ReportFeaturePage`, `lib/export/generators.ts`) — per-feature PDF report.
- Public landing page (SAT-17), rainfall radar panel (SAT-18), full app-shell redesign (SAT-16),
  and host-based routing for the two-domain deploy (qnit.in landing + qnit.site tool).

#### Services — 10 FastAPI microservices (`services/*`, ports 8000–8009)
- **temperature** (8000) — `GET /weather/climate-archive` (Open-Meteo proxy),
  `POST /weather/thermal-grid` (spatial heatmap), `GET /weather/analyze-wind`,
  `GET /weather/thermal-profile`.
- **sunpath** (8001) — `GET /sunpath/{summer,winter,annual,events,orientation,diagram.svg}`,
  per-date `solar-day` (3D study), plus `shadow/*` calculate/timeseries and building extraction
  endpoints.
- **flood** (8002) — `POST /flood/analyze`.
- **wind** (8003) — `POST /wind/analyze`.
- **rainfall** (8004) — `GET /rainfall/{archive,climate-profile,anomaly,seasonality}`,
  `POST /rainfall/{summary,site-analysis}`.
- **geo** (8005, SAT-14) — `GET /geo/{zone,soil,water-constraints,amenities}`.
- **planning** (8006, SAT-10) — `POST /planning/analyze` (FAR, ground coverage, setbacks, max
  height, TOD metro bonus, ICAO airport height restriction).
- **infrastructure** (8007, SAT-11) — `POST /infrastructure/analyze` (road / transit / utility
  connectivity).
- **future-infra** (8008, SAT-12) — `GET /future-infra/pipeline` (planned-infrastructure growth).
- **land-records** (8009, SAT-13) — `POST /land-records/lookup` (portal deep links; no scraping
  by design).

All non-`/health` endpoints are gated by `packages/flags` feature flags (HTTP 403 when off).

#### Infrastructure & deployment
- Self-hosted Overpass mirror + production compose overlay (SAT-15).
- AWS backend deploy: prod compose override + Caddy reverse proxy; backend service ports bound
  to loopback (security review); HSTS on api.qnit.site.
- Deployment docs: phases 0–6 runbooks, rollback runbook (`docs/deployment/ROLLBACK.md`),
  secrets manifest, AWS utilization/sizing estimate.
- Security hardening: scoped IAM deploy user (root access key disabled, MFA enabled); Supabase
  security advisors resolved/accepted.

### Changed
- **flood** (SAT-07b) — live-data scoring (Open-Meteo SRTM elevation + ERA5 precipitation + OSM
  water-body proximity), replacing the deterministic `math.sin(seed)` placeholder.
- **wind** (SAT-09b) — live-data analysis (Open-Meteo ERA5 10 m wind, 5-year daily), replacing
  the placeholder.
- Dropped "GeoKnit" branding (trademark not secured); added proprietary license, per-file
  copyright headers, and Qnit favicon.
- Rainfall UI recolored to blue; landing "Try free" CTA contrast fix.

### Fixed
- Dependency bumps for vulnerable pip pins (Dependabot) and `pytest-asyncio` for pytest 9.
- CI: `pull-requests:read` for paths-filter; flags `tsconfig` + `@types/node` so `lint`
  (tsc --noEmit) passes.

## [0.2.0] — 2026-06-09

### Added
- **rainfall** service — multi-source climate intelligence (CHIRPS via Google Earth Engine,
  with Open-Meteo).

### Fixed
- **sunpath** — added `User-Agent` header to Overpass API requests; Overpass rejected headerless
  requests with HTTP 406, which broke the shadow endpoints.

## [0.1.0] — 2026-05-25 — Monorepo bootstrap

### Added
- Initial monorepo scaffold: Next.js web app, contracts-first workflow, feature flags, Docker
  compose, CI. Initial service contracts for temperature, sunpath, flood, and wind.
