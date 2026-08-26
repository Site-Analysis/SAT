# SAT-19 — Contour Analysis Frontend: Implementation Plan

**Status:** Implemented (WP-0 through WP-9)
**Revision:** rev-2 — incorporates an external spec review; six product decisions previously left implicit are now resolved in §3 (AD-16 to AD-21). See §15 for the change log.
**Implementation log:** 2026-08-21 — all work packages landed in this pass. See the Progress section below.
**Owner ticket:** SAT-19 · FVD: `docs/feature-validation/SAT-19_contour-analysis.md`
**Requirements source of truth:** `Contour_Frontend_UI_Requirements.md` (repo root)
**Backend:** `services/contour/` (port 8010) — **already built and wired** (Dockerfile, compose block, smoke test, feature flag, and OpenAPI contract all exist)
**Target:** `apps/web/` — Next.js 16 · React 19 · react-leaflet 5 · Leaflet 1.9 · Tailwind 4 · zustand 5 · recharts 3

---

## Progress (2026-08-21)

| WP | Status | Notes |
|---|---|---|
| WP-0 Contract addendum | **Done** | `hillshade_bounds` on `ContourResponse`; `lat`/`lng` on `TransectPoint`. Contract 2.9.0. Payload increase: ~200 points × two floats ≈ a few KB. |
| WP-1 Foundation | **Done** | `lib/contour/*`, `lib/stores/contour.ts`, `svcFetch` throws `ApiError` + cancel signal, `polygonAreaM2` promoted to `lib/geo.ts`. Error mapping exercised (`assertContourErrorMapping`). |
| WP-2 Panel shell | **Done** | Eligibility, reactive status (no `/health`), interval select, run/re-run/cancel, InfoTip. |
| WP-3 Results | **Done** | DEM card, slope stats + InfoTips + stacked bar, aspect, buildability. |
| WP-4 Map layers | **Done** | Panes, canvas renderer, nonce keys, zoom-gated labels. |
| WP-5 Map chrome | **Done** | Layer control, legend, map status as MapContainer siblings. |
| WP-6 Transect drawing | **Done** | Draw store `"transect"` mode (AD-18), Start circle / End diamond, keyboard path. |
| WP-7 Transect graph | **Done** | Hand-built SVG, imperative crosshair + cursor marker, rAF readout. |
| WP-8 Page wiring + report | **Done** | Single `contourVisible` flag, D-12 scoring fix, `ContourReportVisual`, stored interval on export. Legacy files deleted. |
| WP-9 Hardening | **Done** | Fixtures gated by `NEXT_PUBLIC_CONTOUR_FIXTURES=1`. Frontend patterns added to `apps/web/CLAUDE.md`. FVD frontend ACs added. |

`npx tsc --noEmit` (apps/web) is clean. Contour smoke tests need the contour service venv (`pip install -r services/contour/requirements.txt`) before `pytest tests/contour_smoke.py`.

---

## 0. How agents must use this plan

1. **Read this whole document before touching code.** The decisions in §3 are already made — do not re-litigate them, do not "improve" the architecture mid-stream.
2. **Read `apps/web/AGENTS.md` and `apps/web/CLAUDE.md` first.** Next.js 16 has breaking changes versus training data. Consult `node_modules/next/dist/docs/` before writing component code.
3. **Work-package order is mandatory** (WP-0 through WP-9). WP-0 and WP-1 unblock everything else. Within a work package, files may be built in parallel.
4. **§5 (Design System Contract) is binding.** Every hex value, radius, font size and spacing value you write must come from §5. Do not introduce a colour, radius or type size that is not listed there. If §5 genuinely lacks something you need, add it to §5 in the same PR with a one-line rationale.
5. **§7 (Copy Deck) is binding.** Every user-visible string lives in `lib/contour/copy.ts`. Do not hardcode strings in components.
6. **Each work package has an inline Definition of Done.** A WP is not done until every box passes.
7. **Do not delete or weaken existing behaviour** to make something pass. If this plan conflicts with what you find in the codebase, stop and report it rather than improvising.

### Non-goals
- No backend feature work beyond the single contract addendum in WP-0 (`hillshade_bounds`).
- No new basemap, no 3D terrain, no vector tiles, no DEM caching layer.
- No redesign of `RightPanel`, `AnalysisModuleSection`, or the report shell — contour plugs into them as they are.

---

## 1. Scope and Deliverables

| Deliverable | Location |
|---|---|
| Control panel: title, blurb, service status, eligibility, interval, run, loading, error, last-run summary | Right panel, inside the existing `Contour` module section |
| DEM metadata display and warning surfacing | Right panel |
| Slope statistics with hover/focus explanations (8 metrics) | Right panel |
| Aspect statistics | Right panel |
| Buildability summary and legend | Right panel + map legend |
| Four independently toggleable map layers (hillshade, contours, slope, buildability) | Map (Leaflet) + HTML layer control |
| Contour labels — index persistent, all hoverable | Map |
| Transect tool: start / clear / confirm, instructions, loading, error | Map + right panel |
| Transect map rendering: dashed line, distinct Start/End markers, vertices, active drawing state | Map |
| Transect elevation profile graph with scrub-to-map-marker sync and point readout | Right panel + map |
| Transect summary: length, min, max, relief, DEM source, sample count | Right panel |
| All error, empty and disabled states | Panel + map |
| Legends for every visible layer | Map |
| Report and export integration | `components/export/` |
| Accessibility: keyboard, focus, non-colour-only, screen-reader labels | Everywhere |

---

## 2. Current-State Audit

A first-cut contour frontend already exists. **It is a scaffold, not the deliverable.** It covers roughly 30% of the requirements and carries several real defects. Treat it as reference material to be replaced, not extended.

### 2.1 Existing files

| File | Lines | Verdict |
|---|---|---|
| `apps/web/components/layout/ContourPanel.tsx` | 166 | **Replace.** Missing: service status, eligibility indicator, DEM metadata block, 6 of the 8 slope stats, all hover explanations, buildability section, layer control, transect instructions/clear/error, transect point readout, start/end labelling, collapsible hierarchy. |
| `apps/web/components/map/ContourOverlay.tsx` | 130 | **Replace.** Defects in §2.2. Also mixes Leaflet children with an absolutely-positioned HTML control inside `<MapContainer>`, against the codebase pattern. |
| `apps/web/components/map/ContourTransectTool.tsx` | 88 | **Replace.** No clear button, no instructional copy, no start/end differentiation, no error state, no keyboard path, confirm only via `dblclick`. |
| `apps/web/components/map/TransectOverlay.tsx` | 17 | **Replace.** Start and end markers are visually identical — a direct violation of the SME requirement. |
| `apps/web/lib/api/analysis.ts` (contour section, lines 103–182) | — | **Keep and extend.** `analyzeContour`, `analyzeTransect` and `getContourAnalysis` are correct and already produce a well-formed `ModuleResult`. |
| `apps/web/lib/stores/analysis.ts` (contour fields) | — | **Migrate** to a dedicated contour store (§6.2). |
| `apps/web/app/project/[id]/page.tsx` | 1011 | **Modify.** Contour wiring is duplicated verbatim across the detail branch (lines 547–567) and the overview branch (lines 869–889). |

### 2.2 Defects to fix, not carry forward

| # | Defect | Evidence |
|---|---|---|
| D-1 | **Hillshade is georeferenced from a single slope polygon.** `boundsFromGeojson` evaluates `data?.features?.[0]?.geometry?.coordinates ?? ...`; the left operand is always truthy, so the fallback is dead code and bounds come from feature `[0]` alone. The hillshade lands in the wrong place at the wrong scale. | `ContourOverlay.tsx:16-26, 35` |
| D-2 | **GeoJSON layers never update after mount.** react-leaflet's `<GeoJSON>` ignores `data` changes post-mount, and the code passes static keys (`key="slope"`, `key="contours"`). Re-running analysis at a new interval renders stale geometry. | `ContourOverlay.tsx:59, 71, 84` |
| D-3 | **Label anchors built by instantiating one `L.geoJSON` per feature** purely to read `.getBounds()` — O(n) Leaflet layer construction on every render, then a React `<Marker>` per label, with no zoom gating and no cap. | `ContourOverlay.tsx:37-51, 100-113` |
| D-4 | **Layer visibility is component-local state**, so it resets whenever the overlay unmounts (switching detail/overview, collapsing the module) and cannot be driven from the panel. | `ContourOverlay.tsx:33` |
| D-5 | **Default layer state is wrong.** Requirement: hillshade **on**, contours **on**, slope off, buildability off. Code has hillshade **off**. | `ContourOverlay.tsx:33` |
| D-6 | **Start and end transect markers are identical** — same radius, same colour, no labels. | `TransectOverlay.tsx:13-14` |
| D-7 | **HTTP status is lost on error.** `svcFetch` throws a bare `Error` carrying only `detail`, so the panel cannot distinguish 403 / 422 / 503 and cannot render the mandated per-status copy. | `lib/api/analysis.ts:57-80` |
| D-8 | **Transect failure is silently swallowed** — `runTransectAnalysis` catches and discards; the spinner stops and nothing else happens. | `lib/stores/analysis.ts:296-299` |
| D-9 | **No client-side 0.5 ha pre-check**, so small sites round-trip to a 422 before the user learns anything. `MultiPolygon` is also rejected by the page guard although the backend accepts it — low impact, since the product does not currently create MultiPolygons (`project/new/page.tsx:264-271`), but free to fix. | `app/project/[id]/page.tsx:411`; `services/contour/app/routers/contour.py:37-41` |
| D-10 | **Report has no contour visual.** `contour` is in `REPORT_MODULE_META` but `pickVisuals` has no case, so the report falls through to the generic first-chart branch. | `components/export/ReportDocument.tsx:31`; `ReportFeaturePage.tsx:58-72` |
| D-11 | **Export hardcodes interval 20**, ignoring the interval the user actually ran. | `app/project/[id]/export/page.tsx:131` |
| D-12 | **An ineligible project silently costs the user ~7 site-score points.** `contourUnavailableResult()` returns `score: 0`, `severity: "none"`, `error: null`, `loading: false`. `computeSiteScore` filters only on `!loading && !error`, so this synthetic result passes the filter and contributes a **0** to the mean across all resolved modules. A point project is scored as though its terrain were maximally bad. **Must be fixed in WP-8.** | `app/project/[id]/page.tsx:173-189`; `lib/api/analysis.ts:1626-1630` |

### 2.3 Backend facts the frontend must respect

Verified against service source, not the contract (the contract can drift — see the header comment at `lib/api/analysis.ts:4-6`).

- **Endpoints:** `GET /health` (also `GET /contour/health`), `POST /contour/analyze`, `POST /contour/transect`. Base URL from `NEXT_PUBLIC_CONTOUR_API_URL`, default `http://localhost:8010`.
- **Feature flag:** `feature.contour.analysis`, enforced in-process from the `FLAGS` env var. Missing → **403**, `detail: "Feature flag disabled: feature.contour.analysis"`. (`routers/contour.py:20, 27-30`)
- **Interval:** integer, `ge=10`, `le=60`. Out of range → **422** from Pydantic. (`models/contour.py:12-17`)
- **Warning:** returned **only** when `interval == 10`. (`routers/contour.py:65-69`)
- **Area gate:** below 0.5 ha → **422**, `"Site polygon too small for DEM analysis at 30m resolution"`. (`routers/contour.py:37-41`)
- **DEM failure:** → **503**, `"DEM fetch failed: ..."`. (`routers/contour.py:47-48`)
- **Polygon input:** accepts `Feature`, `FeatureCollection`, bare `Polygon`, or `MultiPolygon`. (`dem_service.py:55-68`)
- **Contour feature properties:** `elevation`, `is_index` (true every 5th interval), `color` (viridis ramp), `line_weight` (2 if index, else 1). (`contour_engine.py:97-106`)
- **Slope feature properties:** `slope_class`, `color`, `slope_range_label`. (`slope_engine.py:117-119`)
- **Buildability feature properties:** `buildability_class`, `color`. (`slope_engine.py:120-124`)
- **Transect:** samples every **5 m** along the line, projected into local UTM. Returns `distance_m`, `elevation_m`, `slope_pct`, `slope_class` per point — **no coordinates**. The frontend must interpolate positions itself (§6.5). (`transect_service.py:39-72`)
- **Hillshade raster extent:** the DEM is reprojected to local UTM, then `rasterio.mask(..., crop=True)` clips to the polygon. The PNG therefore covers the polygon's **UTM bounding box snapped to the 30 m pixel grid**, which can exceed the polygon's lat/lng bbox by up to one pixel per side. The response carries **no bounds**. See AD-5 and WP-0. (`dem_service.py:163-215`)
- **The transect endpoint re-runs the entire DEM pipeline.** `analyze_transect` calls the same `_analysis_arrays(request.polygon)` as `analyze_contour` — DEM fetch, reprojection, clip, slope, classification. A transect is therefore **exactly as slow and as failure-prone as a full analysis**, not a cheap follow-up query. This drives AD-17. (`routers/contour.py:87-89`)
- **`GET /health` is ungated and proves less than it appears.** It is registered outside the flag-checked router, so a 200 means only that the process is up. It does **not** indicate `feature.contour.analysis` is enabled. It *does* imply the GEE client initialised, because `initialize_gee_client()` runs in the FastAPI lifespan and raises on failure, preventing startup (`main.py:36-43`) — but a specific DEM fetch can still fail with 503. Drives AD-15.

