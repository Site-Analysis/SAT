# SAT

Unified monorepo scaffold for the Site Analysis Tool (SAT). This repository is intentionally empty of feature code. It exists to integrate heavy features safely and incrementally.

## Goals
- Contract-first development (API changes are explicit and reviewed)
- Feature flags default off for new functionality
- Incremental integration with strict CI gates
- Zero breakage on merge

## Structure (high level)
- apps/        Frontend applications
- services/    Backend services (FastAPI)
- packages/    Shared libraries and clients
- contracts/   OpenAPI specs and shared schemas
- migrations/  Database migrations and schema notes
- infra/       Infrastructure and deployment assets
- docs/        Architecture and integration rules
- scripts/     Tooling and automation
- tests/       Cross-service and smoke tests

## Integration workflow (summary)
1. Add or update contract in contracts/.
2. Implement backend slice behind a feature flag.
3. Implement frontend wiring behind the same feature flag.
4. Add tests and documentation.
5. Enable the flag only after validation.

## Status
Scaffold only. No feature code yet.
