# idk/yolo Branch — Build Handover

**Branch:** `idk/yolo` off `main`
**Stack:** Next.js 16 · React 19 · deck.gl v9 · MapLibre GL · Zustand v5
**Working dir:** `/Volumes/LocalDrive/SAT/apps/web/`
**Date:** 2026-06-11

---

## What Was Built

Full urban analysis map application ported from [Axon-City](https://github.com/raynbowy23/Axon-City) into the SAT monorepo frontend, with all 5 SAT backend services wired in alongside.

---

## Feature Inventory

### 1. Map Canvas — `components/MapView.tsx`

- **Base tiles:** MapLibre GL with CARTO free tiles (dark/light/satellite). No API key required.
- **Rendering:** deck.gl v9 on top of MapLibre. All vector layers rendered as deck.gl `GeoJsonLayer`, `ScatterplotLayer`, `LineLayer`, `PolygonLayer`.
- **View control:** Controlled `viewState` from local React state (`localViewState`). DeckGL never switches between controlled/uncontrolled mode — see Bug #1 below.
- **Layer loading indicator:** Spinner + % progress bar at bottom centre while Overpass fetches.
- **"+ Compare Area" button:** Appears after polygon is drawn and Overpass finishes. Saves the polygon + its layer snapshot to `areas[]` for comparison.

### 2. Polygon Drawing — `hooks/usePolygonDrawing.ts` + `components/DrawingTool.tsx`

- Click to add points, double-click to close (or press "✓ Done" button).
- 5px pointer drag threshold distinguishes clicks from pans — prevents accidental points during map drag.
- Undo last point button.
- Cancel clears in-progress drawing.
- On completion: polygon saved to **both** `selectionPolygon` (active analysis target) and `drawings[]` (persistent list).
- Auto-name: "Area 1", "Area 2", etc.

### 3. Saved Drawings List — `components/ControlPanel.tsx` (Drawings tab)

- All completed polygons persist in Zustand + localStorage.
- Inline rename by clicking the name field.
- Click a drawing row → sets it as the active `selectionPolygon` → re-triggers analysis.
- Delete button (×) on hover.
- Badge on tab shows count.
- All drawings render on the map simultaneously; selected drawing highlighted (higher opacity border).

### 4. OSM Layer System — `data/layerManifest.ts` + `utils/osmFetcher.ts`

28 layers across 6 groups:

| Group | Layers |
|---|---|
| Environment | Water Bodies, Parks & Green, Vegetation, Trees |
| Land Use | Buildings (extruded), Residential, Commercial, Industrial, Agricultural |
| Infrastructure | Primary Roads, Secondary Roads, Local Roads, Bike Lanes, Railways |
| Access & Transit | Bus Stops, Metro Stations, Pedestrian Paths |
| Traffic | Traffic Lights, Parking, Crossings |
| Amenities | Food & Dining, Shopping, Healthcare, Education, Entertainment, Banks & ATMs, Places of Worship, Post & Services |

**Overpass batching:** All visible layers fetched in 2 parallel requests (geo batch + points batch) instead of N sequential requests. Single combined Overpass QL query per batch with `out body geom qt;` (quadtile sort — faster). Cache keyed by bbox; cleared on new polygon. 3-endpoint failover with exponential backoff.

### 5. Layer Controls — `components/DraggableLayerList.tsx` + `components/ControlPanel.tsx`

- **Drag-to-reorder** via `@dnd-kit/sortable`. Layer order affects z-index rendering.
- **Toggle visibility** (click name, strikes through when hidden).
- **Solo mode** (◎ button on hover) — isolates one layer, hides all others.
- **Per-layer opacity slider** (appears on hover).
- **Global opacity slider** in panel header.
- **Camera presets** (3D tab): Top / Axono / Horizon / Street — adjusts pitch + bearing.
- **Group spacing / layer spacing sliders** for 3D exploded view.

### 6. 3D Exploded View — `components/ExtractedView.tsx`

- Activated by "3D" button in top bar. Replaces MapView with an OrbitView.
- Each OSM layer rendered at a z-offset calculated from `groupIndex × groupGap × explodedGroupRatio + intraIndex × layerHeight × explodedIntraGroupRatio`.
- Coordinates normalised to metres-scale centred on Bangalore origin (hardcoded — see Known Issues).
- Material lighting: ambient 0.2 / diffuse 0.8.
- Drag to rotate, scroll to zoom, shift+drag to pan.
- Group legend top-right (only shows groups that have loaded data).

### 7. Urban Metrics — `components/MetricsPanel.tsx` + `utils/metrics.ts`

Visible when Metrics tab is active in RightPanel. Computed from Overpass `layerData`:

- **Area** (km²) — shoelace formula with latitude cosine correction.
- **POI Density** — total amenity POIs / area km².
- **Building Density** — building footprint count / area km².
- **Green Space Ratio** — sum of park + vegetation + water polygon areas / total area. Colour-coded: green >20%, yellow >10%, red otherwise.
- **POI Diversity** — Shannon entropy index normalised to [0,1] across amenity categories. Label: Low / Moderate / High.
- **Category breakdown bar chart** — top 6 amenity types sorted by count.

### 8. SAT Backend Analysis — `utils/satApi.ts` + `hooks/useSatAnalysis.ts`

Fires on polygon completion (immediately, not blocked by Overpass). All 8 calls via `Promise.allSettled` — partial failure doesn't kill the panel.

| Service | Port | Endpoints called |
|---|---|---|
| Temperature | 8000 | `GET /weather/climate-archive` · `POST /weather/thermal-grid` |
| SunPath | 8001 | `GET /sunpath/annual` · `GET /sunpath/events` · `GET /sunpath/orientation` · `GET /sunpath/diagram.svg` |
| Flood | 8002 | `POST /flood/analyze` |
| Wind | 8003 | `POST /wind/analyze` |
| Rainfall | 8004 | `GET /rainfall/archive` |

Backend URLs via env vars: `NEXT_PUBLIC_TEMP_API_URL`, `NEXT_PUBLIC_SUNPATH_API_URL`, `NEXT_PUBLIC_FLOOD_API_URL`, `NEXT_PUBLIC_WIND_API_URL`, `NEXT_PUBLIC_RAINFALL_API_URL`. Default to `localhost:800{0-4}`.

Analysis panel tabs:

- **Climate** — monthly max/min temperature bars + precipitation bars. Source: Open-Meteo ERA5.
- **Sun** — SVG sun path diagram from backend · sunrise/solar noon/sunset times · recommended orientation + shading strategy.
- **Flood** — risk category badge (Very Low → Very High) · overall score · breakdown: elevation risk, hydrology risk, historical risk, LLAI risk.
- **Wind** — dominant direction compass · comfort level (Excellent/Good/Fair/Poor) · avg speed m/s · load risk.
- **Rainfall** — monthly total mm + rainy days (panel exists in `RainfallPanel.tsx`).

### 9. Area Comparison — `components/ComparisonTable.tsx`

- "Compare Area" button saves active polygon + its OSM layer snapshot to `areas[]`.
- Comparison table visible in Metrics tab when ≥1 area saved.
- Columns: name, area km², buildings/km², green %.
- Click row to set active area. × to remove.

### 10. Search Bar — `components/SearchBar.tsx`

- Nominatim geocoding. No API key. 400ms debounce.
- Selecting a result calls `setFlyTo(...)` in store → MapView picks it up → smooth `FlyToInterpolator` (800ms, speed 1.5).
- Does NOT call `setViewState` directly (was the root cause of Bug #1 — see below).

### 11. Export — `components/ExportDialog.tsx`

- **PDF** — jsPDF landscape A4. Includes location, date, area km², layer feature counts.
- **CSV** — all features with layer, osm_id, geometry type, name, lat, lon.
- **GeoJSON** — full FeatureCollection per layer, JSON download.
- **Share URL** — encodes viewState + mapStyle + visible layers in URL hash, copies to clipboard.

### 12. State Management — `store/index.ts`

Zustand v5 with `persist` middleware. Persisted fields (localStorage, key `sat-map-store`):

```
mapStyle · layerVisibility · globalOpacity · favoriteLocations · drawings · selectedDrawingId
```

Non-persisted (reset on reload): `viewState` (only persisted for restore), `selectionPolygon`, `satResults`, `layerData`, `flyTo`, `areas`.

`skipHydration: true` — hydration deferred to `StoreHydrator` component (client-side `useEffect`) to avoid Next.js SSR mismatch.

---

## Architecture Decisions

### DeckGL Camera — Always Controlled

DeckGL uses `viewState={localViewState}` (controlled mode) exclusively. `localViewState` is React component state in `MapView`. `onViewStateChange` updates it immediately at 60fps — no Zustand involved during pan/zoom.

Zustand `viewState` is only written by a 1000ms debounced timer, for persistence on reload. It is NOT used to drive DeckGL directly.

Programmatic navigation (SearchBar, future agents) goes through `store.flyTo`, never `store.viewState`.

### OSM Fetch vs Analysis Decoupling

SAT analysis and right panel open fire immediately when `selectionPolygon` is set. OSM layer fetch is independent and updates `layerData` when Overpass responds. Metrics panel shows area immediately; layer-derived metrics fill in when Overpass finishes.

### Polygon State (V3 Pattern)

Mirrors `Site-Analysis-Tool/src/hooks/useMapStore.ts`. Each completed polygon is saved to `drawings[]` with id, name, geometry, area, style, createdAt. `selectDrawing(id)` sets both `selectedDrawingId` and `selectionPolygon` atomically, re-triggering analysis.

---

## Bugs Found & Fixed

### Bug 1 — Map frozen after first interaction (root cause: controlled/uncontrolled DeckGL toggle)

**Symptom:** After the first pan or search, the map would snap back and become unresponsive.

**Root cause:**
1. User pans → `onViewStateChange` debounce → `setViewState()` updates Zustand
2. `useEffect([viewState.lat, viewState.lon])` detects change → sets local `flyTarget` state → DeckGL switches to controlled mode
3. User pans again → `isDragging` detected → `setFlyTarget(null)` → DeckGL reverts to uncontrolled with `initialViewState` (Bangalore hardcoded)
4. Map snaps to Bangalore. Cannot recover.

**Fix:** Removed the `initialViewState`/`flyTarget` toggle entirely. DeckGL is now always controlled from `localViewState` (React state). `flyTo` in Zustand store is a dedicated one-shot command channel for programmatic navigation only.

**Files changed:** `store/index.ts`, `components/SearchBar.tsx`, `components/MapView.tsx`

---

### Bug 2 — Analysis panel not picking up drawn polygon

**Symptom:** After drawing a polygon, right panel showed "Draw a polygon to load data."

**Root cause:** `runAnalysis(selectionPolygon)` and `setRightPanelOpen(true)` were inside the Overpass `.then()` callback. Overpass frequently fails (rate limits, 429s, timeouts). When it failed, `.catch()` ran instead and analysis was never triggered.

**Fix:** Both calls moved immediately after `selectionPolygon` check in the `useEffect`, before the Overpass fetch. OSM fetch continues independently in the background.

**File changed:** `components/MapView.tsx`

---

### Bug 3 — Hydration mismatch on SSR

**Symptom:** React hydration error on initial page load. Console: `Hydration failed because the server rendered HTML didn't match the client.`

**Root cause:** Zustand `persist` middleware reads localStorage on client, returns different values than server-rendered defaults.

**Fix:** `skipHydration: true` in persist config. Added `StoreHydrator` component that calls `useMapStore.persist.rehydrate()` inside `useEffect` (client-only). MapView and ExtractedView dynamically imported with `ssr: false`.

**Files changed:** `store/index.ts`, `components/StoreHydrator.tsx`, `app/map/page.tsx`

---

### Bug 4 — Map jumping to wrong location on load

**Symptom:** On first interaction after page load, map jumped to a different location.

**Root cause:** SearchBar was calling `setViewState({...viewState, lat, lon})` which spread the full store `viewState`. On initial load, store `viewState` had defaults (Bangalore). After rehydration from localStorage, `viewState` could have a different lat/lon. The spread caused inconsistent merging.

**Fix:** SearchBar now calls `setFlyTo({ lat, lon, zoom, pitch: 0, bearing: 0 })` — clean target, no spread from current viewState.

---

### Bug 5 — Slow OSM layer loading (7 Overpass requests)

**Symptom:** Loading 28 layers took 30–60s with sequential requests. Each request hit rate limits.

**Fix:** Batched into 2 parallel requests — one for geo layers (polygon/line), one for points. Single combined Overpass QL query per batch. Added `out body geom qt;` (quadtile sort). Bbox-level cache so re-selecting same polygon is instant. 3-endpoint failover.

**File changed:** `utils/osmFetcher.ts`

---

### Bug 6 — TypeScript: `Map` import name collision

**Symptom:** `import Map from 'react-map-gl/maplibre'` shadowed the native JS `Map` constructor. `new Map(layerData)` broke at runtime.

**Fix:** Renamed import to `MapGL`. Used `new globalThis.Map(layerData)` where native Map constructor is needed.

---

## Known Issues & Limitations

### 1. ExtractedView hardcoded origin

`normalizeGeometry()` in `ExtractedView.tsx` normalises coordinates relative to Bangalore (`77.5946, 12.9716`). If the polygon is drawn anywhere outside Bangalore, the 3D view renders far from the orbit centre.

**Fix needed:** Compute centroid of the `selectionPolygon` and use that as the normalisation origin.

### 2. No satellite layer

All three "satellite" map style buttons use the dark CARTO tiles. A real satellite tile URL requires an API key (Mapbox, Maptiler, etc.).

```ts
// components/MapView.tsx line ~22
satellite: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json', // ← not satellite
```

### 3. SAT analysis uses centroid, not polygon

`fetchFloodAnalysis` and `fetchWindAnalysis` receive `lat, lon, radius_meters=1000` — the polygon centroid + fixed 1km radius. The actual polygon geometry is not passed.

**Fix needed:** Pass the polygon geometry to these backends (if they support it) or compute the correct bounding radius from the polygon extents.

### 4. Thermal grid overlay not shown on map

`fetchThermalGrid` returns a `ThermalGridResponse` GeoJSON FeatureCollection. It is stored in `satResults.thermalGrid` but there is no `ThermalGridLayer` component or deck.gl layer rendering it on the map.

**Fix needed:** Build `components/analysis/ThermalGridLayer.tsx` and add a `GeoJsonLayer` / `HeatmapLayer` to `MapView.tsx` when `satResults.thermalGrid` is non-null.

### 5. Rainfall panel empty state

`components/analysis/RainfallPanel.tsx` exists and is wired into `RightPanel`. Backend data is fetched. Panel content has not been verified — if `RainfallArchiveResponse.monthly` shape doesn't match, it may render blank.

### 6. No per-drawing re-analysis on session restore

On page reload, `drawings[]` and `selectedDrawingId` are restored from localStorage. But `selectionPolygon` is null (not persisted). The user must click the drawing in the Drawings tab to re-trigger analysis.

**Fix needed:** In `StoreHydrator`, after rehydration, if `selectedDrawingId` is non-null, call `selectDrawing(selectedDrawingId)` to restore `selectionPolygon` and trigger analysis.

### 7. Overpass rate limiting

Overpass public API limits concurrent requests. During peak hours endpoints return 429 or 503. The 3-endpoint failover helps but doesn't solve it fully. For production, self-host an Overpass instance or use a subscription.

### 8. PDF export has no map screenshot

`ExportDialog.tsx` PDF contains only text (location, date, layer counts). The map canvas screenshot is stubbed — `mapRef` is wired but `html2canvas` or similar is not called.

### 9. `cancelDrawing` and `startDrawing` don't clear `selectionPolygon`

`startDrawing` previously cleared `selectionPolygon` (removed in a refactor). Starting a new drawing now leaves the previous polygon visible and active for analysis. This may be intentional (draw multiple polygons without losing analysis), but could confuse users who expect the old polygon to be deselected.

---

## Running the App

```bash
# Frontend
cd /Volumes/LocalDrive/SAT/apps/web
npm install
npm run dev          # → http://localhost:3000 → redirects to /map

# SAT backends (all 5, separate terminals or docker)
cd /Volumes/LocalDrive/SAT
docker-compose up    # starts temp:8000, sunpath:8001, flood:8002, wind:8003, rainfall:8004

# Or individually
cd Site-Analysis-Tool/src/Backend/Temperature
source venv/bin/activate && uvicorn app.main:app --reload --port 8000
```

If backends aren't running, the app still works — Overpass OSM layers load fine. Analysis panels show their loading state briefly then go blank (all `Promise.allSettled` failures → null results).

## Env vars (`.env.local` — gitignored)

```
NEXT_PUBLIC_SUPABASE_URL=placeholder
NEXT_PUBLIC_SUPABASE_ANON_KEY=placeholder
NEXT_PUBLIC_TEMP_API_URL=http://localhost:8000
NEXT_PUBLIC_SUNPATH_API_URL=http://localhost:8001
NEXT_PUBLIC_FLOOD_API_URL=http://localhost:8002
NEXT_PUBLIC_WIND_API_URL=http://localhost:8003
NEXT_PUBLIC_RAINFALL_API_URL=http://localhost:8004
```

## File Map

```
apps/web/
├── app/
│   ├── layout.tsx              Supabase env optional (try/catch)
│   ├── page.tsx                Redirects → /map
│   └── map/page.tsx            Full-screen map page, dynamic imports (ssr:false)
├── components/
│   ├── MapView.tsx             Main map: deck.gl + MapLibre, drawing, OSM layers
│   ├── ExtractedView.tsx       3D OrbitView exploded axonometric
│   ├── ControlPanel.tsx        Left panel: Layers / Drawings / 3D tabs
│   ├── DraggableLayerList.tsx  @dnd-kit sortable layer rows
│   ├── DrawingTool.tsx         Drawing mode toolbar (top bar)
│   ├── SearchBar.tsx           Nominatim geocoding (top bar)
│   ├── RightPanel.tsx          Analysis tabs + tab routing
│   ├── MetricsPanel.tsx        OSM-derived urban metrics
│   ├── ComparisonTable.tsx     Multi-area comparison table
│   ├── ExportDialog.tsx        PDF / CSV / GeoJSON / URL export
│   ├── StoreHydrator.tsx       Client-only Zustand rehydration
│   └── analysis/
│       ├── ClimatePanel.tsx    Monthly temp/precip chart
│       ├── SunPathPanel.tsx    SVG diagram + sunrise/sunset
│       ├── FloodPanel.tsx      Risk badge + score breakdown
│       ├── WindPanel.tsx       Direction + comfort + speed
│       └── RainfallPanel.tsx   Monthly rainfall
├── hooks/
│   ├── usePolygonDrawing.ts    Drawing state machine + drag detection
│   └── useSatAnalysis.ts       Promise.allSettled across all 5 SAT services
├── store/index.ts              Zustand store (all state)
├── types/index.ts              All TypeScript types
├── data/layerManifest.ts       28 OSM layers, 6 groups, queries, colors
└── utils/
    ├── osmFetcher.ts           Overpass batch fetch, cache, retry
    ├── satApi.ts               Fetch wrappers for all 5 SAT backends
    ├── metrics.ts              Area, density, diversity, green space
    └── urlState.ts             URL hash encode/decode
```
