# SAT Integration Guide

Detailed playbook for integrating features into the SAT monorepo. Pair this with `integration-rules.md` (the canonical short ruleset) and `CLAUDE.md` (top-level dev workflow).

---

## 1. Repository Overview

### Purpose
SAT (`Site-Analysis/SAT` on GitHub, **public**, main branch protected) is the canonical deployable build target. It is intentionally empty of feature code. Features are migrated one at a time from the review workspace at `/Volumes/LocalDrive/Site Analysis/` after FVD validation and pre-migration cleanup.

### Layout
```
apps/web/              Next.js 16 + React 19 frontend (port 3000)
services/              FastAPI backends — one per analysis type
  temperature/         port 8000  thermal profile (IMD + Open-Meteo)
  sunpath/             port 8001  solar position + sun path (pvlib)
  flood/               port 8002  flood risk (GEE MERIT/JRC/MODIS)
  wind/                port 8003  wind climatology (GEE ERA5-Land)
  geo/                 port 8004  admin boundaries + vegetation (GEE)
packages/flags/        Shared FeatureFlag enum (Python)
contracts/             OpenAPI YAML — one per service + CHANGELOG.md
docs/                  This guide, FVDs, ADRs, integration-rules.md
docker-compose.yml     All services + web
.claude/               Team-shared agents/skills/commands (mcp.json gitignored)
```

### Current state (as of branch `chore/claude-tooling-setup`, PR #1)

| Area | Status |
|---|---|
| Monorepo scaffold | Done — apps/services/packages/contracts directories present |
| Contracts | 4/5 written (temperature, sunpath, flood, wind). **`geo.yaml` missing.** |
| Feature flag enum | Bootstrapped at `packages/flags/src/flags.py` |
| CI gates | npm + ruff + smoke + contract-changelog gate passing |
| Service code | **None.** All 5 service dirs are empty stubs with a README. |
| Frontend app | Next.js 16 scaffold only — no auth wiring, no map, no API client |
| FVDs in `docs/feature-validation/` | **Empty.** 9 source FVDs live in `Site Analysis/Docs/feature-validation/` and must be copied + renamed `SAT-XX_*.md` per CLAUDE.md convention |
| Docker compose | Skeleton present, no service blocks wired |
| Pre-commit hooks | `.pre-commit-config.yaml` committed (ruff + detect-private-key) |
| Claude tooling | `feature-migrator`, `contract-validator` agents + `/migrate-feature` skill committed |

### Source feature inventory (Site Analysis workspace)
Each row maps a source backend to its SAT target. Sources marked **Direct** have working code in `Site-Analysis-Tool/src/Backend/`; sources marked **Indirect** require porting from a different repo or fork.

| # | Feature | Jira | FVD | SAT target | Source | Mode |
|---|---|---|---|---|---|---|
| 1 | Temperature & thermal profile | SAT-9 | FVD-08 | `services/temperature/` | `Site-Analysis-Tool/src/Backend/Temperature/` | Direct |
| 2 | Solar / sun path | SAT-21 | FVD-06 | `services/sunpath/` | `Site-Analysis-Tool/src/Backend/SunPath/` | Direct |
| 3 | Wind analysis | SAT-4 | FVD-09 | `services/wind/` | `Vishwas721/sat` (sat04/) | Indirect |
| 4 | Flood risk | — | FVD-04 | `services/flood/` | `Site-Analysis-Tool/src/Backend/FloodPlains/` | Direct |
| 5 | Vegetation analysis | SAT-18 | FVD-02 | `services/geo/` (part) | `SiteAnalysis_GEE` | Indirect |
| 6 | Admin boundaries | — | FVD-03 | `services/geo/` (part) | `SiteAnalysis_GEE` | Indirect |
| 7 | GEE interactive map | SAT-18 | FVD-01 | `apps/web/` | `SiteAnalysis_GEE` | Indirect |
| 8 | Next.js frontend platform | SAT-23 | FVD-07 | `apps/web/` | `SiteAnalysisV2` | Indirect |
| 9 | PDF report generation | SAT-23 | FVD-05 | TBD (cross-cutting) | `SiteAnalysis_GEE` | Indirect |

---

## 2. Core Things to Build First (Foundation)

These are **prerequisites** to any feature migration. None are feature work themselves — they unblock everything else. Build in order.

### F1. Copy + rename FVDs into SAT
Source FVDs are `FVD-XX_*.md`; CLAUDE.md and `/migrate-feature` skill expect `SAT-XX_*.md`. Map each FVD to its Jira key (see table above), copy `/Volumes/LocalDrive/Site Analysis/Docs/feature-validation/FVD-XX_*.md` to `/Volumes/LocalDrive/SAT/docs/feature-validation/SAT-YY_*.md`. Without this, `/migrate-feature temperature` aborts at pre-flight.

