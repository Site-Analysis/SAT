# SPIKE: SAT-226 — Migrate Solar / Sun Path Service to SAT Monorepo

**Supersedes:** SAT-65 spike (`[Karthik] SAT-65.docx`) — that spike validated *pvlib accuracy* in the abstract and ignored the three existing builds, the SAT contract, the shadow coupling, and the migration itself. This revision is migration-focused.

**Owner:** Chirag · **Story:** SAT-226 · **Related:** SAT-21 (spike, Done), SAT-65 (story, In Progress), FVD-06
**Timebox:** 2 days (1 day POC, 0.5 reconciliation, 0.5 doc)
**Status:** Draft — awaiting approval to execute POC

---

## 1. The real question

Karthik's spike asked *"is pvlib accurate?"* — already answered (NREL SPA, ±0.0003°, used in all builds). The question that actually de-risks SAT-226 is:

> **Three divergent "sun path" implementations exist and the SAT contract matches none of them. Which code migrates, under which API shape, and how does the clean contract absorb the shadow/buildings half of the service it never specified — without breaking the frontend, which already renders the sun-path diagram client-side?**

---

## 2. Findings — three builds, one contract, all different

| # | Build | Location | API shape | Role |
|---|---|---|---|---|
| 1 | **Karthik prototype** | GitHub `Site-Analysis/Sprint0_User_Stories @ SolarAnalysis(Karthik)` → `server.py` (single 30KB file) | `POST /solar-position`, `POST /sun-path` → **PNG**, `POST /sun-path/data` → JSON | FVD-06 source. Matplotlib Marsh diagram. Standalone, no shadow. |
| 2 | **Structured service** | `Site-Analysis-Tool/src/Backend/SunPath/` (+ near-identical V3 copy) | `POST /api/v1/solar/{position,sunpath,sunpath/svg}` **+ `/shadow/*` + `/buildings/*`** + GEE/OSM | Evolution of #1. The migration source. |
| 3 | **SAT contract** | `SAT/contracts/sunpath.yaml` | `GET /sunpath/{summer,winter,annual,events}?lat&lon` → JSON; `GET /health` | Designed top-down. **Unbuilt.** Covers only sun-path, not shadow. |

**Reality checks that reframe the work:**

