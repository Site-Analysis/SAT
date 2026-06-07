# Build Plan: SAT-226 — SunPath Service Migration

**Reads with:** `SAT-226_SunPath_Migration_SPIKE.md` (findings + POC). This is the execution plan.
**Branch:** `feat/sunpath-service` · **Target:** `SAT/services/sunpath/` · **Port:** 8001 · **Flag:** `feature.sunpath.diagram`
**Source of truth:** `Site-Analysis-Tool/src/Backend/SunPath/` (superset — NOT V3; ticket pointer stale).

---

## Context

SAT-226 migrates the Solar/Sun-Path backend into the SAT monorepo. The spike found three divergent builds, a contract matching none, and two must-fix defects. Product decisions: **full solar+shadow scope**, **JSON + optional SVG**, **honor the clean GET contract**, **fold in** orientation recommendations + pybdshadow sunshine-duration. This plan executes that with the repo's established service conventions (mirrors `feat/temperature-service`).

**Two defects that MUST land in this migration (proven in POC):**
1. `solar_engine.py` tz args swapped → `tzfpy.get_tz(longitude, latitude)`.
2. Contract `hour` must map from `local_time` (tz-aware), not `timestamp` (UTC).

**Scope boundary (verified against `apps/web`):** SAT's `apps/web` is a bare Next.js scaffold with **no sunpath/shadow consumer** (`grep` found zero references). Consequences:
- Dropping the `/api/v1` prefix to root paths is **non-breaking** — no SAT consumer exists yet (the legacy `Site-Analysis-Tool`/V3 frontends that call `/api/v1/shadow/*` are not the migration target).
- **This PR is backend-only.** The SAT-226 DoD line *"sun path diagram renders in frontend tab"* is **NOT satisfiable here** — `apps/web` has no tab. That clause moves to the frontend ticket (SAT-228-style); restated DoD below is backend-scoped.

---

## SAT conventions to mirror (verified from `feat/temperature-service`)

- Service layout: `app/main.py`, `app/routers/`, `app/services/`, `app/models/`, `requirements.txt`, `Dockerfile`, `README.md`, `AGENTS.md`. **No `pyproject.toml`** (requirements.txt only).
- `main.py`: `FastAPI(title=..., lifespan=...)`, CORS from env, routers mounted at **root** (no `/api/v1` prefix), **`GET /health` at root**.
- Dockerfile: `python:3.11-slim`, install `curl`, `COPY requirements.txt` → `pip install`, `COPY app/`, `HEALTHCHECK curl /health`, `CMD uvicorn app.main:app --host 0.0.0.0 --port 8001`.
- `docker-compose.yml` already has a `sunpath` block (healthcheck `GET /health`, mounts `gee-sa.json`, `FLAGS` env). **No compose edit needed** beyond confirming.
- Flag `SUNPATH_DIAGRAM` already in `packages/flags/src/flags.py`. Use `from packages.flags.src.flags import is_enabled, FeatureFlag, require_flag`.
- Tests: root `tests/sunpath_smoke.py`; `tests/conftest.py` auto-adds each service dir to `sys.path`. Smoke pattern = guard `from app.main import app` in try/except, `skip_no_app` marker, mock external HTTP.
- CI (`.github/workflows/ci.yml`) gates: **contracts** (`contracts/CHANGELOG.md` must change when `contracts/**` changes), **py** (`ruff check` + `ruff format --check` over `services/`), **smoke** (`pytest tests/` — installs only `pytest httpx`).

---

## Phase 0 — Contract first (gate: contracts CI)

Per `integration-rules.md` #1. Edit **before** any service code.

1. `contracts/sunpath.yaml` — keep the 4 existing GET sun-path endpoints; **add**:
   - `GET /sunpath/diagram.svg?lat&lon&date?` → `image/svg+xml`
   - `GET /sunpath/orientation?lat&lon` → `OrientationResponse` (optimal facade azimuth, summer/winter noon altitude, overhang depth ratio, notes)
   - `POST /shadow/calculate/{polygon,radius,bbox,address}` → `ShadowResponse`
   - `POST /shadow/timeseries/{polygon,radius,bbox}` → `ShadowTimeseriesResponse`
   - `GET /shadow/sunlight-hours?...` → `SunlightHoursResponse` (ground/roof sunshine hours)
   - `POST /buildings/*` → building extraction (GEE/OSM)
   - Confirm `GET /health` at root.
