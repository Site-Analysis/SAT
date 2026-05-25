# Wind Service

Wind climatology analysis — ERA5-Land GEE, 16-sector wind rose, IMD 4-season classification, architectural orientation recommendations.

## Status
Placeholder. Source POC at `Vishwas721/sat` `sat04/sat_wind_poc.py` (commit `55cd75e`).

## Port
8003

## Contract
See `contracts/wind.yaml`.

## Feature flag
`feature.wind.climatology`

## Integration checklist
- [ ] Copy `sat04/sat_wind_poc.py` into `app/` structure
- [ ] Add `pyproject.toml` / `requirements.txt`
- [ ] Wire feature flag: `require_flag(FeatureFlag.WIND_CLIMATOLOGY)`
- [ ] Add `Dockerfile`
- [ ] Add service to `docker-compose.yml`
- [ ] Add CI job to `services/README.md`
- [ ] Add smoke test to `tests/`
