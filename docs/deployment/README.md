# Deployment Docs (staging for Phases 4–5)

Reference material for backend (Phase 4) and frontend (Phase 5) deploy. The **operational
checklist** itself is `infra/DEPLOY.md` (landed in Phase 1 via the overpass-selfhost PR; it is
the Fallback deploy checklist `e744d1d`, byte-identical). This folder holds the supporting
analysis the checklist references.

## Contents

- **`utilization-estimate.md`** — the AWS sizing / capacity analysis (Stage B "B6"). Idle RAM
  per service, per-analysis latency, concurrency ceilings, free-tier verdict, instance
  recommendation, external-quota ceilings. Source: Fallback `e744d1d`. Consume in Phase 4
  (right-sizing) and Phase 5.

## Operational checklist

`infra/DEPLOY.md` covers: required secrets, service image list + ports, build steps, first-time
Overpass init, prod compose (`docker-compose.yml` + `docker-compose.prod.yml`), Supabase/Google
Auth setup, the all-services health-check loop, and minimum instance sizing.

## Port reconciliation (vs `deployment-plan.md` port map) — ✅ MATCHES

The plan's authoritative port map and `infra/DEPLOY.md` agree on every service port, including
the two called out for confirmation:

| Service | Plan | DEPLOY.md | |
|---|---|---|---|
| temperature | 8000 | 8000 | ✅ |
| sunpath | 8001 | 8001 | ✅ |
| flood | 8002 | 8002 | ✅ |
| wind | 8003 | 8003 | ✅ |
| **rainfall** | **8004** | **8004** | ✅ |
| **geo** | **8005** | **8005** | ✅ |
| planning | 8006 | 8006 | ✅ |
| infrastructure | 8007 | 8007 | ✅ |
| future-infra | 8008 | 8008 | ✅ |
| land-records | 8009 | 8009 | ✅ |
| overpass | (self-hosted, internal) | container `12345` | ℹ︎ DEPLOY pins the container port; plan treats it as internal-only. Caddy does not expose it. |

## ⚠ Flag-string reconciliation (action for Phase 4)

`infra/DEPLOY.md` ships a sample production `FLAGS` string it calls "all 18". The **flag registry
is the source of truth** (`packages/flags/src/flags.py`, **20** flags). The DEPLOY string is
stale and must be corrected before prod enable:

- **Phantom (in DEPLOY, not registered):** `feature.terrain.analysis`, `feature.simulation.3d` —
  remove.
- **Missing (registered, not in DEPLOY):** `feature.rainfall.climate-profile`,
  `feature.rainfall.anomaly`, `feature.rainfall.seasonality`, `feature.rainfall.site-analysis` —
  add if those rainfall endpoints should be live.

Phase 4 should regenerate the prod `FLAGS` string directly from `FeatureFlag` so it cannot drift.

## Cross-references

- Service map (ports, routes, deps, flags): `docs/architecture/services.md`
- Frontend deploy (Vercel, domains, env): `docs/architecture/frontend.md`
- Test suites (smoke gate + live integration): `docs/testing/TEST-INVENTORY.md`