### F2. Service skeleton template
Pick ONE service (temperature) and build the canonical layout. Every later service copies this:
```
services/temperature/
  app/
    main.py              FastAPI app, mounts routers, /health
    routers/             one router per contract path
    services/            business logic, GEE/HTTP clients
    models/              Pydantic v2 request/response models
    deps.py              dependency injection (settings, clients)
    settings.py          pydantic-settings, reads from env
  tests/
    test_smoke.py        curls /health, asserts 200
  pyproject.toml         deps + ruff config inheritance
  requirements.txt       pinned, generated from pyproject
  Dockerfile             python:3.12-slim, multi-stage
  .env.example           required env vars documented
  AGENTS.md              already exists — keep updated
```

### F3. `packages/flags/` real implementation
Currently a stub. Needs:
- `StrEnum FeatureFlag` with all 5 service flags declared up front
- `is_enabled(flag) -> bool` reads `FLAGS=` env var (comma-separated)
- TS mirror under `packages/flags/ts/` for frontend parity (or inline in `apps/web/lib/`)
- README documenting the flag-naming convention (`feature.<service>.<capability>`)

### F4. Shared HTTP client package (frontend)
`apps/web/lib/api/` with one file per service. Each exports a typed client generated from the OpenAPI YAML (use `openapi-typescript` + `openapi-fetch`). Avoids drift between contract and frontend. Add `npm run codegen` script.

