# FVD — SAT-15 Self-hosted Overpass + Production Compose

**Jira Ticket:** SAT-15 (infra)
**Status:** Migrating (Phase 1 code integration)
**Type:** Infra / Story
**Source repo:** TanmayCJ/SAT-Fallback (`ux/phase-1-research`)

---

## Feature Overview

OSM-backed services (geo, infrastructure, planning, flood, sunpath) hammer the public
Overpass mirrors and hit rate limits / high latency. This adds a **self-hosted Overpass
mirror** (Southern Zone PBF) plus a production compose overlay and a deploy checklist.

---

## Commit Traceability

| Commit | Repo | Description |
|---|---|---|
| `e744d1d` | SAT-Fallback | self-hosted Overpass, prod compose overlay, deploy checklist, B6 AWS sizing |
| `3627633` | SAT-Fallback | Overpass mirror routing + telecom query syntax; 62/62 tests pass |

Ported into `Site-Analysis/SAT` as branch `feat/overpass-selfhost` (Phase 1).

---

## Scope (this branch)

| # | Acceptance Criterion | File |
|---|---|---|
| 1 | `overpass` service (wiktorn/overpass-api, Southern Zone PBF, lz4) added to dev compose with `overpass-db` volume + healthcheck | `docker-compose.yml` |
| 2 | Production overlay: no source mounts, `--workers 2`, `restart: unless-stopped`, `OVERPASS_MODE=run` | `docker-compose.prod.yml` |
| 3 | Deploy checklist: secrets, images, Overpass init, Supabase/GEE auth, health-check loop, instance sizing | `infra/DEPLOY.md` |

No contract, no feature flag (pure infra).

## Integration note (deferred wiring)

Per-service `OVERPASS_URL=http://overpass:80/api/interpreter` routing is applied as the
OSM services land + adopt env-based Overpass URLs (geo/infrastructure compose blocks
arrive in their own PRs; flood/sunpath read their Overpass URL from settings/constants).
The mirror service + prod overlay land here; final env wiring is completed during the
integration phase once all service blocks are on `main`. The dev compose comment on the
`overpass` service records which services route to it.

## Validation

- `docker-compose.yml` and `docker-compose.prod.yml` parse as valid YAML.
- First boot: `OVERPASS_MODE=init` downloads + imports the PBF (~20 min, `start_period: 1200s`);
  prod overlay switches to `OVERPASS_MODE=run` so restarts don't wipe the DB.