### 2.4 Frontend facts that constrain the design

- **There is no circle geometry.** `project/new/page.tsx:264-271` stores a boundary of `Polygon` (when a shape was drawn) or `Point` (otherwise) — nothing else. The circle visible on the map is a **render-time buffer** of `bufferM` around a point (`project/new/page.tsx:314-315`, `SiteBoundaryOverlay shape="circle"`; same pattern at `project/[id]/page.tsx:518-520`), carrying a `TODO GH#55` marking it temporary. Eligibility must therefore treat point-plus-buffer as exactly the same case as a bare point. Drives AD-10.
- **Contour already auto-runs on project load** at a hardcoded interval of 20, alongside every other selected module (`page.tsx:301`). `modules_run` is the explicit set chosen at project creation (`project/new/page.tsx:273`). Drives AD-16.
- **Map click arbitration already has a convention.** `DrawTools` mirrors its internal tool mode into `useDrawStore.setMode` (`DrawTools.tsx:212`), and `MapClickHandler` yields with `if (mode) return;` (`MapClickHandler.tsx:17`). `DrawTools` binds `map.on("click")` whenever its own mode is `"poly"` (`DrawTools.tsx:434`). Any new click consumer that ignores this store will **double-fire** with polygon drawing. Drives AD-18.
- **Analysis requests use a 90 s client timeout with no cancel path** (`analysis.ts:110, 120`), and nothing is persisted — reopening a project calls `resetAnalysis()` and re-fetches everything, re-hitting GEE (`page.tsx:265-269`). Drives AD-20.
- **The report pipeline is static-SVG only.** `ReportFeaturePage` renders `SunPanel` and `RainfallRadar` as pure SVG and restricts itself to plain hex because html2canvas cannot parse `oklch` or CSS custom properties (`ReportFeaturePage.tsx:22-30`). A Leaflet map does not snapshot through this path. Drives AD-21.
- **No module anywhere in the frontend probes a service health endpoint.** A contour-only health chip would be the sole instance of the pattern. Drives AD-15.

---

## 3. Architecture Decisions

These are decided. Implement them as written.

**AD-1 — Feature folder, not scattered files.**
All contour UI moves into `apps/web/components/contour/` (panel side) and `apps/web/components/map/contour/` (map side), with shared logic in `apps/web/lib/contour/`. Precedent: `components/zoning/` already does exactly this. The four legacy files are deleted.
*Why:* the module is 15+ components; leaving them loose in `layout/` and `map/` does not scale and forces every new file to re-declare the slope palette.

**AD-2 — One store slice owns all contour state.**
New `apps/web/lib/stores/contour.ts` owns interval, run status machine, result, error, layer visibility, transect draft/result/status, and the active profile index. Contour fields are removed from `lib/stores/analysis.ts`. The `modules.contour` `ModuleResult` stays in the analysis store, because site scoring and the report read it.
*Why:* eliminates the duplicated wiring at `page.tsx:547-567` versus `869-889`, survives unmount (fixes D-4), and lets map and panel communicate without prop-drilling through `ProjectPage`.

**AD-3 — Graph-to-map scrub sync is imperative, never React state.**
`activeProfileIndex` lives in the contour store. The map cursor marker subscribes via `useContourStore.subscribe(selector, cb)` and calls `marker.setLatLng()` directly. The graph crosshair mutates an SVG `<g transform>` through a ref. Only the textual readout may use React state, and it must be coalesced with `requestAnimationFrame`.
*Why:* this is a documented repo gotcha — `CLAUDE.md` § "DOM-mutation overlays for mousemove-rate updates", and `DrawTools.tsx → renderMeasure()`. Pointer-rate React state updates visibly lag, and the requirement explicitly states the marker "should not lag behind the user's hover/scrub interaction."

**AD-4 — The transect profile chart is hand-built SVG, not Recharts.**
Recharts remains in use for the "Slope class share" bar chart via the existing `ModuleChart`.
*Why:* the profile needs pointer and keyboard scrubbing, an externally-driven active index, coloured Start/End endpoint anchors, a non-uniform x-domain, and an imperatively-mutated crosshair. Driving Recharts' internal tooltip state from outside is fragile across versions. The codebase already hand-builds bespoke SVG visuals (`SunPanel`, `RainfallRadar`, `FarGauge`, `SetbackPlanDiagram`), so this follows the established precedent, renders identically in the html2canvas report path, and adds no dependency.

**AD-5 — Two visuals require payload the API does not yet carry. Both get contract fields; both get an honest fallback.**

The requirements demand a hillshade "covering the analyzed polygon extent" and a map marker that tracks the graph. **Neither is derivable from the current `ContourResponse` / `TransectResponse`.** These are contract gaps, not frontend problems, and must not be papered over.

*AD-5a — `hillshade_bounds`.* Add optional `hillshade_bounds: [[south, west], [north, east]]` (WGS84) to `ContourResponse`. The frontend uses it when present, else falls back to the **site polygon's** lat/lng bbox — never the slope GeoJSON, which is defect D-1.
*Why:* the raster extent is a pixel-snapped UTM box the frontend cannot reconstruct. Guessing costs up to ~30 m of misregistration on a site that may be 100 m across.
*Fallback rule (binding):* when `hillshade_bounds` is absent, the hillshade legend must carry the caption `Approximate extent — may be offset by up to one DEM pixel (~30 m).` Silent approximation is not acceptable.

*AD-5b — transect point coordinates.* Add optional `lat` and `lng` to `TransectPoint`. The backend already holds the projected point inside the sampling loop; emitting WGS84 requires only an inverse transformer (`transect_service.py:41, 52`).
*Why:* the SME requirement "the marker position must correspond to the nearest profile point" is **only exactly satisfiable with coordinates**. Interpolating along the drawn line and matching haversine length against the backend's UTM length is an approximation.
*Fallback rule (binding):* when `lat`/`lng` are absent, use the interpolation locator (§6.5) and state the limitation in the graph caption: `Marker position is interpolated along the drawn line; start and end are exact.` The locator's endpoint-normalisation step guarantees that claim is true.

Both fields are additive, optional and backwards-compatible. Ship the frontend fallbacks regardless, so the UI is never blocked on the backend PR.

**AD-6 — Leaflet children and HTML chrome are separate components.**
`ContourMapLayers` renders **only** Leaflet children. Layer control, legend and map status render as **siblings of** `<MapContainer>`, not inside it.
*Why:* the codebase pattern — `FloodZoneRings` (Leaflet child, `page.tsx:531`) versus `FloodZoneOverlay` (HTML sibling, `page.tsx:586`). The current `ContourOverlay` puts an absolutely-positioned div inside the Leaflet tree, inheriting Leaflet's stacking context and fighting the map's event handling.

**AD-7 — Explicit Leaflet panes for deterministic stacking.**
Hillshade must sit beneath every vector. Use react-leaflet `<Pane>` with the fixed z-indices in §5.7. Do not rely on add-order.

**AD-8 — Canvas renderer for the polygon layers.**
`rasterio.features.shapes()` on a 30 m grid emits one polygon per contiguous same-class cell region — routinely thousands. Slope and buildability layers share one `L.canvas({ padding: 0.5 })` renderer instance. Contour lines use canvas when the feature count exceeds `MAX_SVG_FEATURES` (800) and SVG below it. Leaflet's canvas renderer still hit-tests, so tooltips keep working. Do **not** set `preferCanvas` on `MapContainer` — that would change rendering for `DrawTools`, `FloodZoneRings`, and every other overlay.

**AD-9 — Contour labels are zoom-gated, capped, and anchored from raw coordinates.**
Anchor = the middle vertex of the feature's own coordinate array (cheap; no Leaflet layer construction). Render only when `map.getZoom() >= LABEL_MIN_ZOOM` (16), only for `is_index` features, capped at `MAX_LABELS` (40) chosen longest-feature-first. All contours, index and regular, get a `sticky` hover tooltip.

**AD-10 — Eligibility is one shared function, and there is no "circle" case.**
`lib/contour/eligibility.ts` exports `deriveContourEligibility(project)` returning a discriminated union. It accepts `Polygon` **and** `MultiPolygon`, and pre-checks area ≥ 0.5 ha client-side so the "too small" message appears instantly rather than after a round trip.
**A circle is not a stored geometry** (§2.4) — it is a render-time buffer around a `Point`. The union therefore has **no `"circle"` member**; point-with-buffer and bare point are the same ineligible case, with one shared message. Do not invent a third type, and never auto-buffer a point into a polygon — the requirements explicitly forbid it.

**AD-11 — Honest progress, not fake progress.**
The backend reports no progress. The panel cycles the four recommended status lines on an elapsed-time schedule and labels them as typical stages, never as measured progress. Required by the repo rule "**Stubs must be honest**" in `CLAUDE.md`.

**AD-12 — Typed error mapping.**
`svcFetch` is extended to throw the existing `ApiError` (from `lib/api/client.ts`) carrying `status`. `lib/contour/errors.ts` maps `(status, detail)` to the exact copy in §7.4. No `catch {}` that discards (fixes D-8).

**AD-13 — User input is never destroyed by an error.**
A failed run keeps the interval, the drawn transect and the previous successful result on screen. Only explicit user actions (Clear transect, boundary deletion) discard state.

**AD-14 — Contour gets a real report page.**
Add a `contour` case to `ReportFeaturePage.pickVisuals` with a purpose-built static SVG hero, plus the mandated disclaimer sentence. Export reuses the store's interval when available (fixes D-10 and D-11).

**AD-15 — No health probe. Status is reactive, derived from the last real request.**
The frontend does not mirror `FLAGS` and does **not** call `GET /health`. The "service status" the requirements ask for is derived from the outcome of the last `/contour/analyze` or `/contour/transect` call: `unknown` (nothing attempted yet) → `ready` (a 2xx was seen) → `flag-disabled` (403) → `unreachable` (network failure) → `degraded` (503).
*Why:* `/health` is ungated and proves only that the process is up (§2.3). A green "online" chip followed by a 403 on Run is strictly worse than no chip. No other module in the app probes health, so this would also be a one-off pattern. Reactive status is honest, costs no request, and reuses the error mapping that must exist anyway (AD-12).

**AD-16 — Contour keeps auto-running on project load. The panel button is a re-run.**
Contour already auto-fetches at interval 20 alongside every other selected module (§2.4). That stays.
*Why:* it preserves parity with all 13 other modules, keeps `computeSiteScore` and the report working with no special-casing, and honours the `modules_run` set chosen at project creation. Making contour click-to-run would make it the only module that leaves a permanent hole in "n of m modules complete" (`page.tsx:371`) and would push GEE latency to a later, more surprising moment.
*Consequences the UI must handle:*
- The primary action is labelled **Run analysis** only until a result exists; thereafter **Re-run at {n} m** (§7.3).
- The interval selector shows the interval of the **current result**, not a pending choice. Changing it marks the result stale (a caption reading `Showing {old} m results — re-run to apply {new} m`) rather than silently disagreeing with the map.
- The initial auto-run uses `DEFAULT_INTERVAL` (20). The store is seeded with the same constant, so the selector and the first result always agree.
- Results are per-session (AD-20), so this costs one GEE DEM fetch per project open. That is the existing behaviour for every module; do not change it here, but flag persistence as follow-up work (§14 R-7).

**AD-17 — The transect requires a successful contour analysis. No pre-analysis drawing.**
The transect tool is disabled until `runStatus === "succeeded"`.
*Why:* this resolves a contradiction in the requirements (the tool is "disabled until contour analysis is available", then pre-analysis drawing is "allowed if copy explains a DEM fetch"). The deciding fact is §2.3: the transect endpoint re-runs the **entire** DEM pipeline. Pre-analysis drawing therefore offers a second path that is just as slow and just as failure-prone, with worse feedback and no layers on screen for the user to aim at. Because contour auto-runs (AD-16), a result normally exists before the user reaches the transect section, so the gate costs nothing in practice.
The disabled state must say why and what to do (§7.9 `transect.needsAnalysis`), never render as an inert button.

