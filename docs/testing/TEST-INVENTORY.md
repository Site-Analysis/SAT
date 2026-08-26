# Test Inventory

Complete inventory of the SAT backend test suites: the in-process **smoke** suite (CI gate)
and the live **integration** suite (Stage B, manual). Nothing untracked.

Last re-run on SAT `main`: **2026-06-21** (local, per-service venvs).

---

## 1. Smoke suite — `tests/*_smoke.py` (in-process, CI gate)

FastAPI `TestClient`, no network. One file per service; each file inserts only its own
`services/<svc>` on `sys.path` and CI runs every file in its **own** pytest process (the
`app`-package collision is documented in `tests/conftest.py`). Flag gating is exercised
in-process via `monkeypatch.setenv("FLAGS", ...)`.

### Current pass count (SAT `main`, 2026-06-21)

| File | Service | Tests | Result | Gating flag(s) exercised |
|---|---|---|---|---|
| `flood_smoke.py` | flood | 3 | ✅ 3 passed | `feature.flood.risk-analysis` |
| `future_infra_smoke.py` | future-infra | 3 | ✅ 3 passed | `feature.context.growth-pipeline` |
| `geo_smoke.py` | geo | 6 | ✅ 6 passed | `feature.zoning.land-use` (+ off-path matrix) |
| `infrastructure_smoke.py` | infrastructure | 3 | ✅ 3 passed | `feature.infrastructure.connectivity` |
| `land_records_smoke.py` | land-records | 3 | ✅ 3 passed | `feature.land.records` |
| `planning_smoke.py` | planning | 3 | ✅ 3 passed | `feature.planning.site-capacity` |
| `rainfall_smoke.py` | rainfall | 9 | ✅ 9 passed | `feature.rainfall.{archive,summary,climate-profile,anomaly,seasonality,site-analysis}` |
| `sunpath_smoke.py` | sunpath | 13 | ✅ 13 passed | `feature.sunpath.diagram`, `feature.sunpath.solar-day` |
| `temperature_smoke.py` | temperature | 8 | ✅ 8 passed | `feature.temperature.thermal-profile` |
| `wind_smoke.py` | wind | 4 | ✅ 4 passed | `feature.wind.analysis` |
| `contour_smoke.py` | contour | 5 | on `feat/contour-analysis` (DEM monkeypatched) | `feature.contour.analysis` |
| **Total** | | **55** | **✅ 55 passed, 0 failed** on `main` 2026-06-21; contour is branch-only until merge | |

Plus `tests/temperature_imd_validation.py` — **2 xfailed** (expected: documents correct
`imdlib` API usage; xfail until IMD `.grd` data is mounted and `IMD_DATA_DIR` is set). Not a
smoke file, not in the CI glob; run manually.

### What each file asserts

| File | Assertions |
|---|---|
| `flood_smoke.py` | `/health` → `{status:ok, service:flood}`; `POST /flood/analyze` with `FLAGS=""` → **403**; with flag on → 200, `overall_score ∈ [0,100]` (>40 for Bellandur), component scores present, `metadata.gee_enabled is False`, `data_source` names Open-Meteo. |
| `future_infra_smoke.py` | `/health` → `future-infra`; `GET /future-infra/pipeline` flag-off → 403; flag-on → `score == 72.0`, `pipeline_items[0].type == "metro"`. |
| `geo_smoke.py` | `/health` → `geo`; parametrized endpoints flag-off → 403 (off-path matrix); `GET /geo/zone` flag-on → `zone_class == "Residential"`, `score == 78.0`. |
| `infrastructure_smoke.py` | `/health` → `infrastructure`; `POST /infrastructure/analyze` flag-off → 403; flag-on → `score == 85.0`, `sub_scores.road == 45.0`, `transit[0].type == "metro"`. |
| `land_records_smoke.py` | `/health` → `land-records`; `POST /land-records/lookup` flag-off → 403; flag-on → `bhoomi.raw_data_available is False`, `severity == "none"`, ≥3 deep links incl. a "Bhoomi" label. No network (portal-only). |
| `planning_smoke.py` | `/health` → `planning`; `POST /planning/analyze` flag-off → 403; flag-on → `far_applicable == 2.0`, `buildable_area_sqm == 600.0`, `severity == "low"`. |
| `rainfall_smoke.py` | `/health` → `rainfall`; `archive`/`summary` flag-off → 403; `archive` flag-on → `daily.precipitation_sum == [2.0, 0.0]`; `summary` flag-on → `total_rainfall_mm == 10.0`; `climate-profile` / `anomaly` / `seasonality` / `site-analysis` each gated by their own flag. |
| `sunpath_smoke.py` | health ungated; tz regression (local-not-UTC, not arctic); summer/winter day-length; events shape; `diagram.svg`; orientation recommendation; sunlight-hours open-sky vs building-shadow reduction; flag-off → 403; `solar-day` gated by `feature.sunpath.solar-day` (+ `diagram`); bad date → 422. |
| `temperature_smoke.py` | health + root; `climate-archive` (Mumbai); `thermal-grid` small polygon; deprecated `thermal-profile` still works; no live network calls (cached); flag-off → 403; flag-on → 200. |
| `wind_smoke.py` | `/health` → `wind`; `POST /wind/analyze` flag-off → 403; flag-on → 200; response shape (mean/max speed, direction, seasonal). |
| `contour_smoke.py` | `/health` → `contour`; `POST /contour/analyze` → contours/slope/buildability/hillshade + `hillshade_bounds`; `POST /contour/transect` → finite `lat`/`lng` samples; interval 5 and 70 → **422**. DEM fetch monkeypatched (no live GEE). |

