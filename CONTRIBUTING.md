# Contributing

This repo is contract-first and feature-flagged. Do not merge breaking changes without explicit review and migration plans.

## Rules
1. Contracts first: update or add OpenAPI specs in contracts/.
2. Feature flags default off for new functionality.
3. Migrations require a rollback plan and documentation.
4. Tests required for new behavior.
5. Keep changes small and scoped.

## Branching
- feature/<area>/<name>
- fix/<area>/<name>
- chore/<area>/<name>

## PR requirements
- Map acceptance criteria to commits and files.
- Update contracts and changelog when APIs change.
- Add tests and docs.
- Ensure CI is green.
