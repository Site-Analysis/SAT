# FVD — SAT-16 Frontend Redesign (app shell)

**Jira Ticket:** SAT-16
**Status:** Migrating (Phase 1 code integration)
**Type:** Story
**Source repo:** TanmayCJ/SAT-Fallback (`ux/phase-1-research`)

---

## Feature Overview

Ports the full `apps/web` Next.js application from SAT-Fallback — the analysis map,
right-panel module system (temperature/sunpath/flood/wind/rainfall/geo/planning/
infrastructure/land-records), 3D sun-path scene, drawing/measurement tools, zoning
build-capacity dashboard, export, and Supabase auth/project wiring. `main` previously
held only scaffolding (`app/`, `lib/`, `package.json`).

The two cleanly-separable additive features are carved into stacked follow-up PRs so this
base builds standalone:
- **`feat/public-landing`** (on this branch) — `components/landing/*` + the landing-gate
  `app/page.tsx`. Base ships the pre-landing `app/page.tsx` (`redirect("/dashboard")`).
- **`feat/rainfall-radar`** (on public-landing) — `RainfallRadar.tsx` + the radar
  `RainfallPanel.tsx`. Base ships the pre-radar `RainfallPanel.tsx`.

The qnit rebrand, map-measurement tools, and the 3D `setPixelRatio` fix are part of this
snapshot (not separable from the core files) — folded into the base, noted in the PR.

---

## Commit Traceability

| Commit | Repo | Description |
|---|---|---|
| `4fc6128` | SAT-Fallback | frontend redesign + live backend wiring + 3D-viz plan |
| `eb835fe` | SAT-Fallback | analysis map overlays, drawing tools, map search, basemap restyle |
| `25240a7` | SAT-Fallback | map overlays, analysis config, sun path, shadow opacity slider |
| `141ef0c` | SAT-Fallback | zoning build-capacity dashboard, climate layer, 3D + geo/planning/land-records |
| `315d959` | SAT-Fallback | 3D sun-path shadows, map compass, camera-matrix fix |
| `7480002` | SAT-Fallback | profile dropdown, nav cleanup, compass redesign |
| `340a1c4` | SAT-Fallback | delete button + zoning infinite-loading fixes |
| `260116b` | SAT-Fallback | toggle positions below compass + amenities fallback |
| `11ae435` | SAT-Fallback | qnit rebrand (tokens/logo/login) — rebrand half folded into base |
| `09895ad` | SAT-Fallback | polygon measurements, SiteConfigCard, flood zone rework, green accent |
| `410a998` | SAT-Fallback | 3D `setPixelRatio` fix on shared MapLibre canvas |

Ported into `Site-Analysis/SAT` as branch `feat/frontend-redesign` (Phase 1 base).

---

## Validation

- `npm install` regenerates root `package-lock.json` (workspace deps).
- `npm run build --workspace apps/web` → **compiles clean** (Next.js 16.2.6, TS passes,
  9 routes generate: `/`, `/dashboard`, `/login`, `/project/[id]`(+export/loading/new),
  `/settings`).
- apps/web has no `lint` script; CI `js` job (`npm ci` + `npm run lint --workspaces
  --if-present`) passes (lint skipped, install in sync via committed lockfile).

## Carve provenance (historical states)

- Base `app/page.tsx` ← `1d0c0d0` (pre-landing redirect stub).
- Base `components/layout/RainfallPanel.tsx` ← `11ae435` (pre-radar).
- `components/landing/` and `components/map/RainfallRadar.tsx` omitted from base (added in
  stacked PRs B/C).