### Run commands

One file per process (required — see `tests/conftest.py`):

```bash
# all smoke files, each in its own process (mirrors CI)
for f in tests/*_smoke.py; do pytest "$f" -v --tb=short -p no:warnings; done

# a single service
pytest tests/sunpath_smoke.py -v
```

**Flags per service:** the smoke tests set `FLAGS` themselves per-test (`monkeypatch.setenv`),
so no env setup is needed to run them. The CI `smoke` job exports a baseline
`FLAGS="feature.temperature.thermal-profile,feature.sunpath.diagram"` and installs every
`services/*/requirements.txt` first. To run a gated endpoint **manually** outside the tests,
export the flag for that service, e.g.:

```bash
FLAGS="feature.flood.risk-analysis" pytest tests/flood_smoke.py -v
```

**Dependencies:** each service ships its own venv. Locally, run a smoke file with that service's
interpreter (e.g. `services/flood/.venv/bin/python -m pytest tests/flood_smoke.py`). Rainfall's
venv is `services/rainfall/venv` (no dot); it shares Open-Meteo deps with temperature.

### CI

`.github/workflows/ci.yml` → `smoke` job. Triggers on `tests/**` or `services/**` changes
(`dorny/paths-filter`). Installs all `services/*/requirements.txt`, then
`for f in tests/*_smoke.py; do pytest "$f"; done`. The glob is **top-level only** — it does not
descend into `tests/integration/`.

---

## 2. Integration suite — `tests/integration/` (live HTTP, manual)

Stage B suite, ported from SAT-Fallback (`testing/backend/`, commit `ed0a35a` + Overpass mirror
fix `3627633`) — see `tests/integration/README.md`. Each file hits a **running** service over
`http://localhost:800x` with `requests`. Requires the full stack up. **Not in the CI gate.**

- 62 tests across 10 services: health, response schema, domain-plausibility ranges, dual-site
  comparison (Bellandur vs Devanahalli).
- Last full run (Fallback, 2026-06-19, Overpass mirror restored): **62 passed, 0 failed, 0
  skipped**, ~113 s. The 2026-06-18 run was 54/62 (8 Overpass tests skipped under public-API
  rate-limiting); a working Overpass mirror resolved all skips.
- Per-service breakdown + mirror config: `matrix.md`. Results + latency + concurrency probe:
  `results.md`. Site coordinates + plausibility ranges: `scenarios.md`.

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d   # stack first
pip install pytest requests
pytest tests/integration/ -v
```

> Re-run the integration suite against the live SAT stack once it is deployed (Phase 4) and
> record the real SAT pass count here — the 62/62 above is the last *Fallback* number.

---

## 3. Coverage gaps (carried from Stage B `matrix.md`)

| Service | Missing coverage |
|---|---|
| temperature | Thermal-grid polygon validation (complex GeoJSON bodies) |
| flood | Coastal / riverine site comparison; concurrency wall (fails at N≥10 — see `results.md`) |
| land-records | Invalid district/taluk (404 vs 422 boundary) |
| all | Frontend-side flag-gating parity (`FLAGS` enforcement in `apps/web`) |