**AD-18 — Transect drawing takes exclusive map interaction through the existing draw store.**
`DrawTools` is always mounted on the project map and binds `map.on("click")` in polygon mode; `MapClickHandler` already yields via `useDrawStore.mode` (§2.4). The transect tool must join that protocol, not bypass it:
1. Add `"transect"` to the `DrawMode` union in `lib/stores/draw.ts`.
2. Activating the transect sets `useDrawStore.setMode("transect")`; clearing or finishing resets it to `null`.
3. `DrawTools` gains one guard: when the store mode is set and is not its own, it clears its internal `mode` and unbinds. Keep this to a single `useEffect` — do not restructure `DrawTools`.
4. `TransectDrawTool` binds click handlers **only** while the store mode is `"transect"`.
Without this, starting a polygon draw and then a transect makes every click add a vertex to both.

**AD-19 — The DSM and planning-level caveat lives on the live UI, not only in the report.**
The FVD is explicit that Copernicus GLO-30 is a **DSM** — it includes buildings and canopy — at ~30 m, suitable for planning-level screening only. The requirements place that disclaimer in the report alone. That is not sufficient next to a layer labelled **Non-Buildable: Regulated/Very Steep**, which reads as a regulatory finding but is a deterministic remap of slope class.
Required placements:
1. A persistent caption under the module blurb in the panel (§7.12 `caveat.dsm`).
2. A caveat line attached to the **buildability** section stating it is derived from slope class alone (§7.12 `caveat.buildability`).
3. A footnote in the map legend whenever the buildability or slope layer is visible.
This is the same standard the repo already applies in `CLAUDE.md` § "Stubs must be honest".

**AD-20 — Explicit timeout, cancel and persistence policy.**
- Timeout stays at 90 s (existing behaviour), surfaced in copy once past 30 s.
- Every run creates an `AbortController` held in the store. A **Cancel** button appears next to the running action and aborts it. An aborted run returns to the previous state — it is not an error.
- **No automatic retry.** Retry is always user-initiated, because each attempt is a billable GEE fetch.
- Results are **not persisted**; reopening a project re-fetches. State this in the panel footnote (§7.12 `caveat.session`) rather than letting users assume caching.

**AD-21 — The report visual is static SVG. Live-map snapshot is out of scope.**
`ContourReportVisual` is a pure SVG built from the result payload: the slope-class distribution bar plus, when present, the transect profile. Leaflet overlays do not snapshot through the html2canvas path (§2.4), so the requirements' "map image or layer snapshot **where supported**" is read as *not supported* here. Do not attempt a canvas capture of the map; a dedicated export renderer is separate, unscoped work (§14 R-8).

---

## 4. Target File Layout

```
apps/web/
├─ lib/
│  ├─ contour/
│  │  ├─ types.ts            # ContourResponse, TransectResponse, SlopeClass, BuildabilityClass, view models
│  │  ├─ constants.ts        # palettes, intervals, panes, thresholds, defaults
│  │  ├─ copy.ts             # §7 copy deck — every user-visible string
│  │  ├─ errors.ts           # mapContourError(status, detail) -> ContourErrorView
│  │  ├─ eligibility.ts      # deriveContourEligibility(project)
│  │  ├─ geometry.ts         # bbox, label anchors, distance->LatLng interpolation, cumulative lengths
│  │  ├─ format.ts           # pct(), metres(), elevation(), demSourceLabel()
│  │  └─ fixtures/           # dev-only sample payloads (WP-9)
│  ├─ stores/
│  │  └─ contour.ts          # NEW — the contour slice (AD-2)
│  └─ geo.ts                 # MODIFIED — promote polygonAreaM2 out of DrawTools
├─ components/
│  ├─ contour/               # NEW — panel-side UI
│  │  ├─ index.ts
│  │  ├─ theme.ts            # contour-scoped style constants (mirrors zoning/theme.ts)
│  │  ├─ ContourPanel.tsx
│  │  ├─ ContourEligibilityNotice.tsx
│  │  ├─ ContourServiceStatus.tsx
│  │  ├─ ContourRunControls.tsx
│  │  ├─ ContourIntervalSelector.tsx
│  │  ├─ ContourRunStatus.tsx
│  │  ├─ DemMetadataCard.tsx
│  │  ├─ SlopeStatsSection.tsx
│  │  ├─ AspectStatsSection.tsx
│  │  ├─ BuildabilitySection.tsx
│  │  ├─ TransectSection.tsx
│  │  ├─ TransectProfileChart.tsx
│  │  ├─ TransectSummary.tsx
│  │  ├─ TransectPointReadout.tsx
│  │  ├─ CollapsibleSubsection.tsx
│  │  ├─ StatTile.tsx
│  │  └─ InfoTip.tsx
│  ├─ map/
│  │  └─ contour/            # NEW — map-side UI
│  │     ├─ index.ts
│  │     ├─ ContourMapLayers.tsx        # Leaflet children only (AD-6)
│  │     ├─ ContourHillshadeLayer.tsx
│  │     ├─ ContourLinesLayer.tsx
│  │     ├─ ContourLabels.tsx
│  │     ├─ SlopeClassLayer.tsx
│  │     ├─ BuildabilityLayer.tsx
│  │     ├─ TransectDrawTool.tsx
│  │     ├─ TransectPathOverlay.tsx
│  │     ├─ TransectCursorMarker.tsx    # imperative, subscribes to store (AD-3)
│  │     ├─ ContourLayerControl.tsx     # HTML sibling
│  │     ├─ ContourLegend.tsx           # HTML sibling
│  │     └─ ContourMapStatus.tsx        # HTML sibling
│  └─ export/
│     ├─ ContourReportVisual.tsx        # NEW — static SVG hero for the report
│     └─ ReportFeaturePage.tsx          # MODIFIED — add contour case
└─ app/project/[id]/
   ├─ page.tsx                          # MODIFIED — single wiring, store-driven
   └─ export/page.tsx                   # MODIFIED — reuse stored interval

DELETE after migration:
  components/layout/ContourPanel.tsx
  components/map/ContourOverlay.tsx
  components/map/ContourTransectTool.tsx
  components/map/TransectOverlay.tsx
```

---

## 5. Design System Contract  (binding)

The SAT UI is a **warm, low-chroma architectural palette** — cream and sage surfaces, muted sage-grey text, saturated colour reserved exclusively for data. Contour UI must be indistinguishable in feel from the flood, wind and zoning modules.

### 5.1 Colour tokens — the only colours permitted for chrome

Defined in `apps/web/app/globals.css` under `@theme`. In Leaflet overlays and inline styles use the **hex literal** (the overlay pane sits outside Tailwind); in Tailwind class contexts use the token utility.

| Role | Hex | Tailwind | Used for |
|---|---|---|---|
| Brand primary | `#306223` | `brand-primary` | Start marker, score pill, active accents |
| Brand secondary | `#99CDD8` | `brand-secondary` | `Button` primary fill, focus ring |
| Brand secondary tint | `#DAEBE3` | `brand-secondary-tint` | Active chip, mint fills |
| Neutral bg | `#F2EDE8` | `neutral-bg` | Inner cards inside a panel section |
| Neutral surface | `#FDFCFB` | `neutral-surface` | Panel body, metric tiles, map HUD base |
| Neutral border | `#CFD6C4` | `neutral-border` | **Every** hairline border and divider |
| Text primary | `#3A3F3B` | `text-primary` | Values, headings, body |
| Text secondary | `#7B8F83` | `text-secondary` | Labels, captions, axis ticks |
| Text disabled | `#B8C4BB` | `text-disabled` | Placeholders, units, footnotes |
| Success | `#5A8F6A` / bg `#E4F0E8` | `semantic-success` | OK status, buildable tone |
| Warning | `#C4865A` / bg `#F8EDE0` | `semantic-warning` | Warnings, 10 m notice, ineligibility |
| Error | `#C46A6A` / bg `#F5E4E4` | `semantic-error` | Failures |
| Info | `#5B93C9` | `semantic-info` | Neutral informational |
| **Contour module accent** | **`#2D6A4F`** | — | Module identity colour, already fixed at `page.tsx:152`, `analysis.ts:24`, `ReportDocument.tsx:31`. Use for the module dot, section rules, profile line and chart series. |
| Amber secondary accent | `#B45309` | — | End marker only (borrowed from `zoning/theme.ts`) |

**Never introduce a new chrome colour.** Data colours are a separate, closed set.

### 5.2 Data palettes — mirrored from the backend, never invented

These must equal `services/contour/app/services/slope_engine.py:10-25`. Put them in `lib/contour/constants.ts` with a comment pointing at that file. The backend also ships `color` on every feature — **render map geometry from the feature's own `color` property**, and use these constants only for legends, chips and the report, where no feature is present.

```ts
export const SLOPE_CLASSES = [
  { id: "FLAT",       label: "Flat",       range: "0-5%",   color: "#2d6a4f", statKey: "flat_area_pct" },
  { id: "GENTLE",     label: "Gentle",     range: "5-10%",  color: "#52b788", statKey: "gentle_area_pct" },
  { id: "MODERATE",   label: "Moderate",   range: "10-15%", color: "#ffd166", statKey: "moderate_area_pct" },
  { id: "STEEP",      label: "Steep",      range: "15-25%", color: "#f4a261", statKey: "steep_area_pct" },
  { id: "VERY_STEEP", label: "Very steep", range: "25-33%", color: "#e76f51", statKey: "very_steep_area_pct" },
  { id: "HAZARD",     label: "Hazard",     range: ">33%",   color: "#c1121f", statKey: "hazard_area_pct" },
] as const;

export const BUILDABILITY_CLASSES = [
  { id: "BUILDABLE_FLAT",          label: "Buildable Flat",                           color: "#2d6a4f" },
  { id: "BUILDABLE_WITH_GRADING",  label: "Buildable With Grading",                   color: "#52b788" },
  { id: "CONSTRAINED_RETAINING",   label: "Constrained: Retaining/Engineering Needed", color: "#ffd166" },
  { id: "NON_BUILDABLE_REGULATED", label: "Non-Buildable: Regulated/Very Steep",      color: "#e76f51" },
  { id: "NON_BUILDABLE_HAZARD",    label: "Non-Buildable: Hazard",                    color: "#c1121f" },
] as const;
```

**Contrast rule:** `#ffd166` and `#52b788` fail text contrast on light surfaces. They are **fill-only**. Legend and chip text is always `#3A3F3B` on `#FDFCFB`; the colour appears solely as a swatch. Every legend row and every stat chip must also carry its text label and range, so nothing is distinguished by colour alone.

### 5.3 Typography

Font stack: `--font-sans` (Inter) for everything; `var(--font-geist-mono), monospace` **for numerals in headline positions only** — matching `HudCard.tsx:76`, `FloodZoneOverlay.tsx:66`, `AnalysisModuleSection.tsx:243`.

| Token | Size / weight / spacing | Use |
|---|---|---|
| `micro-label` | 9px · 600 · `letter-spacing: .5px` · uppercase · `#7B8F83` | Stat tile captions, legend group headers |
| `section-label` | 10px · 700 · `.5px` · uppercase · `#7B8F83` | "Slope Statistics", "Map Layers", "DEM" |
| `caption` | 10px · 500 · `#7B8F83` | Legend rows, helper text |
| `body-sm` | 11px · 400 · `line-height 1.55` · `#7B8F83` | Blurbs, summaries, instructions |
| `value-sm` | 11px · 700 · `#3A3F3B` | Metric tile values |
| `value-md` | 12–13px · 600 · `#3A3F3B` | Indicator values, sub-headers |
| `section-title` | 13px · 600–800 · `#3A3F3B` | Module and sub-section titles |
| `metric-lg` | 16px · 700 · mono · `#3A3F3B` | Prominent single figures |
| `hud-score` | 21–26px · 700 · mono | Map HUD headline number |

Do not use a size outside this table. Fractional sizes already in the codebase (`8.5`, `9.5`, `10.5`) are permitted **only** for dense map chrome, matching `MapToggle` and `ZoningMapLegend`.

### 5.4 Shape, spacing, elevation

| Property | Value | Where |
|---|---|---|
| Radius 6 | metric tile (`StatTile`) | matches the legacy `SmallMetric` |
| Radius 8 | inner card inside a panel section | `background:#F2EDE8; padding:10px 12px` |
| Radius 10 | module section, map HUD card | `AnalysisModuleSection`, `FloodZoneOverlay` legend |
| Radius 11–12 | glass pill, floating HUD | `MapToggle`, `HudCard` |
| Radius 999 | badges, buttons, chips | `StatusBadge`, `Button` |
| Panel gutter | `16px` | `RightPanel` body padding |
| Section stack gap | `12px` | vertical rhythm inside the contour panel |
| Grid gap | `6px` tiles · `8px` cards | |
| Inner card padding | `10px 12px` | |
| Map HUD padding | `9px 13px` compact · `11px 13px` legend | |
| Hairline | `1px solid #CFD6C4` | every divider |
| Panel shadow | none — borders only | |
| Map HUD shadow | `0 2px 12px rgba(0,0,0,0.14)` badge · `0 4px 18px rgba(0,0,0,0.12)` legend | |
| Glass pill | `background: rgba(253,252,251,0.78); backdrop-filter: blur(16px) saturate(160%); border: 1px solid rgba(255,255,255,0.6); box-shadow: 0 6px 22px rgba(58,63,59,0.16), inset 0 1px 0 rgba(255,255,255,0.45)` | copy exactly from `MapToggle.tsx` |