2. `contracts/CHANGELOG.md` — new `## 1.1.0 — <date>` entry listing the additions. **CI fails without this.**

Verify: `npx @redocly/cli lint contracts/sunpath.yaml` (or existing contract lint) green.

---

## Phase 1 — Copy service + apply fixes

1. Copy `Site-Analysis-Tool/src/Backend/SunPath/app/` → `services/sunpath/app/`. **Exclude** `app/workers/` (Celery placeholders).
2. **Restructure routers to root paths** (honor contract):
   - Rename `app/api/v1/` → `app/routers/`; drop `settings.API_V1_PREFIX`; mount routers at root in `main.py`.
   - `solar.py` → `sunpath.py`: replace `POST /solar/*` with `GET /sunpath/{summer,winter,annual,events}` + `GET /sunpath/diagram.svg` + `GET /sunpath/orientation`. Thin adapters over existing `SolarEngine` / `SunpathRenderer` (engine reused unchanged).
   - `health.py` → mount at root `/health` (+ keep `/ready`,`/live`).
   - `shadow.py`, `buildings.py` → keep handlers; drop prefix.
3. **Apply Fix #1:** `solar_engine.py` → `tzfpy.get_tz(longitude, latitude)`.
4. **Apply Fix #2:** in `sunpath.py` adapter, `hour = pd.Timestamp(row.local_time).hour` (not `timestamp`).
5. `main.py` → adopt temperature's slim pattern (title `SAT-Platform Backend`, env CORS, lifespan); GEE init in lifespan stays **graceful-degrade** (log + disable buildings on failure).
6. **Flag-gate** new sun-path + shadow routes. ⚠️ `require_flag()` raises `RuntimeError` → surfaces as **HTTP 500** in a FastAPI dependency. Wrap it: a `sunpath_enabled` dependency that does `if not is_enabled(FeatureFlag.SUNPATH_DIAGRAM): raise HTTPException(status_code=403, detail="feature disabled")`. (Tests/verification below expect 403, not 500.)

---

## Phase 2 — Fold-in features

1. **Orientation** (`GET /sunpath/orientation`): port POC #5 logic — equator-facing facade (`south` N-hemi / `north` S-hemi), summer-vs-winter noon altitude from `solar_engine`. New `app/services/orientation_service.py` + model. ⚠️ **Validate the overhang formula before shipping** — `1/tan(summer_noon_alt)` is shadow-length-per-unit-height, not the same as window-overhang *depth* (which also depends on window height + desired shade line). Treat the POC value as provisional; check semantics against a passive-shading design reference (e.g. projection factor PF = overhang depth / window height) and label the output field accordingly so a designer isn't misled.
2. **Sunlight-hours** (`GET /shadow/sunlight-hours`): port pybdshadow's ground/roof sunshine-duration grid method, **driven by pvlib angles** (not suncalc). New `app/services/sunlight_hours.py`. **BSD-3 attribution** in file header + `services/sunpath/THIRD_PARTY_LICENSES.md`.

---

## Phase 3 — Packaging

1. `requirements.txt` — pin from source, **remove** `celery`, `redis`; keep `pvlib==0.11.1, matplotlib==3.9.2, shapely, pyproj, geopy, earthengine-api, tzfpy, pytz, fastapi, uvicorn`. Add `geopandas, rtree` only if the ported sunlight-hours method needs them (prefer plain shapely to avoid heavy deps).
2. `Dockerfile` — mirror temperature's; port 8001; `HEALTHCHECK /health`. Force matplotlib `Agg` (`ENV MPLBACKEND=Agg`).
3. `README.md` + `AGENTS.md` — service overview, run, GEE note.
4. Confirm `docker-compose.yml` `sunpath` block (already present) builds + `gee-sa.json` mount.
5. **ruff pass:** `ruff format services/sunpath && ruff check services/sunpath --fix` — imported code is not ruff-clean; CI runs `ruff format --check`. Must be clean.

---

## Phase 4 — Tests (gate: smoke CI)

