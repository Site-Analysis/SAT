# FVD-11 — 3D Simulation Engine

**Jira Ticket:** SAT-218 [To Do] — "3D Render in SAT"
**Status:** Done — V3 in org repo; Jira story still To Do (docs/review pending)
**Resolved:** 2026-05-26 (SiteAnalysisToolV3)
**Type:** Story
**Authors:** V3 team
**Repository:** [`Site-Analysis/SiteAnalysisToolV3`](https://github.com/Site-Analysis/SiteAnalysisToolV3) — `frontend/src/simulation/`
**Latest Commit:** `dc4288a` (Merge PR #3 — fix 3D render issues)

---

## Feature Overview

**User Story:** As an architect, I want to load a real site in 3D with terrain and OSM context, place and edit buildings on it, and design floor-by-floor, so that I can evaluate massing, GFA, parking, and carbon at concept stage.

**Business Value:** Provides a full AEC-grade 3D design environment in the browser — no desktop BIM software required. Architects select a site on a map, get real OSM buildings + terrain in seconds, then sketch proposals with live metrics (GFA, FAR, carbon, daylight, parking). Floor-by-floor detail editor enables per-floor use assignment and opening placement.

---

## Acceptance Criteria (derived; no Jira ticket)

| # | Acceptance Criterion |
|---|---|
| 1 | User can search and select a site by drawing rectangle on a Mapbox map |
| 2 | OSM context (buildings, roads, trees, water) loaded and rendered in 3D |
| 3 | Terrain DEM fetched from Mapbox tiles and rendered as mesh |
| 4 | Proposal buildings placeable, moveable, scaleable in 3D scene |
| 5 | Live metrics displayed: GFA, Volume, Floors, Carbon, Daylight, Parking |
| 6 | Floor-by-floor sketch detail editor (2D plan + 3D preview, per-floor use) |
| 7 | Terrain-aware building placement (buildings sit on terrain surface) |
| 8 | Buildings, trees, roads, terrain-pads, sculpt elements all supported as design tools |

---

## Code Traceability Matrix

| # | Acceptance Criterion | File | Function / Class |
|---|---|---|---|
| 1 | Map site selection | `simulation/components/site-creation/SiteCreationFlow.tsx` | `SiteCreationFlow` — Mapbox rectangle draw |
| 1 | Search providers | `services/geocodingService.ts` | Multi-provider (Ola, Mapbox, Google) India-first ranking |
| 1 | Selection validation | `simulation/stores/useCurrentSiteStore.ts` | Hard limits: min ~10,000 m², max ~6,250,000 m² |
| 2 | OSM fetch | `lib/osm-fetch.ts` | `fetchOSMContext()` — Overpass API + osmtogeojson |
| 2 | Context geometry | `simulation/utils/context-geometry.ts` + `.worker.ts` | Web Worker — buildings/roads/trees → local XZ meters |
| 3 | Terrain DEM fetch | `simulation/utils/terrain-dem.ts` | `fetchTerrainDEM()` — Mapbox Terrain-RGB tiles, WebGL decode |
| 3 | Terrain mesh | `simulation/components/scene/SceneCanvas.tsx` | `PlaneGeometry` vertex displacement from elevation grid |
| 4 | Building placement | `simulation/stores/useProposalStore.ts` | `addDesignElement()` — `BasicBuildingElement` |
| 4 | Transform controls | `simulation/components/scene/SceneCanvas.tsx` | `TransformControls` — move/rotate/scale |
| 5 | Live metrics | `simulation/stores/useProposalAnalysisStore.ts` | `proposalMetrics` — GFA, volume, floors, carbon, daylight, parking |
| 5 | Analysis display | `simulation/components/panels/AnalysisPanel.tsx` | `AnalysisPanel` — live metric rows |
| 6 | Detail editor | `simulation/components/sketch-detail/SketchDetailRoot.tsx` | `SketchDetailRoot` (lazy loaded) |
| 6 | 2D plan canvas | `simulation/components/sketch-detail/editor-2d/PlanCanvas.tsx` | Konva 2D floor editing |
| 6 | 3D preview | `simulation/components/sketch-detail/preview-3d/DetailPreviewCanvas.tsx` | R3F live preview |
| 6 | Floor stack nav | `simulation/components/sketch-detail/FloorStackNavigator.tsx` | Per-floor height, usage, openings |
| 7 | Terrain-aware placement | `simulation/components/scene/SceneCanvas.tsx` | Elevation sampling at XZ coordinates |
| 8 | Design tools | `simulation/stores/useDesignToolbarStore.ts` | Categories: buildings, vegetation, transportation, generic, sketch3d, terrain |
| 8 | Proposal types | `simulation/types/proposal.ts` | `BasicBuilding`, `Tree`, `Road`, `SiteLimits`, `TerrainPad`, `TerrainSculpt`, `Surface`, `Sketch3D` |

---

## Implementation Breakdown

### Architecture

```
/simulation route
  └── SimulationRoot (simulation/app/SimulationRoot.tsx)
      ├── Stage: map-selection → SiteCreationFlow
      │   ├── Mapbox react-map-gl (rectangle draw)
      │   ├── geocodingService (Ola / Mapbox / Google, India-first)
      │   └── On confirm:
      │       ├── terrain-dem.ts: fetch Terrain-RGB tiles → decode WebGL → bilinear grid
      │       └── osm-fetch.ts: Overpass API → osmtogeojson → context-geometry.worker.ts
      │           └── Buildings/roads/trees projected to local XZ metres (Turf.js)
      └── Stage: scene-ready → SceneCanvas (Three.js / R3F)
          ├── Terrain mesh: PlaneGeometry + vertex Y from elevation grid
          ├── Context: buildings (ExtrudeGeometry), roads (strip), trees (instanced)
          ├── Proposal design elements (from useProposalStore)
          │   ├── BasicBuilding: ExtrudeGeometry + TransformControls
          │   ├── Tree: instanced mesh
          │   ├── Road: terrain-draped strip
          │   ├── TerrainPad / SculptTerrain / SiteLimits
          │   └── Generic volumes + Sketch3D
          ├── AnalysisPanel: live GFA/Volume/Floors/Carbon/Daylight/Parking
          └── Double-click → SketchDetailRoot (lazy)
              ├── PlanCanvas (Konva): 2D floor editing
              ├── DetailPreviewCanvas (R3F): live 3D sync
              └── FloorStackNavigator: per-floor height + use + openings
```

### Technology Stack

| Component | Technology |
|---|---|
| Frontend framework | React 18 + TypeScript + Vite |
| 3D engine | Three.js + `@react-three/fiber` + `@react-three/drei` |
| Raycast acceleration | `@react-three/drei` `Bvh` |
| 2D map stage | `react-map-gl` + `mapbox-gl` |
| Terrain source | Mapbox Terrain-RGB `{z}/{x}/{y}.pngraw` (WebGL decode) |
| OSM context | Overpass API + `osmtogeojson` |
| Geometry operations | Turf.js (area, bounds, clip, rectangle) |
| 2D floor editor | `react-konva` + Konva |
| Panels split | `allotment` (resizable panes) |
| State management | Zustand (8 simulation stores) |
| Web Worker | `context-geometry.worker.ts` — context geometry conversion |

### Simulation Stores

| Store | Purpose |
|---|---|
| `useCurrentSiteStore` | Stage machine, site selection, context layer |
| `useProposalStore` | Design elements (buildings/trees/roads/etc.), selection |
| `useProposalAnalysisStore` | Derived GFA/volume/floor/carbon/daylight/parking metrics |
| `useDesignToolbarStore` | Active tool category + tool |
| `useSketchDetailStore` | Isolation mode, floor-by-floor state, undo/redo |
| `useContextEditStore` | Double-click context building editing |
| `useContextMenuStore` | Right-click menu state |
| `useBuildingHoverStore` | Hover tooltip (area, floors, height) |

### Known Limitations (from SIMULATION_TECH_STACK.md)

| # | Limitation |
|---|---|
| 1 | CSG boolean ops (union/subtract/intersect) use bounds approximation — `csg-ops.ts` exists but not wired |
| 2 | Terrain tools (pad, sculpt, site-limits) do not mutate the base elevation grid |
| 3 | Analysis panel uses local proposal metrics only — does not call SunPath/Flood/Temperature APIs |
| 4 | Simulation persistence (Supabase) exists as service but not wired to main UI flow |

---

## Automated Validation Plan

> No backend required for simulation. Needs Mapbox token in `frontend/.env`.

### AC-1: Site selection validation (manual UI test)

```bash
cd /Volumes/LocalDrive/SiteAnalysisToolV3/frontend
npm run dev
# Navigate to http://localhost:8080/simulation
# Draw rectangle < 10,000 m² → expect validation error (too small)
# Draw rectangle > 6,250,000 m² → expect validation error (too large)
# Draw valid ~100,000 m² rectangle → expect context+terrain load
```

### AC-2 & AC-3: OSM context + terrain load (console check)

```javascript
// In browser console after confirming site:
const site = window.__zustand_useCurrentSiteStore?.getState?.();
// stage should be 'scene-ready'
// contextLayer.buildings.length > 0 (for urban sites)
```

### AC-5: Live metrics sanity check (console)

```javascript
const store = window.__zustand_useProposalAnalysisStore?.getState?.();
const m = store.proposalMetrics;
console.log('GFA:', m.gfa, 'm²');
console.log('Carbon:', m.carbon, 'kgCO₂e');
// Place a 10×10×10m building → expect GFA ~300m² (3 floors × 100m²)
```

### AC-6: Sketch detail isolation mode (manual UI test)

```bash
# In simulation scene:
# Double-click a proposal building → SketchDetailRoot should mount
# Left pane shows Konva 2D plan
# Right pane shows 3D preview
# Change floor height → 3D preview updates live
# Press Save → main scene building updates
```

---

## Outstanding Actions

1. **Wire analysis APIs** — simulation `AnalysisPanel` uses only local proposal metrics. Should call `SunPath/Temperature/Wind` backends after massing is set.
2. **Wire persistence** — `simulationProjectService.ts` + `collaborationService.ts` exist but are not connected to `SimulationRoot`'s UI flow.
3. **CSG boolean ops** — `csg-ops.ts` (three-bvh-csg) must be wired to replace bounds-based approximation in `useProposalStore`.
4. **Terrain mutation** — `TerrainPad` and `TerrainSculpt` elements need to modify the elevation grid, not just render overlays.
5. **SAT-218 subtasks open** — SAT-219 (System Overview), SAT-220 (Technical pipeline), SAT-221 (Tech stack) are all To Do. Write documentation to close them.
6. **SAT-218 status** — Story is still [To Do] in Jira despite code being in org repo. Move to In Progress / Done after subtask docs are written.