### 5.5 Component vocabulary — reuse, do not re-create

| Need | Use | Notes |
|---|---|---|
| Any button | `components/ui/Button.tsx` | variants `primary`/`secondary`/`ghost`/`danger`, sizes `sm`/`md`/`lg`. Panel actions use `size="sm"`. Built-in `loading` and `aria-busy`. |
| Panel switch | `components/ui/Toggle.tsx` | 24×44 track, `role="switch"` + `aria-checked` |
| Map glass switch | inline mini switch, 26×15 track, 11px knob | copy from `MapToggle.tsx:57-70`; used in `ContourLayerControl` rows |
| Status chip | `components/ui/StatusBadge.tsx` | severities `complete`/`needs-review`/`high`/`moderate`/`low`/`none` |
| Map toggle pill | `components/map/MapToggle.tsx` | reuse verbatim if a map-level open/close pill is needed |
| Standard chart | `components/layout/ModuleChart.tsx` | Recharts wrapper — use for "Slope class share" |
| Floating map card | pattern from `components/zoning/HudCard.tsx` | do not import it (amber-themed); replicate the shell with the contour accent |
| Class merging | `cn()` from `lib/utils.ts` | |

### 5.6 Motion

- Interactive state changes: `120–160ms ease`.
- Expand/collapse: `200ms ease-in-out` on `grid-template-rows: 0fr -> 1fr` (copy `AnalysisModuleSection.tsx:196-201`).
- Floating card entrance: `0.32s cubic-bezier(0.22,1,0.36,1)` fade plus 6px rise (copy `HudCard.tsx:52`).
- **No animation on the scrub cursor** — it must track the pointer 1:1.
- Respect `@media (prefers-reduced-motion: reduce)`: disable entrance and expand transitions.

### 5.7 Map stacking (z-index ladder)

Leaflet defaults: `tilePane 200`, `overlayPane 400`, `shadowPane 500`, `markerPane 600`, `tooltipPane 650`, `popupPane 700`.

| Pane name | z-index | Contents |
|---|---|---|
| `contour-hillshade` | **350** | Base64 PNG `ImageOverlay` — above tiles, below every vector (requirement) |
| `contour-fill` | **401** | Slope and buildability polygons |
| `contour-lines` | **402** | Contour LineStrings |
| `contour-transect` | **403** | Transect casing and line |
| default `markerPane` | 600 | Contour labels, transect vertex/Start/End markers, scrub cursor |

HTML siblings of the map, outside Leaflet:

| Element | z-index | Position |
|---|---|---|
| `ContourLegend` | 420 | bottom-centre, `bottom: 76px` (clears the `DrawTools` dock) |
| `ContourLayerControl` | 430 | top-right, `top: 84px` (below the 2D/3D toggle at `top: 14`) |
| `ContourMapStatus` | 430 | top-left, `top: 14px` |
| `TransectDrawTool` toolbar | 500 | top-left, `top: 72px` |

### 5.8 Panel information hierarchy (fixed order)

Inside the `Contour` `AnalysisModuleSection` body, in this order — matching the requirement's Visual Hierarchy section:

1. **Eligibility and service status** — a row of two indicators
2. **Run controls** — interval selector, Run button, status line, error
3. **DEM metadata** — 4-up tile grid plus warning banner
4. **Map layers** — 2×2 toggle grid, mirrors the map control; both write the same store
5. **Slope statistics** — stacked distribution bar plus 8 stats with `InfoTip`
6. **Aspect statistics** — 4 tiles plus one explanatory line
7. **Buildability** — legend rows with class labels
8. **Transect** — controls, summary, graph, point readout
9. **Advanced / debug** — collapsed by default (feature counts, sample count, raw DEM values)

Sections 5–9 are `CollapsibleSubsection`s. Default open: 3, 4, 5, 8. Default closed: 6, 7, 9. Nothing past section 2 renders until a successful run exists.

### 5.9 Anti-patterns — do not do these

- Hardcoding a user-visible string in a component (use `copy.ts`).
- A colour not in §5.1 or §5.2.
- `oklch()` or CSS custom properties in anything rendered into the report — html2canvas chokes; the report path is plain hex only (`ReportFeaturePage.tsx:22-30`).
- Absolutely-positioned HTML inside `<MapContainer>` children.
- React state driven at pointermove rate.
- `catch {}` that discards an error.
- Dot access on hyphenated CSS-module class names (see `apps/web/CLAUDE.md`).
- Distinguishing anything by colour alone.

---

## 6. Data and State Contracts

### 6.1 Types — `lib/contour/types.ts`

Move the `ContourResponse` and `TransectResponse` interfaces out of `lib/stores/analysis.ts` into this file and re-export them from the store for backwards compatibility, so no existing import breaks. Add:

```ts
export type SlopeClassId = (typeof SLOPE_CLASSES)[number]["id"];
export type BuildabilityClassId = (typeof BUILDABILITY_CLASSES)[number]["id"];

/** Added by the WP-0 contract addendum. Optional — always guard. */
export interface ContourResponse {
  // ...existing fields...
  hillshade_bounds?: [[number, number], [number, number]]; // [[S,W],[N,E]] WGS84
}

export type ContourLayerId = "hillshade" | "contours" | "slope" | "buildability";
export type ContourRunStatus = "idle" | "running" | "succeeded" | "failed" | "cancelled";
export type TransectStatus = "idle" | "drawing" | "ready" | "running" | "succeeded" | "failed";

/** Reactive, derived from the last real request outcome — never from /health (AD-15). */
export type ServiceStatus = "unknown" | "ready" | "flag-disabled" | "unreachable" | "degraded";

/** Added by the WP-0 contract addendum (AD-5b). Optional — always guard. */
export interface TransectPoint {
  distance_m: number;
  elevation_m: number;
  slope_pct: number;
  slope_class: SlopeClassId;
  lat?: number;
  lng?: number;
}

export interface ContourErrorView {
  title: string;      // short, from copy.ts
  detail?: string;    // optional backend detail, shown small
  recoverable: boolean;
  action?: "retry" | "adjust-interval" | "draw-polygon" | "contact-ops";
}
```

### 6.2 Store — `lib/stores/contour.ts`

```ts
interface ContourState {
  // configuration
  interval: number;                    // seeded from DEFAULT_INTERVAL (20) to match the auto-run (AD-16)
  intervalError: string | null;        // client-side validation, set before any request
  resultInterval: number | null;       // the interval the CURRENT result was produced at
  // -> `interval !== resultInterval` means "stale, re-run to apply" (AD-16)

  // service status — reactive only, never probed (AD-15)
  serviceStatus: ServiceStatus;

  // analysis
  runStatus: ContourRunStatus;
  runStartedAt: number | null;         // for the elapsed-time status copy (AD-11)
  abortController: AbortController | null;  // AD-20
  cancelRun: () => void;
  result: ContourResponse | null;
  error: ContourErrorView | null;
  resultNonce: number;                 // increments per successful run -> Leaflet layer keys (fixes D-2)

  // layers
  layers: Record<ContourLayerId, boolean>;  // default { hillshade: true, contours: true, slope: false, buildability: false }
  hillshadeOpacity: number;                 // default 0.45

  // transect
  transectStatus: TransectStatus;
  transectDraft: [number, number][];   // [lat, lng] vertices being drawn
  transectSubmitted: [number, number][]; // the line the current result belongs to
  transectResult: TransectResponse | null;
  transectError: ContourErrorView | null;
  activeProfileIndex: number | null;   // scrub sync (AD-3)

  // actions
  setInterval: (v: number) => void;
  toggleLayer: (id: ContourLayerId) => void;
  setLayers: (next: Partial<Record<ContourLayerId, boolean>>) => void;
  runAnalysis: (polygon: GeoJSONLike) => Promise<void>;
  /** True only when runStatus === "succeeded" — gates the transect tool (AD-17). */
  canDrawTransect: () => boolean;
  startTransect: () => void;
  addTransectPoint: (pt: [number, number]) => void;
  undoTransectPoint: () => void;
  clearTransect: () => void;
  runTransect: (polygon: GeoJSONLike) => Promise<void>;
  setActiveProfileIndex: (i: number | null) => void;
  resetForProject: () => void;         // called when the project id changes
}
```

**Rules for the store:**
- `runAnalysis` also writes `modules.contour` in the analysis store, via `getContourAnalysis`, so site scoring and the report keep working. Import the analysis store lazily inside the action, mirroring `analysis.ts:283`.
- On failure it sets `error` and leaves `result`, `interval`, and all transect state untouched (AD-13).
- `resultNonce` increments only on success and is the source of the Leaflet layer `key`s.
- `setActiveProfileIndex` must be callable at pointer rate. Keep it a bare `set` — no derived recomputation inside.
- Layer defaults reset to the required defaults on each successful run (hillshade on, contours on, slope off, buildability off), but not on a failed run.
- `serviceStatus` is written **only** from a request outcome (AD-15): 2xx → `ready`, 403 → `flag-disabled`, 503 → `degraded`, network/abort-without-cancel → `unreachable`. Never set it speculatively.
- `runAnalysis` and `runTransect` create an `AbortController`, store it, pass `signal` down through `svcFetch`, and clear it in `finally`. `cancelRun` aborts and sets `runStatus: "cancelled"` — **not** `"failed"`, and it must not populate `error` (AD-20).
- `setInterval` never mutates `resultInterval`. Only a successful run does.
- No action retries automatically (AD-20).

### 6.3 API layer changes — `lib/api/analysis.ts`

1. Extend `svcFetch` to throw `ApiError` (already exported from `lib/api/client.ts`) carrying `status` and the parsed `detail` message. Keep `message` formatting identical so existing callers are unaffected. Fixes D-7.
2. Extend `svcFetch` to accept an optional external `AbortSignal`, combined with its own timeout controller, so the store can cancel a run (AD-20). An abort triggered by the caller must be distinguishable from a timeout abort — timeout keeps the existing "Service timed out" message; caller-abort rethrows a sentinel the store maps to `cancelled`.
3. **Do not add a health probe.** `getContourHealth` is explicitly out of scope (AD-15).
4. `getContourAnalysis` gains an optional `interval` pass-through — already present; make the export page use it.

### 6.4 Eligibility — `lib/contour/eligibility.ts`

```ts
export type ContourEligibility =
  | { eligible: true;  polygon: GeoJSONLike; areaHa: number }
  | { eligible: false; reason: "no-boundary" | "point" | "too-small"; areaHa?: number };

export function deriveContourEligibility(project: Project | null): ContourEligibility;
```

- `Polygon` and `MultiPolygon` are eligible (D-9). Wrap as `{ type: "Feature", geometry }`.
- `Point` → `reason: "point"`. **This covers the on-map circle too** — the circle is a render-time buffer, not a stored geometry (AD-10, §2.4). There is deliberately no `"circle"` member; adding one would create a state that stored data can never produce.
- Area from `project.area_sqm` when present and > 0, else computed from the ring via `polygonAreaM2`.
- `areaHa < 0.5` → `reason: "too-small"`. Never auto-buffer a point into a polygon — the requirement forbids it.

### 6.5 Distance-to-position interpolation — `lib/contour/geometry.ts`

**Used only when the WP-0 `lat`/`lng` addendum (AD-5b) is unavailable.** When `points[i].lat` and `.lng` are present, use them directly and skip this entirely — that is the exact path, and the graph caption drops the interpolation disclaimer.

The backend otherwise returns profile points with `distance_m` but no coordinates, so the frontend must place the scrub marker itself.

```ts
export function buildProfileLocator(
  line: [number, number][],   // drawn vertices, [lat, lng]
  backendTotalM: number,      // TransectResponse.total_length_m
  distanceFn: (a: LatLng, b: LatLng) => number,  // pass map.distance
): (distanceM: number) => [number, number];
```

Algorithm:
1. Compute per-segment haversine lengths with the caller-supplied `distanceFn` and the cumulative array; call the sum `localTotal`.
2. Scale the query: `d' = distanceM * (localTotal / backendTotalM)`. The backend measures in projected UTM, the frontend in haversine — the ratio is within ~0.1% but scaling guarantees the endpoints land exactly on the drawn vertices.
3. Binary-search the cumulative array for the segment, then linearly interpolate lat/lng within it.

Build the locator once per transect result with `useMemo`; it must be a pure closure with no Leaflet dependency beyond the injected `distanceFn`.

Also in this file:
- `bboxOfPolygon(geojson): [[number,number],[number,number]]` — the hillshade fallback (AD-5), correctly walking **all** rings and **all** features (unlike D-1).
- `labelAnchor(feature): [number, number] | null` — middle vertex of the coordinate array, no Leaflet.
- `featureLength(feature): number` — vertex count, used to rank labels.

### 6.6 Also promote to `lib/geo.ts`

