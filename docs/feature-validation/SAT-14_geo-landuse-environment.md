# FVD — SAT-14 Geo / Land-Use / Environment Service

**Jira Ticket:** SAT-14
**Status:** Migrating (Phase 1 code integration)
**Type:** Story
**Source repo:** TanmayCJ/SAT-Fallback (`ux/phase-1-research`)

---

## Feature Overview

**User Story:** As an architect, I want land-use classification, soil/foundation
indicators, water-body construction constraints, and nearby amenities for a site, so I
can assess developability and context from one geo service.

**Business Value:** Consolidates four context layers (zoning, soil, water setbacks,
amenities) with honest sourcing (OSM-inferred zoning is *not* official BDA/BBMP zoning;
LULC from ISRO Bhuvan; admin context from KGIS).

**Note:** `services/geo` on `main` contained only `README.md` + `AGENTS.md` placeholders;
this branch delivers the app code — additive, no regression.

---

## Commit Traceability

| Commit | Repo | Description |
|---|---|---|
| `141ef0c` | SAT-Fallback | checkpoint(web): … + geo/land-records buildout (zone/soil/water/amenities/kgis/lulc) |

Ported into `Site-Analysis/SAT` as branch `feat/geo-service` (Phase 1).

---

## Code Traceability Matrix

| # | Acceptance Criterion | File | Function / Class |
|---|---|---|---|
| 1 | `GET /geo/zone` → `ZoneResult`, gated by `feature.zoning.land-use` | `app/routers/geo.py` | `get_zone()` |
| 2 | KGIS admin context opt-in via `feature.geo.kgis-context` | `app/routers/geo.py`, `app/services/kgis_service.py` | `get_zone()`, `KgisService` |
| 3 | ISRO Bhuvan LULC class/code/vintage merged into zone | `app/services/lulc_service.py` | `LulcService` |
| 4 | `GET /geo/soil` → `SoilResult`, gated by `feature.environment.soil` | `app/routers/geo.py`, `app/services/soil_service.py` | `get_soil()`, `SoilService.get_soil()` |
| 5 | `GET /geo/water-constraints` → `WaterConstraintResult`, gated by `feature.environment.water-constraints` | `app/routers/geo.py`, `app/services/water_service.py` | `get_water_constraints()`, `WaterService` |
| 6 | `GET /geo/amenities` → `AmenitiesResult` (7 categories), gated by `feature.geo.amenities` | `app/routers/geo.py`, `app/services/amenities_service.py` | `get_amenities()`, `AmenitiesService` |
| 7 | Each endpoint returns 403 when its flag is off | `app/routers/geo.py` | `_require_flag()` |
| 8 | Honest `data_source` + `data_disclaimer` per result | `app/models/geo.py` | `ZoneResult`, `WaterConstraintResult` |
| 9 | Typed models | `app/models/geo.py` | `ZoneResult`, `SoilResult`, `WaterConstraintResult`, `AmenitiesResult`, … |

---

## Contract

`contracts/geo.yaml` (v1.0.0) — CHANGELOG 2.5.0.

## Flags (all default off)

`feature.zoning.land-use`, `feature.geo.kgis-context`, `feature.environment.soil`,
`feature.environment.water-constraints`, `feature.geo.amenities` — registered in
`packages/flags/src/flags.py`.

## Tests

`tests/geo_smoke.py` — health, per-endpoint flag-off 403, zone flag-on 200 (monkeypatched).
