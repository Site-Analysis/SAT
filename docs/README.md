# Docs

## Process & conventions
- `integration-rules.md` — strict integration workflow
- `feature-flags.md` — flag naming + rules (registry: `packages/flags/`)
- `local-secrets.md` — where secrets live (never committed)
- `adr/0000-template.md` — ADR template
- `PROGRESS.md` — deployment phase log + feature-build timeline

## Architecture (`architecture/`)
- `services.md` — backend service map: ports, routes, contracts, flags, external deps
- `frontend.md` — `apps/web` routing, Supabase auth, domain routing, backend base URLs

## Testing (`testing/`)
- `TEST-INVENTORY.md` — every test, what it asserts, flag, run command, current pass count
- `matrix.md` · `results.md` · `scenarios.md` — Stage B integration suite reports

## Deployment (`deployment/`)
- `README.md` — staging for Phases 4–5; points to `infra/DEPLOY.md`; port + flag reconciliation
- `utilization-estimate.md` — AWS sizing / capacity analysis (B6)

## Feature validation (`feature-validation/`)
- One FVD per feature (`SAT-NN_*.md`) — acceptance criteria → commit/function traceability
