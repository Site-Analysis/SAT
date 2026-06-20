# FVD — SAT-04b Sun-Path 3D Study (per-date solar-day endpoint)

**Jira Ticket:** SAT-04 (extension)
**Status:** Migrating (Phase 1 code integration)
**Type:** Story
**Source repo:** TanmayCJ/SAT-Fallback (`ux/phase-1-research`)

Extends the migrated sunpath service (FVD SAT-04) with the accurate per-date endpoint
that drives the 3D sun-path study.

---

## Commit Traceability

| Commit | Repo | Description |
|---|---|---|
| `315d959` | SAT-Fallback | feat(web): 3D sun-path shadows, map compass, camera-matrix fix |
| `141ef0c` | SAT-Fallback | checkpoint(web): … 3D buildout |

Ported into `Site-Analysis/SAT` as branch `feat/sunpath-3d-flags` (Phase 1).

---

## Scope (additive only — no regression)

| # | Acceptance Criterion | File | Function |
|---|---|---|---|
| 1 | New `GET /sunpath/solar-day?lat&lon&date` returns per-date hourly az/el + events | `app/routers/sunpath.py` | `solar_day()` |
| 2 | New flag `feature.sunpath.solar-day` gates it (in addition to the router-wide `feature.sunpath.diagram`) | `app/core/flags.py` | `SOLAR_DAY_FLAG`, `require_solar_day_flag()` |
| 3 | pvlib SPA per-date positions (not interpolated from reference days) | `app/routers/sunpath.py` | `solar_day()` → `solar_engine.calculate_solar_position()` |
| 4 | Bad date → 422; empty solar engine → 502 | `app/routers/sunpath.py` | `solar_day()` |

### Deliberately NOT ported (sibling-regression guard)

The Fallback `osm_extractor.py` hunk that **removes the Overpass `User-Agent` header**
was *not* ported. `main` added that header (contract CHANGELOG 1.5.1) to fix Overpass
`406 Not Acceptable`. Porting the Fallback version would revert that fix. `osm_extractor.py`
is left at `main`'s version; only the additive flag + endpoint are migrated.

---

## Contract

`contracts/sunpath.yaml` 1.5.1 → 1.6.0 — CHANGELOG 2.6.0.

## Flag

`feature.sunpath.solar-day` — `FeatureFlag.SUNPATH_SOLAR_DAY`, default off.

## Tests

`tests/sunpath_smoke.py` — added: solar-day flag-off 403 (diagram-only), flag-on 200
(both flags, engine monkeypatched), bad-date 422. 13 pass locally.
