# FVD — SAT-18 Rainfall Radar Panel

**Jira Ticket:** SAT-18
**Status:** Migrating (Phase 1 code integration)
**Type:** Story
**Source repo:** TanmayCJ/SAT-Fallback (`ux/phase-1-research`)
**Stacked on:** `feat/public-landing` (PR #71) → `feat/frontend-redesign` (PR #69)

---

## Feature Overview

Monthly rainfall radar (spider) chart in the right-panel rainfall module — replaces the
earlier vertical-bar visualization. Carved out of the frontend base so the base builds
standalone (base shipped the pre-radar `RainfallPanel.tsx` from `11ae435`).

Data comes from the rainfall service (`GET /rainfall/*`), which is flag-gated server-side
(`feature.rainfall.*`); this is the client visualization only.

---

## Commit Traceability

| Commit | Repo | Description |
|---|---|---|
| `9502fed` | SAT-Fallback | rainfall radar panel (monthly spider), nav search removal, landing copy |

Ported into `Site-Analysis/SAT` as branch `feat/rainfall-radar` (Phase 1, stacked).

---

## Code Traceability Matrix

| # | Acceptance Criterion | File |
|---|---|---|
| 1 | Monthly rainfall radar/spider chart component | `components/map/RainfallRadar.tsx` |
| 2 | Rainfall panel renders the radar (replaces vertical bars) | `components/layout/RainfallPanel.tsx` |

---

## Validation

`npm run build --workspace apps/web` compiles clean with the radar wired into the panel.
