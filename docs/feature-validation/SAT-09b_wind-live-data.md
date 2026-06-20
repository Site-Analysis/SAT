# FVD — SAT-09b Wind Analysis: live-data scoring

**Jira Ticket:** SAT-09 (wind extension)
**Status:** Migrating (Phase 1 code integration)
**Type:** Story
**Source repo:** TanmayCJ/SAT-Fallback (`ux/phase-1-research`)

Replaces the monorepo wind service's deterministic placeholder with live ERA5 data.
Builds on the migrated wind service (FVD SAT-09 wind). **Response schema unchanged.**

---

## Commit Traceability

| Commit | Repo | Description |
|---|---|---|
| `141ef0c` | SAT-Fallback | checkpoint(web): … wind_service live-data rewrite |

Ported into `Site-Analysis/SAT` as branch `feat/wind-service` (Phase 1).

---

## What changed

`main`'s `wind_service.py` derived speed/direction from a deterministic formula
(`# TODO: replace with ERA5-Land or GEE`). This rewrite uses real data:

| # | Acceptance Criterion | File | Function |
|---|---|---|---|
| 1 | 5-year daily wind from Open-Meteo Archive (ERA5, 10 m) | `app/services/wind_service.py` | `WindAnalysisService.analyze()` |
| 2 | Mean speed + max gust | `app/services/wind_service.py` | `analyze()` |
| 3 | Prevailing direction binned to 8 compass points (most common dominant) | `app/services/wind_service.py` | `_bearing_to_compass()`, `analyze()` |
| 4 | India seasonal breakdown (summer/monsoon/winter) | `app/services/wind_service.py` | `_season_mean()` |
| 5 | Comfort + building-impact scoring retained | `app/services/wind_service.py` | (unchanged helpers) |
| 6 | `metadata.data_source` names Open-Meteo ERA5; raises on no data (no fabrication) | `app/services/wind_service.py` | `analyze()` |
| 7 | `WindAnalysis` response schema unchanged | `app/models/wind.py` | (unchanged) |

---

## Contract

`contracts/wind.yaml` 1.1.0 → 1.2.0 — CHANGELOG 2.8.0. Schema unchanged; description +
data source updated.

## Tests

`tests/wind_smoke.py` — flag-off 403 unchanged; both flag-on tests now stub
`wind_service.httpx.Client` with canned ERA5 daily data (real parsing/scoring, no network).
4 pass locally.