`tests/sunpath_smoke.py` (mirror temperature pattern — guard import, `skip_no_app`, mock OSM/GEE HTTP):
- `GET /health` → 200.
- **Regression for Fix #1:** `solar_engine.detect_timezone(12.97, 77.59) == "Asia/Kolkata"` (not Arctic).
- **Regression for Fix #2:** BLR Jun-21 `GET /sunpath/summer` → peak-elevation point at **local hour 12 ±1**; sunrise ~05:5x IST.
- Accuracy: BLR Jun-21 peak elevation ∈ [76,80]; Delhi Dec-21 day length ∈ [10.0,10.6].
- `GET /sunpath/diagram.svg` → `image/svg+xml`, body has `<svg`.
- `GET /sunpath/orientation?lat=12.97&lon=77.59` → facade `south`, summer>winter altitude.
- Shadow: `POST /shadow/calculate/polygon` (mock GEE) → FeatureCollection; 30 m @ 25° → ~64 m.
- `GET /shadow/sunlight-hours` → grid with hours ∈ [0,24].

**CI caveat:** the smoke job installs only `pytest httpx`, so app import (needs pvlib/matplotlib) will **skip** there like temperature's does. To actually run the regressions in CI, add a sunpath step to the `smoke` job: when `services/sunpath/**` changes, `pip install -r services/sunpath/requirements.txt` before `pytest`. Otherwise validation is local/docker only — call this out in the PR.

---

## Phase 5 — PR → CI → merge

1. `feat/sunpath-service` branch; one feature, reviewable.
2. Run `feature-reviewer` agent (per SAT-226 step 1) on shadow/face-shadow/OSM before pushing.
3. Push → CI: contracts ✓, ruff ✓, smoke ✓.
4. PR body: link spike + FVD; note V3-vs-src/Backend decision, the 2 fixes, fold-ins, BSD attribution, the CI smoke-deps caveat, rollback note (revert branch; flag default-off means no prod exposure).
5. Self-review with `/code-review`; address; merge.

---

## Verification (end-to-end, local)

```bash
# 1. Service boots, health at root
cd services/sunpath && pip install -r requirements.txt
MPLBACKEND=Agg FLAGS=feature.sunpath.diagram uvicorn app.main:app --port 8001 &
curl -s localhost:8001/health                     # 200 healthy

# 2. Sun-path JSON, correct tz/hours (the 2 fixes)
curl -s "localhost:8001/sunpath/summer?lat=12.9716&lon=77.5946" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['timezone']);p=max(d['hourly_data'],key=lambda x:x['elevation']);print('peak hour',p['hour'],'elev',round(p['elevation'],1))"
# expect: Asia/Kolkata · peak hour 12 · elev ~78

# 3. Diagram + orientation + shadow + sunlight-hours
curl -s "localhost:8001/sunpath/diagram.svg?lat=12.97&lon=77.59" | head -c 40   # <svg
curl -s "localhost:8001/sunpath/orientation?lat=12.97&lon=77.59"                 # south
curl -s -X POST localhost:8001/shadow/calculate/polygon -d '{...}'               # FeatureCollection
curl -s "localhost:8001/shadow/sunlight-hours?lat=12.97&lon=77.59&date=2025-06-21"

# 4. Flag off → gated routes 403
FLAGS= uvicorn ... ; curl -s -o /dev/null -w "%{http_code}" "localhost:8001/sunpath/summer?..."  # 403

# 5. Full stack
docker-compose up sunpath        # healthy
pytest tests/sunpath_smoke.py -v # green (with reqs installed)
```

**DoD:** `/health` 200 · sun-path JSON has correct IST hours · diagram SVG renders · orientation + sunlight-hours respond · shadow responds · flag-gated · smoke green · CI green.

---

## Risks carried from spike

| Risk | Handling |
|---|---|
| matplotlib heavy/headless | `MPLBACKEND=Agg` in Dockerfile + env; SVG not PNG |
| GEE in CI | graceful-degrade; smoke mocks GEE |
| Imported code not ruff-clean | Phase 3 `ruff format` + `--fix` pass |
| Smoke CI lacks pvlib | add per-service `pip install -r` step (Phase 4 caveat) |
| pybdshadow port adds geopandas/rtree | prefer plain shapely; add deps only if required |
| Shadow timeseries slow (180s FE timeout) | preserve pagination; document as perf debt, not fixed here |