1. **The diagram already renders client-side — verified in BOTH frontends.** V3 `SunPathResultView.tsx` uses the `suncalc` JS lib; the primary `Site-Analysis-Tool/src` uses `utils/solarCalculations.ts` (`calculateSolarMetrics`). Neither calls `/solar/*` — both `sunPathApi.ts` files hit the backend **only** for `/shadow/*` and `/health`. The structured service's `/solar/*` endpoints are *dead code* for every live frontend. **Implication:** moving sun-path to `GET /sunpath/*` is **non-breaking** — there is no live consumer of the old POST `/solar/*` paths to migrate.
2. **Contract-first is law here** (`integration-rules.md` #1: "update OpenAPI specs before code changes"). The contract is the canonical target — but it is currently wrong (POST vs GET, path prefixes, response shapes) and incomplete (no shadow/buildings).
3. **The ticket's source pointer is stale.** SAT-226 says source = `SiteAnalysisToolV3/`. SAT's own `services/sunpath/README.md` and a `diff -rq` say **`Site-Analysis-Tool/src/Backend/SunPath/`** — it is a strict superset (adds `workers/`, sketchup integration, docker-compose, init/seed scripts). **Use src/Backend; treat V3 pointer as outdated.**
4. **`workers/` (Celery) + Redis are placeholders** ("to be implemented"). Do **not** migrate them. Drop `celery`, `redis` from pinned deps.

---

## 3. Locked decisions (from product owner)

| Decision | Choice | Consequence |
|---|---|---|
| **Scope** | **Full solar + shadow service** | Migrate solar + shadow engine + face-shadow + building extraction + GEE/OSM. ~5× a sun-path-only migration. |
| **Diagram rendering** | **Both** — JSON + optional image | Backend returns angle JSON (primary) **and** exposes an optional SVG/PNG render endpoint for export. |
| **Canonical API shape** | **Honor the clean GET contract** | Sun-path endpoints become `GET /sunpath/{summer,winter,annual,events}?lat&lon`. Endpoint layer is rewritten over the existing pvlib engine. |

**Reconciliation rule that follows:** Because scope is *full* but the contract only covers sun-path, the contract must be **extended** (contract-first, before code) to add `/shadow/*` and `/buildings/*` — keeping the clean style: `GET` for the stateless sun-path reads, `POST` for shadow/building queries that carry polygons + time ranges. Sun-path image is added as `GET /sunpath/diagram.svg?...`. All under root paths (no `/api/v1/solar` prefix), `GET /health` at root, per the existing contract.

---

## 4. Target architecture in SAT (`services/sunpath/`)

```
services/sunpath/
  app/
    main.py                 # FastAPI app, root-level routers, /health
    core/      config, logging, exceptions, dependencies
    api/v1/
      sunpath.py            # NEW thin layer: GET /sunpath/{summer,winter,annual,events,diagram.svg}
      shadow.py             # migrated POST /shadow/* (engine reused as-is)
      buildings.py          # migrated POST /buildings/* (GEE/OSM)
      health.py             # GET /health, /ready, /live
    services/               # REUSED unchanged: solar_engine, sunpath_renderer,
                            #   shadow_engine, face_shadow_engine, shadow_timeseries,
                            #   building_extractor, osm_extractor, gee_service, geocoding_service
    models/                 # solar/shadow/building pydantic models
    utils/                  # geo, projections, datetime_utils, cache
  tests/sunpath_smoke.py    # health + one solstice + one shadow call
  requirements.txt          # pinned; celery/redis removed
  pyproject.toml
  Dockerfile
  # + docker-compose block in SAT root, + flag wiring in packages/flags
```

**Engine is reused, not rewritten.** `solar_engine.calculate_solar_position()` and `sunpath_renderer.generate_plot_data()` already produce azimuth/elevation arrays. The new `sunpath.py` endpoints are thin adapters: pick the solstice/equinox date, call the engine, map to the contract's `SunPathResponse {latitude, longitude, timezone, hourly_data:[{hour,azimuth,elevation}]}`. The `/sunpath/diagram.svg` endpoint reuses `sunpath_renderer.render_svg()`.

**Contract delta (write first):** add `/sunpath/diagram.svg`, `/shadow/{calculate,timeseries}/{polygon,radius,bbox,address}`, `/buildings/*` to `contracts/sunpath.yaml`; bump `contracts/CHANGELOG.md`. Existing 4 GET sun-path endpoints unchanged.

**GEE / secrets:** shadow + buildings need a GEE service account. SAT already has `services/service-account.json`. Wire via env (`GEE_SERVICE_ACCOUNT_JSON` path), never bake into image. Service must **degrade gracefully** if GEE init fails (it already logs + disables building endpoints — keep that).

**Feature flag:** `feature.sunpath.diagram` default off (`packages/flags/src/flags.py`). Gate the new sun-path tab; shadow stays behind it too for this PR.

---

## 5. POC — what we build to prove the findings (1 day)

Goal: prove the engine maps cleanly onto the GET contract and the shadow engine runs in isolation, **before** committing to the full migration PR.

1. **Endpoint-adapter POC + field-mapping audit** — stand up `GET /sunpath/summer|winter|annual|events?lat&lon` over the existing `solar_engine`, returning contract-shaped JSON. **Pin the mapping explicitly** (this is where the silent bug lives): pvlib `get_solarposition(method='nrel_numpy')` returns a timestamp-indexed DataFrame with `azimuth`, `elevation`, `apparent_elevation`, `apparent_zenith`. The existing engine already chooses `apparent_elevation` (refraction-corrected) — keep that. Contract mapping: `hourly_data[].azimuth ← df.azimuth`, `hourly_data[].elevation ← df.apparent_elevation`, `hourly_data[].hour ← timestamp.hour` (synthesized from the DatetimeIndex). Resolution: **hourly (`freq='H'`) for the JSON contract**, **5-min for the SVG render** (smooth curves per FVD-06). Diff actual engine output keys against the contract schema and assert no field is dropped/mislabelled. Verify against a known ephemeris (Bangalore Jun 21 solar noon → apparent_elevation ≈ 77–78°; Delhi Dec 21 day length ≈ 10.3 h).
2. **Image parity POC** — call `sunpath_renderer.render_svg()` standalone; confirm the Marsh polar diagram renders headless (matplotlib `Agg`) in a container with no display.
3. **Shadow smoke POC** — run `shadow_engine` on one hardcoded building polygon + timestamp; confirm GEE-optional path works (mock/skip GEE, supply a polygon directly).
4. **Dep/import POC** — fresh venv from pruned `requirements.txt` (no celery/redis); confirm `app.main` imports and `/health` returns 200.
5. **Orientation-recommendation POC** (folded in) — prototype `GET /sunpath/orientation?lat&lon`: from annual solar geometry derive optimal building/facade azimuth (max winter gain, min summer overheating) + overhang depth guidance from summer-vs-winter noon elevation. Verify direction sanity (N-hemisphere → south-facing optimal; overhang sizing scales with summer elevation).

**POC findings get appended to §7 of this doc** before the build plan.

---

## 6. Risks & mitigations

| Risk | Mitigation |
|---|---|
| matplotlib in container (heavy, headless) | Force `Agg` backend; verify in POC #2; SVG over PNG to avoid font/DPI issues |
| GEE service-account / quota in CI | Graceful-degrade path already exists; smoke test skips GEE; mock building input |
| Contract drift (GET vs built POST) | Contract-first: write the spec delta + CHANGELOG *before* endpoint code |
| Shadow timeseries is slow (frontend uses 180s timeout + retries) | Out of scope to optimize; preserve existing pagination; document as known perf debt |
| Both frontends already render sun-path via suncalc/solarCalculations; backend sun-path endpoints unused | Confirmed non-breaking — no FE calls `/solar/*`. New `GET /sunpath/*` endpoints exist for contract parity + SVG export; optional FE rewire to consume them is a separate ticket, not this PR |
| V3 vs src/Backend divergence | Decided: src/Backend is canonical superset; note in PR |

---

## 7. POC findings

Executed against the real `Site-Analysis-Tool/src/Backend/SunPath` code + its venv (pvlib 0.11.1, matplotlib 3.9.2). All 5 experiments **PASS**. Scratch scripts in `/tmp/poc_sunpath*.py` (throwaway).

| # | Experiment | Result | Evidence |
|---|---|---|---|
| 1 | Engine → GET-contract field mapping | ✅ PASS *(after 2 fixes — see below)* | `SolarPositionData` exposes `timestamp(UTC), local_time(tz-aware), azimuth, elevation(=apparent), zenith, hour_angle, declination, sunrise, sunset, solar_noon, day_length`. BLR Jun21 peak elev **78.4°** (✓); Delhi Dec21 day length **10.32 h** (✓). Initial run printed peak "at hour 7" — the assertion only checked elevation/azimuth ranges, *not* the `hour` field, so it masked both bugs below. After fixing tz order **and** sourcing `hour ← local_time`, peak lands at **local hour 12** (solar noon), sunrise **05:54**, sunset **18:47** IST (✓). |
| 2 | Headless matplotlib SVG | ✅ PASS | `render_svg()` with `Agg` → valid 794 KB `<svg>`. No display needed. |
| 3 | Shadow engine, GEE-optional | ✅ PASS | `ShadowEngine(gee_service=None).generate_shadow_polygon()` → valid Polygon list; 30 m building @ 25° sun → **64.3 m** shadow (= 30/tan25° ✓). Pure geometry, no GEE. |
| 4 | Deps import + `/health` | ✅ PASS | `app.main` imports; `GET /api/v1/health` → **200** `{"status":"healthy"}`. GEE init failed gracefully (logged, building endpoints disabled) — service still healthy. Confirms degrade path. |
| 5 | Orientation recommendation (folded in) | ✅ PASS | Prototype `orientation_reco()`: BLR → south-facing, summer noon 79.3° vs winter 53.5°, overhang depth ratio 0.188×window-height. Sydney → north-facing (S-hemisphere ✓). |

### 🔴 BUG #1 — swapped tzfpy args (must fix during migration)
**`app/services/solar_engine.py:43`** calls `tzfpy.get_tz(latitude, longitude)`, but tzfpy's API is `get_tz(lng, lat)` (longitude first). Bangalore (12.97, 77.59) resolves to **`Arctic/Longyearbyen`**, corrupting localized hours + sunrise/sunset (day length + elevation survive — tz-independent). **Fix:** `tzfpy.get_tz(longitude, latitude)`. Verified: buggy→`Arctic/Longyearbyen`, fixed→`Asia/Kolkata` (+ Delhi, Sydney correct). Note `shadow_engine.py:53` already calls it **correctly** — the two engines were inconsistent. Regression test (BLR→Asia/Kolkata) goes in `sunpath_smoke.py`.

### 🟠 MAPPING RULE — `hour` comes from `local_time`, not `timestamp` (build-plan precondition)
`SolarPositionData.timestamp` is **UTC** (e.g. `06:30Z`); `local_time` is tz-aware (`12:00 IST`). The contract's `hourly_data[].hour` must map from **`local_time`**, else the GET endpoints ship UTC hours and the diagram's hour-axis is shifted by the UTC offset. The thin `sunpath.py` adapter must use `local_time.hour`. (This is *why* the initial EXP 1 looked fine — elevation values were correct, only the hour label was wrong.)

### Recommendation
**Proceed to the full migration PR** (`feat/sunpath-service`). Engine + renderer + shadow are reusable over a thin GET adapter; two must-dos baked into the build: (1) tz arg fix, (2) `hour ← local_time` in the adapter. Both verified green. No architectural blockers.

---

## 8. Deliverables

- This spike doc with §7 completed
- POC scripts (4 above) — throwaway, in a `poc/` scratch dir
- A recommendation: proceed to full migration PR (`feat/sunpath-service`) **or** descope shadow to a follow-up
- Detailed build plan (post-approval) for the SAT PR: contract delta → service copy → flag → Dockerfile → compose → smoke tests → CI → merge

## 9. Acceptance criteria traceability (SAT-65 / SAT-21)

| AC (SAT-65) | Covered by |
|---|---|
| Sun path diagram for location | `GET /sunpath/annual` + `/sunpath/diagram.svg` |
| Solar altitude & azimuth displayed | `hourly_data[].{elevation,azimuth}` |
| Building orientation recommendations | ⚠️ **GAP — not implemented anywhere; FOLDED INTO THIS EFFORT** (product owner decision). New backend endpoint `GET /sunpath/orientation?lat&lon` derives optimal facade azimuth + overhang/shading guidance from annual solar geometry (summer-vs-winter elevation). Contract addition + POC experiment #5. |
| Seasonal shadow patterns | `/shadow/timeseries/*` |
| Duration of sunlight (SAT-21) | `GET /shadow/sunlight-hours` — **NEW, folded in**: ground/roof sunshine-hours grid, ported from pybdshadow (BSD-3, attributed). |
| Solstice data exported | `/sunpath/{summer,winter}` + `/sunpath/diagram.svg` download |

**DoD (SAT-226), backend-scoped:** `/health` 200; sun-path JSON returns correct IST-localized hours; diagram SVG renders; orientation + sunlight-hours + shadow endpoints respond; flag-gated (403 when off); smoke green in CI. ⚠️ *"sun-path diagram renders in frontend tab"* is **out of scope for this backend PR** — `apps/web` has no consumer yet; that clause belongs to the frontend ticket (SAT-228-style).

---

## 10. External implementation benchmark (websearch)

Question: is there a *better source* than the homegrown `src/Backend/SunPath` to build on? Verdict per layer: **keep the current base; borrow two things selectively. No wholesale swap.**

### Solar engine — pvlib stays (already best-in-class)
| Lib | Accuracy | Fit | Verdict |
|---|---|---|---|
| **pvlib NREL SPA** *(current)* | ±0.0003° | FastAPI-ready, used everywhere | **Keep.** Gold standard. |
| skyfield | astronomy-grade | heavy, general-purpose ephemeris | overkill |
| pysolar (UMEP uses) | lower | — | downgrade |
| astral | low, lightweight | sunrise/sunset only, no full path | insufficient |
| suncalc(-py) | ~±0.5° | fast, JS+py; current FE + pybdshadow use it | fine for *viz*, not for authoritative angles |

### Sun-path diagram — keep matplotlib replica; Marsh is inspiration-only
- **Andrew Marsh 3D/2D Sun-Path** (andrewmarsh.com) is the gold-standard look (WebGL 3D + SVG 2D polar/orthographic), but **copyright-locked — explicitly forbids copy/derive/reverse-engineer.** Cannot reuse code. Inspiration only.
- **pvlib ships an official polar sun-path example** — could replace ~part of the custom `sunpath_renderer` matplotlib code with the maintained upstream recipe. Low-risk simplification, optional.

### Shadow engine — homegrown is competitive; borrow one feature
**pybdshadow** (BSD-3-Clause, v0.3.5 May-2024, GeoPandas/Shapely) is the strongest external candidate:
| | pybdshadow | current `shadow_engine.py` |
|---|---|---|
| Sun angles | suncalc (~±0.5°) | **pvlib SPA (better)** |
| Ground + rooftop shadow | ✅ | ground only |
| **Sunshine-duration grid** (hrs of sun on ground/roof) | ✅ **(has it)** | ❌ missing |
| Inter-building shadow overlap | ❌ | ✅ **(`_calculate_shadow_overlaps`)** |
| Timeseries | ✅ | ✅ |
| API layer | ❌ Python-only | ✅ FastAPI |

**Verdict:** current engine is ahead on angle accuracy, overlap detection, and API. pybdshadow's one real edge is **sunshine-duration-on-ground/roof** — which maps directly to SAT-21's *"duration of sunlight"* insight. **Decision (product owner): FOLDED IN.** Port pybdshadow's sunshine-duration grid method (BSD-3, with attribution in the source file + a `THIRD_PARTY_LICENSES` note) as a new `GET /shadow/sunlight-hours` endpoint, driven by **pvlib** angles (not suncalc) for consistency with the rest of the service. Do not swap the engine.

Other surveyed: SWAN (open-source 3D city shadow tool, academic), Shadowmap (commercial SaaS), python-dem-shadows (DEM/terrain, not buildings) — none a better fit than current.

**Net:** no better foundation exists; the migration source stands. Two optional, low-risk borrows: pvlib's polar example (trim renderer), pybdshadow's sunshine-duration method (new insight, BSD-licensed).
