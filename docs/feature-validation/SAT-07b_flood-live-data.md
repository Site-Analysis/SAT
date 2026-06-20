# FVD — SAT-07b Flood Risk: live-data scoring

**Jira Ticket:** SAT-07 (extension)
**Status:** Migrating (Phase 1 code integration)
**Type:** Story
**Source repo:** TanmayCJ/SAT-Fallback (`ux/phase-1-research`)

Replaces the monorepo flood service's deterministic placeholder scoring with live data.
Builds on the migrated flood service (FVD SAT-07). **Response schema unchanged.**

---

## Commit Traceability

| Commit | Repo | Description |
|---|---|---|
| `141ef0c` | SAT-Fallback | checkpoint(web): … flood_service live-data rewrite |

Ported into `Site-Analysis/SAT` as branch `feat/flood-service` (Phase 1).

---

## What changed

`main`'s `flood_service.py` computed component scores from `math.sin(seed)` over lat/lon
(a deterministic placeholder with a `# TODO: replace with GEE` note). This rewrite uses
real data:

| # | Acceptance Criterion | File | Function |
|---|---|---|---|
| 1 | Elevation from Open-Meteo SRTM | `app/services/flood_service.py` | `_fetch_elevation()` |
| 2 | Rainfall from Open-Meteo ERA5 5-year daily archive (mean, max, >100 mm days) | `app/services/flood_service.py` | `_fetch_rain()` |
| 3 | Nearest water-body distance from OSM Overpass (haversine to river/water) | `app/services/flood_service.py` | `_fetch_water_distance()`, `_haversine()` |
| 4 | Component risks: elevation / hydrology / rainfall / LLAI → weighted overall | `app/services/flood_service.py` | `_elevation_risk()`, `_hydro_risk()`, `_rain_risk()`, `analyze()` |
| 5 | `metadata.data_source` names Open-Meteo + OSM; `gee_enabled=false` | `app/services/flood_service.py` | `analyze()` |
| 6 | Conservative fallbacks on upstream failure (no fabricated provider data) | `app/services/flood_service.py` | `_fetch_*` |
| 7 | `FloodReport` response schema unchanged | `app/models/flood.py` | (unchanged) |

---

## Contract

`contracts/flood.yaml` 1.6.0 → 1.7.0 — CHANGELOG 2.7.0. Schema unchanged; description +
data-source updated.

## Tests

`tests/flood_smoke.py` — flag-off 403 unchanged; flag-on rewritten to stub the three
fetchers (real scoring, no network) and assert elevated coastal risk + `gee_enabled=false`.
