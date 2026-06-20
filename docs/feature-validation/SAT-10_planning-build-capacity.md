# FVD — SAT-10 Planning / Build-Capacity Service

**Jira Ticket:** SAT-10
**Status:** Migrating (Phase 1 code integration)
**Type:** Story
**Source repo:** TanmayCJ/SAT-Fallback (`ux/phase-1-research`)

---

## Feature Overview

**User Story:** As an architect or urban planner, I want a build-capacity report for a
plot — applicable FAR, ground coverage, setbacks, maximum height, and buildable area —
derived from Indian planning regulation (NBC 2016, BDA CDP 2031, BDA TOD 2020) and
airport height surfaces (ICAO Annex 14), so I can size a feasible building envelope
before design.

**Business Value:** Turns scattered regulation (FAR tables, TOD metro bonuses, DGCA/AAI
airport restrictions) into a single deterministic envelope + suitability score, with an
explicit data disclaimer pointing back to the governing notifications.

---

## Commit Traceability

| Commit | Repo | Description |
|---|---|---|
| `141ef0c` | SAT-Fallback | checkpoint(web): zoning build-capacity dashboard … + planning service buildout |

Ported into `Site-Analysis/SAT` as branch `feat/planning-service` (Phase 1).

---

## Code Traceability Matrix

| # | Acceptance Criterion | File | Function / Class |
|---|---|---|---|
| 1 | `POST /planning/analyze` returns a typed `PlanningResult` | `app/routers/planning.py` | `analyze_planning()` |
| 2 | Endpoint gated by `feature.planning.site-capacity` → 403 when off | `app/routers/planning.py` | `_require_flag()` |
| 3 | Applicable FAR from zone × road-width bracket (NBC 2016 Table 15) | `app/services/planning_service.py` | `_lookup_far()`, `NBC_FAR` |
| 4 | TOD FAR 4.0 within 500 m of metro for Residential/Mixed Use (BDA TOD 2020) | `app/services/planning_service.py` | `_detect_metro()`, `TOD_FAR` |
| 5 | Ground coverage, max height per zone (NBC 2016) | `app/services/planning_service.py` | `NBC_GROUND_COVERAGE`, `NBC_MAX_HEIGHT` |
| 6 | Setbacks scaled by plot area + road width | `app/services/planning_service.py` | `_setbacks()` |
| 7 | ICAO Annex 14 airport height surface caps max height + DGCA NOC flag | `app/services/planning_service.py` | `_icao_max_height()`, `AAI_AIRPORTS` |
| 8 | Road width auto-detected from OSM when not supplied (width / lanes×3.5) | `app/services/planning_service.py` | `_detect_road_width()` |
| 9 | Buildable area = plot_area × FAR | `app/services/planning_service.py` | `PlanningService.analyze()` |
| 10 | Suitability score (10–95) + severity band | `app/services/planning_service.py` | `PlanningService.analyze()` |
| 11 | Honest `data_source` + `data_disclaimer` citing governing regulations | `app/models/planning.py` | `PlanningResult.data_source`, `.data_disclaimer` |
| 12 | Typed request/response models | `app/models/planning.py` | `PlanningRequest`, `PlanningResult`, `AirportRestriction` |

---

## Contract

`contracts/planning.yaml` (v1.0.0) — CHANGELOG 2.1.0.

## Flag

`feature.planning.site-capacity` — registered in `packages/flags/src/flags.py`
(`FeatureFlag.PLANNING_SITE_CAPACITY`), default off.

## Tests

`tests/planning_smoke.py` — health, flag-off 403, flag-on 200 (service monkeypatched).
