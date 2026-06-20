# FVD — SAT-12 Future Infrastructure / Growth Pipeline Service

**Jira Ticket:** SAT-12
**Status:** Migrating (Phase 1 code integration)
**Type:** Story
**Source repo:** TanmayCJ/SAT-Fallback (`ux/phase-1-research`)

---

## Feature Overview

**User Story:** As an investor or planner, I want to see planned and under-construction
infrastructure near a site — metro lines, expressways, ring roads, IT parks, SEZs — so I
can judge future growth potential, not just current state.

**Business Value:** Surfaces the development pipeline (with status, expected completion,
distance, and originating agency) that drives land-value appreciation, with an honest
disclaimer that alignments are approximate and must be verified.

---

## Commit Traceability

| Commit | Repo | Description |
|---|---|---|
| `141ef0c` | SAT-Fallback | checkpoint(web): … + future-infra / growth-pipeline buildout |

Ported into `Site-Analysis/SAT` as branch `feat/future-infra-service` (Phase 1).

---

## Code Traceability Matrix

| # | Acceptance Criterion | File | Function / Class |
|---|---|---|---|
| 1 | `GET /future-infra/pipeline` returns typed `PipelineResult` | `app/routers/future_infra.py` | `get_pipeline()` |
| 2 | Gated by `feature.context.growth-pipeline` → 403 when off | `app/routers/future_infra.py` | `_require_flag()` |
| 3 | Curated pipeline loaded from bundled JSON (Bengaluru + pan-India) | `app/services/pipeline_service.py` | `PipelineService.__init__()` |
| 4 | Items filtered to radius via haversine on feature centroid | `app/services/pipeline_service.py` | `_haversine_km()`, `_feature_centroid()` |
| 5 | Each item typed: metro/expressway/ring_road/it_park/sez/… + status | `app/models/future_infra.py` | `PipelineItem`, `PipelineType`, `PipelineStatus` |
| 6 | Growth score + severity from nearby pipeline density | `app/services/pipeline_service.py` | `PipelineService.get_pipeline()` |
| 7 | Honest `data_source` + `data_as_of` + `data_disclaimer` (curated, approximate) | `app/models/future_infra.py` | `PipelineResult.data_source`, `.data_disclaimer` |

---

## Contract

`contracts/future-infra.yaml` (v1.0.0) — CHANGELOG 2.3.0.

## Flag

`feature.context.growth-pipeline` — `FeatureFlag.CONTEXT_GROWTH_PIPELINE`, default off.

## Data

`services/future-infra/data/{bengaluru_pipeline.json,pan_india_pipeline.json}` (bundled,
`COPY data/` in Dockerfile).

## Tests

`tests/future_infra_smoke.py` — health, flag-off 403, flag-on 200 (service monkeypatched).