`polyAreaM2` currently lives privately in `components/map/DrawTools.tsx:46`. Move it to `lib/geo.ts` as `polygonAreaM2(pts: LatLng[]): number`, export it, and have `DrawTools` import it. Pure move — no behavioural change.

---

## 7. Copy Deck  (binding — `lib/contour/copy.ts`)

### 7.1 Module framing

| Key | String |
|---|---|
| `moduleTitle` | Contour Analysis |
| `moduleBlurb` | Terrain contours, slope classes, buildability zones and elevation profiles derived from Copernicus DEM GLO-30. Planning-level output for early site assessment. |
| `demSourceLabel` | Copernicus DEM GLO-30 2024 |
| `demSourceDetail` | DSM · ~30 m resolution · EGM2008 vertical datum |

### 7.2 Eligibility and service status

| Key | String |
|---|---|
| `eligibility.ok` | Polygon boundary detected |
| `eligibility.noBoundary` | Contour analysis requires a polygon site boundary. |
| `eligibility.point` | This project uses a point location with a display buffer, not a drawn boundary. Contour analysis requires a polygon site boundary — draw or select one to run it. |
| `eligibility.tooSmall` | This site is too small for reliable 30m DEM contour analysis. |
| `eligibility.tooSmallDetail` | Contour analysis needs at least 0.5 ha. This site is {area} ha. |

There is no `eligibility.circle` string — the on-map circle is a buffer around a point and uses `eligibility.point` (AD-10).

Service status is **reactive** (AD-15) and renders only in the non-ready states. There is no green "online" chip.

| Key | String |
|---|---|
| `service.flagDisabled` | Contour analysis is not enabled in this environment. |
| `service.unreachable` | Contour service unreachable. Check that the contour backend is running. |
| `service.degraded` | Terrain data could not be fetched on the last attempt. |

### 7.3 Interval selector

| Key | String |
|---|---|
| `interval.label` | Contour interval |
| `interval.hint` | 10 m to 60 m. 20 m recommended. |
| `interval.invalid` | Choose a contour interval between 10m and 60m. |
| `interval.minWarning` | Minimum reliable contour interval for Copernicus GLO-30 is 10m. |
| `run.first` | Run analysis |
| `run.again` | Re-run at {interval} m |
| `run.stale` | Showing {resultInterval} m results — re-run to apply {interval} m. |
| `run.cancel` | Cancel |
| `run.cancelled` | Analysis cancelled. Previous results are unchanged. |

The 10 m warning is **informative, not blocking** — render it as a warning-toned inline note, never disable Run because of it.

Because contour auto-runs on project load (AD-16), the primary action reads `run.first` only while no result exists; thereafter it reads `run.again`. When `interval !== resultInterval`, show `run.stale` in caption type beneath the selector — never let the selector silently disagree with what is drawn on the map.

### 7.4 Errors — exact mapping

| Trigger | `title` | `recoverable` | `action` |
|---|---|---|---|
| HTTP 403 | Contour analysis is not enabled in this environment. | false | `contact-ops` |
| HTTP 422, detail contains "too small" | This site is too small for reliable 30m DEM contour analysis. | false | `draw-polygon` |
| HTTP 422, detail mentions `contour_interval` | Choose a contour interval between 10m and 60m. | true | `adjust-interval` |
| HTTP 422, any other | Contour analysis could not run with the current inputs. | true | `retry` |
| HTTP 503 | Terrain data could not be fetched. Check the contour backend and Earth Engine configuration. | true | `retry` |
| Network failure / abort | Contour service unreachable. Check that the contour backend is running. | true | `retry` |
| Missing polygon (client-side) | Contour analysis requires a polygon site boundary. | false | `draw-polygon` |
| Transect line with fewer than 2 points | Draw a transect line with at least a start and end point. | true | `retry` |
| Any other | Contour analysis failed. | true | `retry` |

Always render the backend `detail` beneath the title in `caption` type when present — it is what makes ops debuggable — but never as the primary message.

### 7.5 Loading and progress (AD-11)

Cycle on elapsed time; hold the last line indefinitely:

| Elapsed | Line |
|---|---|
| 0–3 s | Fetching DEM data… |
| 3–10 s | Generating contour lines… |
| 10–20 s | Computing slope and buildability… |
| 20 s+ | Rendering terrain layers… |
| 30 s+ | append: `Large or steep sites can take up to 90 seconds.` |

Beneath, in `caption` type: `Typical stages — the service does not report exact progress.` The Run button shows its own `loading` state and is disabled for the duration (no duplicate submits). A **Cancel** button sits beside it throughout (AD-20). The map shows `ContourMapStatus` reading `Contour analysis running…`.

### 7.6 DEM metadata labels

`DEM Source` · `Resolution` · `Vertical RMSE` · `Contour Interval` · `Warning`

Values: source rendered as `Copernicus DEM GLO-30 2024` (never the raw `copernicus`), resolution as `30 m`, RMSE as `4.0 m`, interval as `{n} m`.

### 7.7 Slope statistic help text — verbatim, in `InfoTip`

| Statistic | Help text |
|---|---|
| Mean slope | Average terrain slope across the analyzed polygon. Useful for understanding the general grading burden of the site. |
| Maximum slope | Steepest sampled slope within the analyzed polygon. Useful for identifying localized terrain constraints. |
| Flat area | Share of the site with slope between 0-5%. Usually the most straightforward area for development. |
| Gentle area | Share of the site with slope between 5-10%. Often buildable, but may require grading or drainage attention. |
| Moderate area | Share of the site with slope between 10-15%. May affect road layout, foundation strategy, and stormwater movement. |
| Steep area | Share of the site with slope between 15-25%. Likely to need careful grading, retaining, or design constraints. |
| Very steep area | Share of the site with slope between 25-33%. Typically highly constrained. |
| Hazard area | Share of the site with slope greater than 33%. Should be treated as hazard-prone or generally unsuitable without specialist review. |

### 7.8 Aspect

| Key | String |
|---|---|
| `aspect.explanation` | Aspect describes the compass direction that slopes face. It can influence solar exposure, drainage, vegetation, and thermal behavior. |

Do not add copy implying aspect alone determines suitability.

### 7.9 Transect

| Key | String |
|---|---|
| `transect.start` | Start transect |
| `transect.stop` | Finish drawing |
| `transect.clear` | Clear transect |
| `transect.run` | Run transect |
| `transect.instructions` | Click along the site to place transect points, then run the profile. Two points minimum. Press Enter to finish, Backspace to remove the last point, Escape to cancel. |
| `transect.needsAnalysis` | Run contour analysis first — the transect samples the same terrain data. |
| `transect.cost` | Running a transect re-fetches DEM data and takes about as long as a full analysis. |
| `transect.empty` | No transect drawn yet. |
| `transect.running` | Sampling elevations along the transect… |
| `transect.interpolated` | Marker position is interpolated along the drawn line; start and end are exact. |
| `transect.startLabel` | Start |
| `transect.endLabel` | End |
| `transect.graphAria` | Elevation profile along the drawn transect. Use left and right arrow keys to move along the profile. |

### 7.10 Legends

| Key | String |
|---|---|
| `legend.contours` | Contours — {interval} m interval. Bolder lines are index contours, every {index} m. |
| `legend.hillshade` | Hillshade — shaded relief at {opacity}% opacity, drawn beneath all other layers. |
| `legend.slopeTitle` | Slope class |
| `legend.buildabilityTitle` | Buildability |
| `legend.hillshadeApprox` | Approximate extent — may be offset by up to one DEM pixel (~30 m). |

`legend.hillshadeApprox` renders only when `hillshade_bounds` is absent from the response (AD-5a).

### 7.11 Report disclaimer — mandatory, verbatim

> Contour analysis uses Copernicus DEM GLO-30 2024 at approximately 30m resolution. Outputs are planning-level and should be reviewed with site survey data for detailed design.

### 7.12 Live-UI caveats (AD-19) — required, not optional

The report disclaimer alone is insufficient. These appear in the live module.

| Key | Placement | String |
|---|---|---|
| `caveat.dsm` | Caption directly under the module blurb, always visible | Copernicus GLO-30 is a surface model — elevations include buildings and vegetation. Planning-level screening only; verify with a topographic survey. |
| `caveat.buildability` | Attached to the buildability section header, and as a legend footnote whenever the buildability layer is visible | Buildability classes are derived from slope gradient alone. They are not a regulatory determination and do not account for zoning, tenure, geology, or drainage. |
| `caveat.slopeLayer` | Legend footnote whenever the slope layer is visible | Slope is computed from 30 m DEM cells; features smaller than about 30 m are not resolved. |
| `caveat.session` | Panel footnote, caption type | Results are not saved. Reopening this project re-runs the analysis. |

These carry warning tone (`#C4865A` on `#F8EDE0`) when adjacent to buildability, and plain caption tone (`#7B8F83`) elsewhere. Do not bury them behind a collapsed section — `caveat.dsm` and `caveat.buildability` must be visible without expanding anything.

---

## 8. Work Packages

### WP-0 — Contract addendum and repo compliance  *(blocking; do this first)*