### F5. Frontend shell
Minimum for any feature wiring:
- Supabase auth context + protected route guard
- Map page (Leaflet) with point selection → emits `{lat, lng}`
- Right side panel with tab list (Temperature / Sun / Flood / Wind / Geo)
- Each tab gated by its FeatureFlag — disabled chip if off
- `.env.example` lists `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### F6. Docker compose wired
Add service block template:
```yaml
temperature:
  build: ./services/temperature
  ports: ["8000:8000"]
  env_file: .env
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```
Replicate per service as it migrates. `apps/web` block reads `NEXT_PUBLIC_*_API_URL` for each.

### F7. Smoke test runner
`tests/smoke.py` that boots compose, hits each enabled service's `/health`, then runs one canonical request per service (e.g. `POST /temperature/profile` with a fixed lat/lng). Wired to CI on push to any `feat/*` branch.

### F8. Add `geo.yaml` contract
Required before any geo service work. Define endpoints for admin boundaries lookup + vegetation NDVI bbox query (FVD-02, FVD-03). Add to `contracts/CHANGELOG.md`.

### F9. Pre-commit + secret scan in CI
Already have `.pre-commit-config.yaml` with `detect-private-key`. Add a GitHub Action that runs `gitleaks` on PRs — defense in depth since the repo is public.

### F10. ADR for cross-cutting decisions
Use `docs/adr/0000-template.md` to record: GEE service-account distribution, Supabase project tier, Open-Meteo rate limit handling, IMD data licensing. One ADR per decision, numbered.

---

## 3. Which Features to Integrate First

Ordering criteria (priority high → low):
1. **External dependency weight** — no auth/keys first, GEE next, paid APIs last
2. **FVD completeness** — features with full acceptance-criteria → code traceability migrate cleanly
3. **Source quality** — `Direct` sources in `Site-Analysis-Tool/` are review-ready; `Indirect` need more cleanup
4. **User-visible value** — pick features that, alone, demonstrate the product loop (pick site → get insight)
5. **Risk surface** — small/simple first, builds team confidence in the workflow before tackling heavyweights

### Recommended order

#### Phase 1 — Prove the workflow (Week 1)
**1. Temperature (SAT-9, FVD-08)** — first feature to migrate.
- Why first: zero auth (Open-Meteo is public), single endpoint, FVD is complete and recent (Mar 2026), source code is local + recently maintained, exercises the entire pipeline end-to-end without external-cred risk.
- Output: validates the F1–F7 foundation. If `/migrate-feature temperature` succeeds, every later migration follows the same script.
- Gate before declaring done: hit `POST /temperature/profile` from `apps/web` map page, see chart render, flag toggle works.

#### Phase 2 — Add a second deps-light feature (Week 2)
**2. Sun Path (SAT-21, FVD-06)** — adds pvlib but no remote APIs.
- Why second: pvlib is pip-only, no external service. Proves the frontend tab pattern with a second service. Builds confidence with a calculation-heavy backend (solar position math) before adding remote-API failure modes.
- Risk: pvlib version pinning matters — fix the version in `requirements.txt` and document in AGENTS.md.

#### Phase 3 — First GEE-backed feature (Week 3)
**3. Wind (SAT-4, FVD-09)** — introduces GEE via ERA5-Land.
- Why before flood: source is `Vishwas721/sat` (one repo, focused), ERA5-Land is well-documented, wind rose output has clear visual validation. Tests the GEE service-account flow without flood's 4-component scoring complexity.
- Prerequisites: `gee-sa.json` distributed, ADR on GEE auth, GEE quota reviewed.

#### Phase 4 — Heaviest backend (Week 4)
**4. Flood (FVD-04)** — heaviest GEE dependency mix (MERIT DEM, JRC water, MODIS LULC, hydrology).
- Why fourth: 4 GEE datasets, scoring logic in `gee_utils.py` + `chart_generator.py`, has its own PDF generator. Migration is the largest single PR; do it after wind has shaved the GEE-auth bugs.
- Gate: smoke test must include a fixed coordinate with known flood score to detect scoring regressions.

#### Phase 5 — Geo service (Week 5)
**5. Geo (FVD-02, FVD-03)** — admin boundaries + vegetation NDVI.
- Why last among services: source lives in `SiteAnalysis_GEE` (separate repo, older code), needs `geo.yaml` written from scratch (F8), and the FVDs are spike-style so acceptance criteria are looser.
- Sub-order inside geo: admin boundaries (simple bbox lookup) before vegetation (needs GEE NDVI time series).

### Explicitly deferred (Phase 6+)
- **PDF report (FVD-05)**: cross-cutting — defer until 3+ services produce data. Then build as a separate `services/reports/` that aggregates.
- **3D simulation, NBC engine, energy/carbon, BIM exports (FVD-11–15)**: New features, not migrations. Out of scope for v1 deployable.
- **Realtime collaboration (FVD-16)**: defer to v2.
- **Rainfall, terrain (FVD-10, FVD-18)**: post-v1, after the 5 core services ship.

---

## 4. Per-Feature Migration Playbook

Driven by `/migrate-feature <service>`. Manual fallback steps (in order):

1. **Pre-flight in SAT** — working tree clean, on `main`, FVD exists at `docs/feature-validation/SAT-XX_*.md`.
2. **Source review** — spawn `feature-reviewer` agent against the source path. Block on any reviewer-flagged issue (hardcoded creds, Pydantic v1 idioms, missing CORS, etc.). Apply fixes in the source workspace first.
3. **Branch** — `git checkout -b feat/<service>-service`.
4. **Contract** — update `contracts/<service>.yaml`, bump version, append entry to `contracts/CHANGELOG.md`. Commit: `feat(contracts): <service> v1.x.x`.
5. **Flag** — add `FeatureFlag.<SERVICE>_<CAPABILITY>` to `packages/flags/src/flags.py`. Default off. Commit: `feat(flags): add <service> flag`.
6. **Service code** — copy cleaned source into `services/<service>/app/`. Add `requirements.txt`, `pyproject.toml`, `Dockerfile`, `.env.example`, `tests/test_smoke.py`. Commit: `feat(<service>): service implementation`.
7. **Compose** — add service block to `docker-compose.yml`. Commit: `feat(<service>): docker-compose wiring`.
8. **Smoke test** — add `tests/<service>_smoke.py`. Commit: `test(<service>): smoke`.
9. **Frontend** — wire tab in `apps/web/`, gated by the new flag. Commit: `feat(web): <service> panel`.
10. **PR** — `gh pr create`. Verify all 4 CI jobs pass. Wait for review.
11. **Merge** — after approval. Flag stays off in production `.env`.
12. **Enable in prod** — after manual validation against a known site, add the flag to `FLAGS=` in prod env.

### Commit hygiene
Logical commits, one purpose each (contracts / flag / service / docker / tests / frontend). Makes reverting any single layer trivial. No mega-commits.

### CI gates (must all pass before merge)
- `contracts` — `contracts/CHANGELOG.md` modified iff `contracts/*.yaml` modified
- `py` — ruff lint + format on all touched Python files
- `js` — `npm run lint` + `npm run build` for `apps/web`
- `smoke` — `tests/smoke.py` boots compose, hits `/health` per service

---

## 5. Definition of Done (per feature)

A feature is considered integrated when **all** of:
- [ ] FVD exists at `docs/feature-validation/SAT-XX_*.md` and all ACs map to commits/functions
- [ ] Contract YAML matches FastAPI route signatures (`contract-validator` agent passes)
- [ ] FeatureFlag enum entry exists, default off
- [ ] Service has `/health` returning 200 with `{status: "ok", service: "<name>"}`
- [ ] Service runs via `docker-compose up <service>` with no errors
- [ ] Smoke test passes in CI
- [ ] Frontend tab renders behind flag; toggling flag in `.env` hides/shows it
- [ ] PR merged, CI green
- [ ] Manual validation against one known-good coordinate documented in PR description
- [ ] Flag enabled in production `.env` only after validation

---

## 6. Related Docs
- `integration-rules.md` — canonical short ruleset
- `feature-flags.md` — flag naming and lifecycle
- `feature-validation/` — FVDs (populate via F1)
- `adr/` — architectural decisions (one per cross-cutting choice)
- `CLAUDE.md` (repo root) — Claude tooling, dev workflow, Jira access
- `apps/web/AGENTS.md` — Next.js 16 specific rules
- `services/<service>/AGENTS.md` — per-service migration notes
