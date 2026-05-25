# SunPath Service

Solar position and sun path diagrams via pvlib NREL SPA. Andrew Marsh-style polar + cartesian diagrams. Summer/winter solstice and annual overlays.

## Status
Backend complete. Source at `Site-Analysis-Tool/src/Backend/SunPath/` and `Sprint0_User_Stories` commit `944c5b8` — Jira SAT-21, resolved 2025-11-10.

## Port
8001

## Contract
`contracts/sunpath.yaml` — `GET /sunpath/{summer|winter|annual|events}`

## Feature flag
`feature.sunpath.diagram`

## Run (current source)
```bash
cd Site-Analysis-Tool/src/Backend/SunPath
source venv/bin/activate
uvicorn app.main:app --reload --port 8001
```

## Integration checklist
- [ ] Copy `Site-Analysis-Tool/src/Backend/SunPath/app/` → `services/sunpath/app/`
- [ ] Add `pyproject.toml` + `requirements.txt`
- [ ] Wire feature flag via `packages/flags/src/flags.py`
- [ ] Add `Dockerfile`
- [ ] Add service block to root `docker-compose.yml`
- [ ] Add smoke test to `tests/sunpath_smoke.py`
- [ ] Update `contracts/CHANGELOG.md` if API shape changes
