# FVD — SAT-11 Infrastructure / Connectivity Service

**Jira Ticket:** SAT-11
**Status:** Migrating (Phase 1 code integration)
**Type:** Story
**Source repo:** TanmayCJ/SAT-Fallback (`ux/phase-1-research`)

---

## Feature Overview

**User Story:** As an architect or developer, I want a connectivity score for a site —
road access, public transit proximity, and power infrastructure within a radius — so I
can judge how serviceable a plot is before committing.

**Business Value:** Turns raw OSM features into a road/transit/power sub-scored
connectivity rating, with an honest disclaimer that under-mapped utilities (water,
sewage, telecom) are detected but not scored.

---

## Commit Traceability

| Commit | Repo | Description |
|---|---|---|
| `141ef0c` | SAT-Fallback | checkpoint(web): … + geo/planning/infrastructure buildout |

Ported into `Site-Analysis/SAT` as branch `feat/infrastructure-service` (Phase 1).

---

## Code Traceability Matrix

| # | Acceptance Criterion | File | Function / Class |
|---|---|---|---|
| 1 | `POST /infrastructure/analyze` returns typed `InfraResult` | `app/routers/infrastructure.py` | `analyze_infrastructure()` |
| 2 | Gated by `feature.infrastructure.connectivity` → 403 when off | `app/routers/infrastructure.py` | `_require_flag()` |
| 3 | Road access (nearest road, type, surface, lanes, width, frontage) from OSM | `app/services/infrastructure_service.py` | `InfrastructureService.analyze()`, `_road_score()` |
| 4 | Transit stops (metro/railway/bus) with distance + line | `app/services/infrastructure_service.py` | `_transit_score()` |
| 5 | Power presence (substation, line voltage/distance) | `app/services/infrastructure_service.py` | `InfrastructureService.analyze()` |
| 6 | Sub-scores: road 0–50, transit 0–30, power 0–20 | `app/models/infrastructure.py` | `InfraSubScores` |
| 7 | Water/telecom detected but scored 0 (honest, OSM India <20%) | `app/models/infrastructure.py` | `InfraSubScores.water`, `.telecom`, `InfraResult.data_disclaimer` |
| 8 | Overall connectivity score + severity band | `app/services/infrastructure_service.py` | `InfrastructureService.analyze()` |
| 9 | Typed request/response models | `app/models/infrastructure.py` | `InfraRequest`, `InfraResult`, `RoadAccess`, `TransitStop`, `UtilityPresence` |

---

## Contract

`contracts/infrastructure.yaml` (v1.0.0) — CHANGELOG 2.2.0.

## Flag

`feature.infrastructure.connectivity` — `FeatureFlag.INFRASTRUCTURE_CONNECTIVITY`, default off.

## Tests

`tests/infrastructure_smoke.py` — health, flag-off 403, flag-on 200 (service monkeypatched).