The repo mandates contract-first (`CLAUDE.md` § Non-Negotiable Rules #1, #3). Both fields (AD-5a, AD-5b) are additive and optional.

**Why this WP exists:** two of the requirement document's headline visuals — the hillshade overlay and the graph-to-map marker — cannot be produced correctly from the current payload. Without these fields the frontend can only approximate, and must say so in the UI. Ship the frontend fallbacks either way (AD-5), so the UI is never blocked on this PR.

Tasks:
1. `contracts/contour.yaml` — add `hillshade_bounds` to `ContourResponse.properties`:
   ```yaml
   hillshade_bounds:
     type: array
     nullable: true
     description: >
       WGS84 bounds of the hillshade PNG as [[south, west], [north, east]].
       The raster covers the polygon's UTM bounding box snapped to the DEM pixel
       grid, which the client cannot reconstruct from the polygon alone.
     items:
       type: array
       items: { type: number }
   ```
2. `contracts/CHANGELOG.md` — add a **new dated entry** with the next free aggregate version. Read the current top entry first; the version is monotonic across **all** services and parallel PRs collide (`CLAUDE.md` § Gotchas). CI requires the changelog to appear in the PR diff versus `main`.
3. `services/contour/app/models/contour.py` — add `hillshade_bounds: list[list[float]] | None = None` to `ContourResponse`.
4. `services/contour/app/routers/contour.py` — populate it. The bounds come from `dem["transform"]` and the clipped array shape, reprojected from the DEM CRS to EPSG:4326:
   ```python
   from rasterio.transform import array_bounds
   from rasterio.warp import transform_bounds
   h, w = dem["array"].shape
   west, south, east, north = transform_bounds(
       dem["crs"], "EPSG:4326", *array_bounds(h, w, dem["transform"])
   )
   hillshade_bounds = [[south, west], [north, east]]
   ```
5. `contracts/contour.yaml` — add `lat` and `lng` to `TransectPoint.properties` (AD-5b), both `type: number`, `nullable: true`, described as the WGS84 position of the sample.
6. `services/contour/app/models/contour.py` — add `lat: float | None = None` and `lng: float | None = None` to `TransectPoint`.
7. `services/contour/app/services/transect_service.py` — emit them. The sampling loop already holds the projected point; add an inverse transformer beside the existing forward one at line 41 and use it at line 52:
   ```python
   inverse_transformer = Transformer.from_crs(crs, "EPSG:4326", always_xy=True)
   # ...inside the loop, after `point = line.interpolate(float(distance))`:
   lon_wgs, lat_wgs = inverse_transformer.transform(point.x, point.y)
   ```
   Round to 6 decimal places (~0.1 m) to keep the payload small.
8. `tests/contour_smoke.py` — assert `hillshade_bounds` is present, is 2×2, and that `south < north` and `west < east`; assert every transect point carries finite `lat`/`lng` and that the first and last land within a small tolerance of the requested line's endpoints. Follow the existing per-file isolation pattern (`sys.path` self-insert plus `sys.modules.pop("app")` — `CLAUDE.md` § Tests).
9. `packages/flags/src/flags.py` — verify `CONTOUR_ANALYSIS` is present. It already is; no change expected.
10. `.env.example` — confirm `NEXT_PUBLIC_CONTOUR_API_URL=http://localhost:8010` exists. It does; no change expected.

**Definition of Done**
- [ ] `pytest tests/contour_smoke.py` passes.
- [ ] `ruff check services/ packages/flags/src/flags.py` clean.
- [ ] `contracts/CHANGELOG.md` has a fresh dated entry with a free version number.
- [ ] Both fields are optional everywhere; a client that ignores them still works.
- [ ] Payload size increase from `lat`/`lng` measured and noted in the PR — a 1 km transect at 5 m sampling is ~200 points, so the increase should be a few KB at most.

---

### WP-1 — Foundation: types, constants, copy, errors, geometry, store

No UI. This is the layer everything else imports.

Tasks:
1. Create `lib/contour/{types,constants,copy,errors,eligibility,geometry,format}.ts` per §5.2, §6, §7.
2. Create `lib/stores/contour.ts` per §6.2.
3. Remove contour fields from `lib/stores/analysis.ts` (`contourInterval`, `contourResult`, `contourLoading`, `contourError`, `transectResult`, `transectLoading`, `runContourAnalysis`, `runTransectAnalysis`, `setContourInterval`, `clearContourResults`) and the matching lines in `resetAnalysis`. Keep the `ContourResponse` / `TransectResponse` type re-exports so no import breaks.
4. Extend `svcFetch` in `lib/api/analysis.ts` to throw `ApiError` with `status` (AD-12, fixes D-7) and to accept an external `AbortSignal` for cancellation (AD-20). **Do not add a health probe** (AD-15).
5. Promote `polyAreaM2` from `DrawTools.tsx` into `lib/geo.ts` as `polygonAreaM2` and update the import in `DrawTools`.
6. `components/contour/theme.ts` — freeze the inline-style constants from §5 (`tile`, `innerCard`, `sectionLabel`, `caption`, `hairline`, `hudCard`, `glassPill`) so no component re-declares them.

**Definition of Done**
- [ ] `npx tsc --noEmit` clean.
- [ ] Every string in §7 exists in `copy.ts`, referenced by key.
- [ ] `mapContourError` has a unit-style exercise covering every row of §7.4 (a dev script under the scratchpad is fine; do not add a test framework).
- [ ] `deriveContourEligibility` handles `Polygon`, `MultiPolygon`, `Point`, `null`, and the sub-0.5 ha case.
- [ ] No component imports contour geometry or palette logic from anywhere but `lib/contour/`.

---

### WP-2 — Panel shell: eligibility, service status, run controls

Files: `ContourPanel.tsx`, `ContourEligibilityNotice.tsx`, `ContourServiceStatus.tsx`, `ContourRunControls.tsx`, `ContourIntervalSelector.tsx`, `ContourRunStatus.tsx`, `CollapsibleSubsection.tsx`, `StatTile.tsx`, `InfoTip.tsx`.

Requirements covered: Module Availability, Control Panel, Interval Selector, Loading and Progress, Error states.

Notes:
- `ContourPanel` is rendered as `moduleSpecificContent` on the `Contour` `AnalysisModuleSection` — the same slot `FloodRiskPanel` and `SunPanel` use (`page.tsx:967-1000`). It receives no contour data as props; it reads the contour store. It receives only `result?: ModuleResult` and `eligibility` from the page.
- **`caveat.dsm` renders directly under the module blurb and is always visible** (AD-19), before any conditional content.
- **Run semantics follow AD-16.** Contour auto-runs on load, so on first paint the panel is usually already in `succeeded` with a 20 m result. The action button reads `run.first` only while no result exists, otherwise `run.again`. When `interval !== resultInterval`, render `run.stale` beneath the selector.
- **A Cancel button sits beside the action while `runStatus === "running"`** (AD-20). Cancelling returns to the prior state and shows `run.cancelled` — it is not an error and must not populate the error slot.
- **`ContourServiceStatus` is reactive and renders nothing in the `ready` and `unknown` states** (AD-15). It is not a green "online" chip and must not call `/health`.
- When ineligible, render `caveat.dsm` plus **only** `ContourEligibilityNotice` — a `#F8EDE0` / `#C4865A` card stating the reason, what is required, and what to do. It must be visible in the panel, not hidden behind a missing button (explicit requirement). Point projects and point-plus-buffer projects share one message (AD-10).
- `ContourIntervalSelector`: a `<select>` of 10/20/30/40/50/60 is the primary control (matches the backend's discrete useful range and needs no free-text validation). If free numeric entry is added, validate client-side and set `intervalError` **before** dispatching — never wait for the 422.
- `InfoTip` is the accessibility-critical primitive. Build it once, correctly: a `<button type="button">` trigger with `aria-describedby`, opening on hover **and** focus **and** click/tap, closing on `Escape` and blur, with the content in a `role="tooltip"` element. Hover-only is explicitly insufficient.
- `ContourRunStatus` owns the elapsed-time copy cycle (§7.5) with a single interval timer cleaned up on unmount.

**Definition of Done**
- [ ] Point projects (with and without the display buffer) show the disabled state with the point copy; the Run button is absent, not merely disabled-looking.
- [ ] `caveat.dsm` is visible without expanding anything, in both the eligible and ineligible states.
- [ ] Interval 10 shows the warning note and Run stays enabled.
- [ ] Run is disabled while `runStatus === "running"`; double-clicking issues one request.
- [ ] Cancel aborts an in-flight run, restores the prior result, and shows `run.cancelled` with no error styling.
- [ ] Changing the interval after a run shows `run.stale` and relabels the button `run.again`; the map still shows the old result until re-run.
- [ ] No `/health` request is issued anywhere (verify in the Network tab).
- [ ] Every §7.4 error renders its mapped title, with `detail` in caption type beneath.
- [ ] A failed run leaves the previous result and the interval untouched.
- [ ] Full keyboard traversal: Tab reaches interval, Run, Cancel, and every `InfoTip`; `InfoTip` opens on focus and closes on `Escape`.

---

### WP-3 — Results: DEM metadata, slope, aspect, buildability

Files: `DemMetadataCard.tsx`, `SlopeStatsSection.tsx`, `AspectStatsSection.tsx`, `BuildabilitySection.tsx`.

Requirements covered: DEM Metadata Display, Slope Statistics (with hoverable explanations), Aspect Statistics, Buildability legend.

Notes:
- `DemMetadataCard`: 2×2 `StatTile` grid (Source, Resolution, Vertical RMSE, Contour Interval) plus a full-width warning row when `dem_metadata.warning` is set. Source label is humanised (§7.6) — never print `copernicus`.
- `SlopeStatsSection`: a single stacked distribution bar (14px tall, radius 4, segments in `SLOPE_CLASSES` order using the class colours) above a 2-column grid of the 8 statistics. **Every one** of the 8 carries an `InfoTip` with the verbatim §7.7 text. Give the stacked bar `role="img"` with an `aria-label` enumerating the class shares, since it is a colour-only visual.
- Reuse `ModuleChart` for a "Slope class share" bar chart — `getContourAnalysis` already emits that chart spec (`analysis.ts:145-158`), so read it from the `ModuleResult` rather than rebuilding it.
- `BuildabilitySection`: one row per `BUILDABILITY_CLASSES` entry with swatch, UI label from §5.2, and the share derived from the matching slope classes. Because the backend derives buildability deterministically from slope class, state that provenance in caption type rather than implying an independent computation.

**Definition of Done**
- [ ] All 8 slope statistics render with correct values and units.
- [ ] All 8 `InfoTip`s carry the exact §7.7 strings.
- [ ] Buildability labels match §5.2 exactly.
- [ ] The stacked bar has an accessible text equivalent.
- [ ] Sections 6 and 7 are collapsed by default; 3, 4 and 5 are open.

---

### WP-4 — Map layers

Files: `ContourMapLayers.tsx`, `ContourHillshadeLayer.tsx`, `ContourLinesLayer.tsx`, `ContourLabels.tsx`, `SlopeClassLayer.tsx`, `BuildabilityLayer.tsx`.

Requirements covered: Map Layer Requirements, Hillshade, Contour Lines, Contour Labels, Slope Layer, Buildability Layer.

Notes:
- Declare the four `<Pane>`s from §5.7 in `ContourMapLayers`, once.
- **Every** GeoJSON layer takes `key={`${layerId}-${resultNonce}`}` (fixes D-2).
- Style callbacks read `feature.properties.color`, `.line_weight`, `.is_index` — the backend's own values (§2.3). Fall back to the palette constants only when a property is missing.
- Hillshade: `<ImageOverlay>` with `url={`data:image/png;base64,${hillshade_png_b64}`}`, bounds from `hillshade_bounds` when present else `bboxOfPolygon(sitePolygon)` (AD-5), `opacity` from the store (default 0.45), `interactive={false}`, in the `contour-hillshade` pane. It is an overlay, never a basemap.
- Slope and buildability: shared `L.canvas({ padding: 0.5 })` instance created once with `useMemo` and passed as `renderer` in `pathOptions` (AD-8). `weight: 0.8`, `fillOpacity: 0.42`, `opacity: 0.8`. Bind a tooltip showing `slope_range_label` / the buildability UI label — not the raw enum.
- Contour lines: index contours get `weight: line_weight` and `opacity: 1`; regular get `opacity: 0.7`. Bind a `sticky` tooltip `${elevation} m` to every contour.
- `ContourLabels`: index contours only, persistent, `${elevation} m`, zoom-gated at `LABEL_MIN_ZOOM = 16`, capped at 40, ranked by vertex count, anchored via `labelAnchor()` (AD-9, fixes D-3). Subscribe to the map's `zoomend` to re-evaluate the gate — and heed the `CLAUDE.md` Leaflet gotcha: labels appended outside `.leaflet-map-pane` freeze during zoom animation. These are `L.divIcon` markers inside `markerPane`, so they animate correctly; do **not** move them to `map.getContainer()`.
- Layers mount and unmount from `store.layers`, so visibility survives navigation (fixes D-4). Defaults per D-5.

**Definition of Done**
- [ ] Four layers toggle independently; state persists across detail/overview switching and module collapse.
- [ ] Hillshade renders beneath all vectors and aligns with the site polygon.
- [ ] Re-running at a different interval fully replaces the rendered geometry.
- [ ] Labels appear only at zoom ≥ 16, never exceed 40, and do not jump during zoom animation.
- [ ] Hovering any contour shows its elevation in metres.
- [ ] With 5,000+ slope polygons, pan and zoom stay interactive.

---

### WP-5 — Map chrome: layer control, legend, status

Files: `ContourLayerControl.tsx`, `ContourLegend.tsx`, `ContourMapStatus.tsx`.

Requirements covered: layer visibility clarity, Layer Legend Requirements, map-level pending indication.

Notes:
- All three are **siblings of** `<MapContainer>` (AD-6), positioned per §5.7.
- `ContourLayerControl`: glass card (§5.4) with four rows, each a mini switch plus label plus a small colour cue. Every row is a real `<button role="switch" aria-checked>`. It writes the same store as the panel's layer grid, so the two stay in lockstep.
- `ContourLegend`: renders a block per **visible** layer only. Hidden layers are omitted or shown collapsed and dimmed. Contour block shows interval and the index-contour explanation; hillshade block shows the opacity explanation; slope and buildability blocks show swatch, label and range rows.
- `ContourMapStatus`: appears while `runStatus === "running"` or `transectStatus === "running"`, using the compact HUD style. This satisfies "a map-level indication that outputs are pending."

**Definition of Done**
- [ ] Toggling in the panel updates the map control and vice versa.
- [ ] The legend reflects exactly which layers are visible and updates immediately.
- [ ] Everything is reachable and operable by keyboard, with visible focus.
- [ ] Nothing overlaps the `DrawTools` dock, the `MapSearch` field, or the 2D/3D toggle at any viewport ≥ 1280 px.

---

### WP-6 — Transect: drawing and map rendering

Files: `TransectDrawTool.tsx`, `TransectPathOverlay.tsx`.

Requirements covered: Transect Tool Requirements, Transect Line Map Requirements, clear Start and End points.

Notes:
- Tool state lives in the store (`transectStatus`, `transectDraft`), so the toolbar, the panel controls and the map all agree.
- **Gating (AD-17):** the tool is disabled until `runStatus === "succeeded"`. There is no pre-analysis drawing. The disabled state renders `transect.needsAnalysis` explaining why, never an inert button. Once enabled, show `transect.cost` so the user knows a transect is as expensive as a full analysis.
- **Exclusive map interaction (AD-18) — do not skip this.** `DrawTools` is always mounted and binds `map.on("click")` in polygon mode, so a transect tool that binds clicks independently will double-fire. Implement all four steps of AD-18:
  1. Add `"transect"` to the `DrawMode` union in `lib/stores/draw.ts`.
  2. `TransectDrawTool` sets `setMode("transect")` on activate and `setMode(null)` on finish, clear or cancel — including on unmount.
  3. `DrawTools` gains **one** `useEffect`: when the store mode is non-null and not its own, clear its internal `mode`. Do not restructure `DrawTools` beyond this.
  4. `TransectDrawTool` binds click handlers only while the store mode is `"transect"`.
- **2D only.** The 3D view replaces the Leaflet map with `Scene3D` and has no contour layers. In the overview branch the existing `{!view3D && ...}` wrapper already handles this; make sure the derived visibility flag in WP-8 also carries `&& !view3D` so no contour chrome renders over the 3D scene.
- Drawing interactions: click adds a vertex; `Enter` finishes; `Backspace` removes the last vertex; `Escape` cancels and restores the previous submitted line. Keep `dblclick` as a convenience but never as the only path.
- Visual treatment (`contour-transect` pane):
  - White casing polyline underneath, `weight: 5`, `opacity: 0.9` — keeps the line legible over hillshade.
  - Transect line on top: `color: "#3A3F3B"`, `weight: 3`, `dashArray: "8 7"`.
  - While drawing, add a rubber-band segment from the last vertex to the cursor at reduced opacity — this is the "clear selected/active visual state".
  - Intermediate vertices: `CircleMarker`, `radius: 4`, white fill, `#3A3F3B` stroke, `weight: 2`.
  - **Start**: filled circle, `radius: 7`, fill `#306223`, white stroke `weight: 2`, plus a permanent `Start` tooltip.
  - **End**: filled **diamond** (`L.divIcon` with a 45°-rotated square), fill `#B45309`, white stroke, plus a permanent `End` tooltip.
  - Non-colour-only distinction is satisfied by shape plus the text labels — required.
- Toolbar (top-left, z-index 500): point count, Finish, Clear, Cancel. Real buttons with `aria-label`s, not icon-only divs.

**Definition of Done**
- [ ] Start and end are distinguishable by shape, colour **and** label.
- [ ] The tool is disabled with an explanatory message until an analysis has succeeded.
- [ ] **Starting a polygon draw, then starting a transect, adds each click to exactly one of them** — never both. Test this explicitly in both orders.
- [ ] Leaving transect mode restores normal map click behaviour, including `MapClickHandler`.
- [ ] Enter / Backspace / Escape all work; a keyboard-only user can complete a transect.
- [ ] Clearing removes line, markers, result and readout together.
- [ ] Redrawing in the opposite direction updates the line and clears the stale result.
- [ ] The line stays legible over the hillshade at every zoom.

---

### WP-7 — Transect: profile graph, scrub sync, summary

Files: `TransectSection.tsx`, `TransectProfileChart.tsx`, `TransectSummary.tsx`, `TransectPointReadout.tsx`, `TransectCursorMarker.tsx`.

Requirements covered: Transect Graph, map marker follows graph, start/end consistency, Transect Summary. **This is the highest-risk work package — build it last and test it hardest.**

`TransectProfileChart` specification:
- Hand-built responsive SVG (AD-4). `viewBox="0 0 W H"`, `width: 100%`, `preserveAspectRatio="none"` avoided — use a fixed aspect and let the container size it.
- X axis: distance in metres, `0` at left, `total_length_m` at right. Y axis: elevation in metres, domain padded 5% beyond min/max.
- Profile line: `#2D6A4F`, `stroke-width: 2`, `stroke-linejoin: round`, plus a subtle fill beneath at `rgba(45,106,79,0.10)`.
- Grid: horizontal only, `#CFD6C4`, matching `ModuleChart`'s convention.
- Axis ticks: `9px`, `#7B8F83`.
- **Endpoint anchors**: a `#306223` dot with a `Start` label at the left edge and a `#B45309` diamond with an `End` label at the right edge — the same colours and shapes as the map markers. Left is always the transect start; right is always the end. Redrawing reverses accordingly, because the point array follows the drawn direction.
- Min, max and relief are annotated on the plot: a dashed horizontal rule at min and at max, each labelled.
- Crosshair: a single `<g ref>` containing a vertical rule and a dot, moved by mutating `transform` (AD-3). Never re-rendered through React.
- Interaction:
  - `pointermove` / `pointerdown` on an invisible full-height capture `<rect>`: map the x offset to the nearest point index, call `setActiveProfileIndex`, mutate the crosshair transform.
  - `pointerleave`: clear the index.
  - Keyboard: `tabIndex={0}`, `role="img"` with `aria-label` from `transect.graphAria`; `ArrowLeft`/`ArrowRight` step one sample, `Shift` plus arrow steps ten, `Home`/`End` jump to the ends. Announce the active point through an `aria-live="polite"` region — this is the required non-hover equivalent.

`TransectCursorMarker` (map side):
- A single `CircleMarker` created once, held in a ref, in `markerPane`.
- Subscribes to `useContourStore.subscribe(s => s.activeProfileIndex, ...)`. Position resolution, in priority order (AD-5b):
  1. `points[i].lat` / `.lng` when present — exact, no caveat.
  2. Otherwise `locator(points[i].distance_m)` from §6.5 — interpolated. The graph then renders the `transect.interpolated` caption.
  Hidden by setting radius 0 or removing from the map when the index is `null`.
- **No React re-render on scrub.** Verify with React DevTools Profiler.

`TransectPointReadout`: distance from start, elevation, slope percentage, slope class — all four are required. Coalesce updates with `requestAnimationFrame`.

`TransectSummary`: total length (m), min elevation (m), max elevation (m), relief (m), DEM source, and sample count. Place it **immediately above** the graph so the values obviously describe the current transect.

**Definition of Done**
- [ ] Scrubbing the graph moves a marker along the map line, tracking the pointer with no perceptible lag.
- [ ] The graph's active point and the map marker always refer to the same sample.
- [ ] The readout shows distance, elevation, slope % and slope class.
- [ ] Left equals Start, right equals End, with matching colours and shapes on both map and graph.
- [ ] Reversing the transect reverses the graph.
- [ ] Arrow-key scrubbing works and the active point is announced to screen readers.
- [ ] React DevTools Profiler shows **zero** component re-renders during a scrub, apart from the readout.
- [ ] Transect failure surfaces a mapped error and preserves the drawn line.

---

### WP-8 — Page wiring and export/report

Files: `app/project/[id]/page.tsx`, `app/project/[id]/export/page.tsx`, `components/export/ReportFeaturePage.tsx`, `components/export/ContourReportVisual.tsx`.

Tasks:
1. **De-duplicate the wiring.** Replace both contour blocks (`page.tsx:547-567` and `869-889`) with one `<ContourMapLayers />` plus the transect components, rendered when `contourVisible` — a single derived boolean, `(detailModule === "contour" || expanded.contour) && !view3D` (AD-18, 2D only). Map chrome (WP-5) renders as a sibling under the same condition.
2. Compute `eligibility` once with `deriveContourEligibility(project)` and pass it to `ContourPanel`. Delete the ad-hoc `contourPolygon` derivation at `page.tsx:411`.
3. Delete the local `transectActive` / `transectPositions` state (`page.tsx:224-225`) — the store owns both now.
4. Call `resetForProject()` when the project id changes. **Do not add a health probe** (AD-15).
5. Keep the existing auto-run at `page.tsx:301` (AD-16), but source the interval from the store's `DEFAULT_INTERVAL` instead of the literal `20`, and use `deriveContourEligibility` for the guard rather than the inline `type === "Polygon"` check. On success the store records `resultInterval`, so the selector and the map agree from first paint.
6. **Fix D-12 — the ineligible-module scoring bug.** `contourUnavailableResult()` currently returns `score: 0` with `error: null`, and `computeSiteScore` filters only on `!loading && !error` (`analysis.ts:1626-1630`), so an ineligible contour module drags the site average down by a full zero. Correct approach: **do not register a `ModuleResult` at all** for an ineligible project — the panel already renders the eligibility notice from `eligibility`, so the synthetic result serves no purpose. Remove the `contourUnavailableResult` branch from the fetcher list and delete the function. Then verify `module_progress.total` (`page.tsx:371`) still reads sensibly; if contour is in `modules_run` but ineligible, subtract it from the total rather than leaving a permanently incomplete count.
7. **Report:** add a `contour` case to `pickVisuals` (`ReportFeaturePage.tsx:58-72`) returning `<ContourReportVisual result={result} />` as the hero and the slope-share chart as the primary chart.
8. `ContourReportVisual`: a static SVG — the slope class distribution bar with labels, plus the transect profile when a transect result exists. **Plain hex only, no CSS variables, no `oklch`** (html2canvas constraint, `ReportFeaturePage.tsx:22-30`). No interactivity, no store reads; everything comes in through props. **Do not attempt a live-map snapshot** (AD-21) — "map image or layer snapshot where supported" is read as not supported through this pipeline, and is explicitly out of acceptance.
9. Add DEM metadata, slope stats, aspect stats and the buildability summary to the report page body, the §7.11 disclaimer verbatim in footnote type, and `caveat.buildability` beside the buildability summary (AD-19 applies to the report as well as the live UI).
10. `export/page.tsx:131`: replace the hardcoded `20` with the stored `resultInterval`, falling back to `DEFAULT_INTERVAL`.

**Definition of Done**
- [ ] Only one contour wiring block exists in `page.tsx`.
- [ ] Toggling between overview and detail preserves layer state, transect and results.
- [ ] Contour chrome never renders over the 3D scene.
- [ ] An ineligible project no longer contributes a 0 to the site score; verify the score before and after the D-12 fix on a point project.
- [ ] `module_progress` reads sensibly for a project whose `modules_run` includes an ineligible contour.
- [ ] The report renders a contour page with metadata, slope, aspect, buildability, both caveats, and the transect profile when present.
- [ ] PDF export succeeds with no html2canvas colour-parsing errors.
- [ ] The four legacy files and `contourUnavailableResult` are deleted, and nothing imports them.

---

### WP-9 — Hardening: fixtures, QA pass, docs  *(optional fixtures, mandatory QA)*

1. **Dev fixtures** (optional but strongly recommended — GEE credentials are not always available). Capture one real `/contour/analyze` and one `/contour/transect` response into `lib/contour/fixtures/`. **Replace `hillshade_png_b64` with a tiny placeholder PNG** so the fixture stays small. Serve them when `NEXT_PUBLIC_CONTOUR_FIXTURES=1`, gated inside the API module so no fixture code reaches a production bundle.
2. Run the full manual QA script in §11.2.
3. Update `apps/web/CHANGELOG.md` and add a Frontend Patterns note to `apps/web/CLAUDE.md` capturing the two reusable lessons: the react-leaflet `data`-after-mount gotcha (D-2) and the store-subscribe imperative marker pattern (AD-3).
4. Update `docs/feature-validation/SAT-19_contour-analysis.md` — add frontend acceptance criteria mapped to the components that satisfy them.

---

## 9. Accessibility Specification

Every item is a requirement, not a nice-to-have.

| Area | Requirement |
|---|---|
| Keyboard | Every control reachable by Tab in visual order. No keyboard traps. Visible focus everywhere — reuse `focus-visible:ring-2 focus-visible:ring-brand-secondary` from `Button.tsx`. |
| `InfoTip` | Opens on hover **and** focus **and** click/tap. Closes on `Escape` and blur. `aria-describedby` links trigger to content. Hover-only is explicitly insufficient. |
| Layer toggles | `role="switch"` with `aria-checked`, and an accessible name that includes the layer name. |
| Graph | `tabIndex={0}`, `role="img"`, descriptive `aria-label`. Arrow keys scrub; `Home`/`End` jump to ends. Active point announced through `aria-live="polite"`. |
| Map markers | Start and end carry permanent text labels; `aria-label` on marker elements where Leaflet allows. |
| Colour | Nothing distinguished by colour alone. Slope and buildability legends always show the text label plus range. Start and End differ by shape as well as colour. |
| Contrast | Text meets 4.5:1 against its own background. `#ffd166` and `#52b788` are fill-only, never text colours. |
| Status | Run status uses `role="status"`; errors use `role="alert"`. |
| Loading | Buttons set `aria-busy` (already handled by `Button`). |
| Motion | Honour `prefers-reduced-motion` for entrance and expand transitions. |

---

## 10. Performance Budget

| Metric | Budget | How |
|---|---|---|
| Layer first paint after a response | < 500 ms for ≤ 5,000 features | Canvas renderer (AD-8), no per-feature Leaflet layer construction (AD-9) |
| Scrub frame cost | < 16 ms | Imperative marker and crosshair (AD-3); zero React re-renders except the rAF-coalesced readout |
| Contour label count | ≤ 40 | Zoom gate plus longest-first ranking |
| Re-render on layer toggle | Only the toggled layer | Per-layer components subscribing to their own store slice |
| Bundle | No new runtime dependency | Hand-built SVG (AD-4); fixtures dev-gated |
| Hillshade payload | Not re-decoded on every render | Memoise the data URL against `resultNonce` |

Guard against pathological responses: if `slope_geojson.features.length > 20000`, render the layer but show a caption noting that geometry has been simplified for display, and skip tooltips on that layer.

---

## 11. Verification Plan

There is no JS test runner in `apps/web` (`package.json` has no jest or vitest). **Do not add one as part of this work** — verification is static checks plus a scripted manual pass.

### 11.1 Static gates (every WP)

```bash
cd apps/web
npx tsc --noEmit
npm run lint
npm run build
```

Backend gates for WP-0:

```bash
ruff check services/ packages/flags/src/flags.py
pytest tests/contour_smoke.py
```

### 11.2 Manual QA script

Start the backend with the flag enabled — every gated endpoint 403s without it:

```bash
cd services/contour
FLAGS=feature.contour.analysis uvicorn app.main:app --reload --port 8010
```

`tests/testUI.html` is a standalone backend probe; use it to confirm the service returns sane data before debugging the React UI.

| # | Scenario | Expected |
|---|---|---|
| 1 | Polygon project, interval 20, Run | All four layers render; hillshade aligns with the boundary; metadata populates |
| 2 | Interval 10 | Warning note shows; Run stays enabled; response warning surfaces in metadata |
| 3 | Re-run at 40 | Geometry fully replaced, not stacked (D-2) |
| 4 | Point project (with the on-map buffer circle) | Disabled state with the point copy; no Run button; **site score does not include a contour 0** (D-12) |
| 5 | Open a polygon project fresh | Contour auto-runs at 20 m; the selector reads 20 m; no `run.stale` caption |
| 6 | Polygon < 0.5 ha | "Too small" message appears immediately, with no network request |
| 7 | Backend stopped | "Service unreachable"; the previous result stays on screen |
| 8 | Backend started without `FLAGS` | 403 copy: "Contour analysis is not enabled in this environment." No `/health` request is ever issued |
| 9 | Toggle each layer | Map and legend update; panel and map controls stay in sync |
| 10 | Collapse and re-expand the module | Layer state, result and transect all preserved |
| 11 | Switch to detail view and back | Same — no reset, no duplicate layers |
| 12 | Draw a 2-point transect, run | Line, Start, End, graph and summary all render |
| 13 | Scrub the graph | Map marker tracks with no perceptible lag; readout shows all four fields |
| 14 | Arrow-key scrub | Same behaviour; active point announced |
| 15 | Redraw the transect reversed | Graph direction flips; Start/End swap on both map and graph |
| 16 | Clear transect | Line, markers, graph, summary and readout all cleared together |
| 17 | Transect with the backend down | Mapped error; the drawn line is preserved |
| 18 | Export to PDF | Contour report page renders with metadata, stats, disclaimer and profile |
| 19 | Keyboard-only pass | Every control reachable and operable; focus always visible |
| 20 | Zoom out below 16 | Contour labels disappear; no jumping during the zoom animation |
| 21 | Change interval to 40 without re-running | `run.stale` caption appears; button reads "Re-run at 40 m"; the map still shows the 20 m result |
| 22 | Cancel a run mid-flight | Request aborts; previous result intact; `run.cancelled` shown; no error styling |
| 23 | Start polygon draw, then start transect | Clicks go to exactly one tool. Repeat in the reverse order |
| 24 | Exit transect mode | Normal map click behaviour returns |
| 25 | Try the transect before any analysis | Tool disabled with `transect.needsAnalysis`, not an inert button |
| 26 | Switch to 3D with contour expanded | No contour layers, legend or layer control render over the 3D scene |
| 27 | Confirm the live caveats | `caveat.dsm` and `caveat.buildability` visible without expanding any section |
| 28 | Run against a backend without the WP-0 fields | Hillshade shows `legend.hillshadeApprox`; graph shows `transect.interpolated`; both still function |

Record results in the PR description as a checklist.

**Agent playbook (executable):** `docs/SAT-19_contour-frontend-agent-qa.md` — same 65 cases as step-by-step browser instructions (setup, selectors, verbatim copy, network rules, results log). Use that file if an agent will drive the UI.

---

## 12. Repo Process Compliance

From `CLAUDE.md` § Non-Negotiable Rules:

1. **Contract-first** — WP-0 updates `contracts/contour.yaml` and `contracts/CHANGELOG.md` **before** any service code. CI fails the PR otherwise.
2. **Flag-default-off** — `feature.contour.analysis` already exists in `packages/flags/src/flags.py` and is enforced in-process. No new flag needed. The frontend must degrade gracefully when the flag is off (403 path).
3. **One feature per PR** — split this work into at most two PRs: `feat/contour-backend-hillshade-bounds` (WP-0) and `feat/contour-frontend` (WP-1 to WP-9). Do not bundle unrelated refactors; the `polyAreaM2` move and the `svcFetch` status change are in-scope enablers and must be called out in the PR description.
4. **No direct push to `main`** — branch, PR, one review, green CI. The current branch is `feat/contour-analysis`.
5. **No secrets in committed files** — never commit `gee-sa.json`, a `.env`, or any token. Fixtures must contain no credentials and no real project data.
6. **Merge `main` before merging** — a branch forked before a sibling merged ships a stale copy of that sibling. Verify sibling files are byte-identical to `main` before merge (`CLAUDE.md` § Gotchas).
7. **`contracts/CHANGELOG.md` version numbers are a shared monotonic counter** across all services. Pick the next free one when rebasing; if a sibling PR merged your entry, add a fresh dated entry so the file still appears in the diff.
8. Run `/security-review` before merging.

---

## 13. Traceability Matrix

Requirement section → implementation → work package.

| Requirement (`Contour_Frontend_UI_Requirements.md`) | Implementation | WP |
|---|---|---|
| Module Availability — polygon | `eligibility.ts`, `ContourPanel` | 1, 2 |
| Module Availability — point (incl. buffer circle) disabled state | `ContourEligibilityNotice`, AD-10 | 2 |
| Control Panel (title, blurb, status, eligibility, interval, run, loading, error, summary) | `ContourPanel`, `ContourRunControls`, `ContourServiceStatus`, `ContourRunStatus` | 2 |
| Contour Interval Selector + 10 m warning | `ContourIntervalSelector`, `copy.ts` | 2 |
| DEM Metadata Display | `DemMetadataCard` | 3 |
| Map Layer Requirements + default state | `ContourMapLayers`, `ContourLayerControl`, store defaults | 4, 5 |
| Hillshade Layer | `ContourHillshadeLayer`, `hillshade_bounds` | 0, 4 |
| Contour Line Layer + labels | `ContourLinesLayer`, `ContourLabels` | 4 |
| Slope Layer + legend | `SlopeClassLayer`, `ContourLegend` | 4, 5 |
| Buildability Layer + legend | `BuildabilityLayer`, `BuildabilitySection`, `ContourLegend` | 3, 4, 5 |
| Slope Statistics + hoverable explanations | `SlopeStatsSection`, `InfoTip`, `copy.ts` §7.7 | 2, 3 |
| Aspect Statistics | `AspectStatsSection` | 3 |
| Transect Tool (start/clear/confirm, instructions, loading, error) | `TransectDrawTool`, `TransectSection` | 6, 7 |
| Transect Line Map (dashed, start/end, vertices, active state) | `TransectPathOverlay` | 6 |
| Transect Graph (axes, line, labels, min/max/relief/length) | `TransectProfileChart` | 7 |
| Map Marker Follows Graph | `TransectCursorMarker`, `buildProfileLocator`, AD-3 | 1, 7 |
| Start/End consistency on graph | `TransectProfileChart` endpoint anchors | 7 |
| Transect Summary | `TransectSummary` | 7 |
| Error and Empty States + recommended copy | `errors.ts`, `copy.ts` §7.4 | 1, 2 |
| Loading and Progress | `ContourRunStatus`, `ContourMapStatus` | 2, 5 |
| Layer Legend Requirements | `ContourLegend` | 5 |
| Report and Export Requirements + disclaimer | `ContourReportVisual`, `ReportFeaturePage` | 8 |
| Accessibility Requirements | §9, `InfoTip`, graph keyboard support | 2, 3, 7 |
| Visual Hierarchy Requirements | §5.8 panel order, `CollapsibleSubsection` | 2, 3 |

Requirement acceptance criteria (the doc's final section) map one-to-one onto the Definition-of-Done boxes in WP-2 through WP-8.

---

## 14. Risks and Open Questions

| # | Risk | Mitigation |
|---|---|---|
| R-1 | GEE credentials unavailable during frontend development | WP-9 fixtures; `tests/testUI.html` as a backend probe |
| R-2 | WP-0 contract fields rejected in review | Both frontend fallbacks ship regardless (AD-5). The cost is an approximate hillshade and an interpolated marker, each of which **must** then carry its disclosure caption |
| R-3 | Slope GeoJSON larger than expected on hilly sites | Canvas renderer plus the 20,000-feature guard in §10 |
| R-4 | Scrub sync regresses under future refactors | Document the pattern in `apps/web/CLAUDE.md` (WP-9 item 3) and assert it in the QA script |
| R-5 | Contract version collision with a parallel PR | Pick the next free version at rebase time (`CLAUDE.md` § Gotchas) |
| R-6 | Report page breaks html2canvas | Plain hex only in `ContourReportVisual`; verify with a real PDF export in QA step 18 |
| R-7 | Auto-run means a GEE DEM fetch on every project open, at up to 90 s | Accepted for parity with all other modules (AD-16). **Follow-up work, not in this scope:** persist contour results per project so reopening does not re-fetch. Raise as a separate ticket |
| R-8 | Stakeholders expect a map image in the report | AD-21 explicitly excludes it. If a map snapshot is genuinely required, it needs a dedicated export renderer — separate, unscoped work |
| R-9 | AD-18 touches `DrawTools`, which is shared and fragile | Keep the change to a single `useEffect`; QA steps 23–24 cover the regression surface |

**Open questions for the product owner — do not block on these; implement the stated default and flag it in the PR:**

1. **Free numeric interval entry?** Default implemented: a discrete `<select>` of 10/20/30/40/50/60. The requirement permits free input with client-side validation; the select removes an entire class of validation error and matches the backend's useful range.
2. **Hillshade opacity — user-adjustable or fixed?** Default implemented: fixed at 0.45, exposed in the store so a slider can be added later without refactoring.
3. **Should `run.stale` block interaction?** Default implemented: no — it is an informational caption. The map keeps showing the last real result rather than clearing, because a blank map is worse than a labelled stale one.

**Previously open, now resolved** (see §15): auto-run versus manual run → AD-16. Pre-analysis transect drawing → AD-17. Service health indicator → AD-15. Circle eligibility → AD-10.

---

## 15. Revision Log

### rev-2 — external spec review incorporated

An external review flagged eight areas where the plan assumed data or product behaviour the SAT stack does not have. All eight were verified against the codebase; all eight were valid, with one nuance corrected. Verification also surfaced a ninth defect the review did not catch.

| Review point | Verified? | Resolution |
|---|---|---|
| Hillshade has no bounds in the payload | Yes — `dem_service.py:163-215` | Already covered by AD-5a; strengthened with a **binding disclosure caption** when the field is absent |
| Transect points have no coordinates | Yes — `transect_service.py:63-70` | **Escalated to a contract field** (AD-5b) rather than left as frontend interpolation; interpolation retained as a disclosed fallback |
| Auto-run conflicts with the manual run flow | Yes — `page.tsx:301` auto-fetches at a hardcoded 20 | **AD-16** — auto-run retained for module parity; the button becomes a re-run; stale-interval state defined |
| "Circle project" is not a geometry type | Yes — `project/new/page.tsx:264-271` stores only `Polygon` or `Point`; the circle is a `bufferM` render overlay with a `TODO GH#55` | **AD-10** — the `"circle"` eligibility member is removed; point and point-plus-buffer share one message |
| A green "service online" chip will be wrong | Yes — `/health` is ungated (`main.py:71-73`); no other module probes health | **AD-15** — health probe dropped entirely; status is reactive from the last request outcome |
| Live UI overclaims what a DSM can say | Yes — FVD states DSM, ~30 m, planning-level; the disclaimer was report-only | **AD-19** — caveats required on the live panel, the buildability section, and the map legend |
| Transect gating contradicts itself; drawing will collide with `DrawTools` | Yes — the transect endpoint re-runs `_analysis_arrays` (`routers/contour.py:87`); `DrawTools` binds `map.on("click")` in poly mode (`DrawTools.tsx:434`) | **AD-17** (analysis required first) and **AD-18** (exclusive mode via the existing draw store) |
| Report "map snapshot" does not match the export pipeline | Yes — html2canvas path is static-SVG and plain-hex only | **AD-21** — static SVG only; map snapshot explicitly out of acceptance |
| No product rule for long GEE runs | Yes — 90 s timeout, no cancel, no persistence | **AD-20** — cancel via `AbortController`, no auto-retry, session-only results disclosed in copy |

**Nuance corrected:** the review states `/health` "does not mean Earth Engine can fetch a DEM." Partially true. `initialize_gee_client()` runs in the FastAPI lifespan and raises on failure, so a serving process implies the GEE client **did** initialise (`main.py:36-43`). What `/health` genuinely cannot tell you is whether the feature flag is enabled or whether a *specific* DEM fetch will succeed. The conclusion stands; the reasoning is recorded accurately in §2.3.

**Found during verification, not in the review — D-12.** `contourUnavailableResult()` returns `score: 0, severity: "none", error: null`, and `computeSiteScore` filters only on `!loading && !error` (`analysis.ts:1626-1630`). The synthetic "unavailable" result therefore passes the filter and contributes a **zero** to the site-score mean. Every point project is currently scored as though its terrain were maximally bad. Fixed in WP-8 item 6.
