# FVD-10 — Terrain Analysis

**Jira Ticket:** SAT-66 (Backlog) / SAT-207 (To Do) — "As an architect, I want to analyze contour maps and slope orientation"
**Status:** Done — V3 backend in org repo
**Resolved:** 2026-05-26 (SiteAnalysisToolV3)
**Type:** Story
**Authors:** V3 team
**Repository:** [`Site-Analysis/SiteAnalysisToolV3`](https://github.com/Site-Analysis/SiteAnalysisToolV3) — `backend/Terrain/` + `frontend/src/`
**Latest Commit:** `4bf53de` (2026-05-15, main branch HEAD)

---

## Feature Overview

**User Story:** As an architect, I want to understand slope, aspect, and elevation of a site, so that I can identify buildable zones, hazard areas, and optimal building placement.

**Business Value:** Replaces manual topographic survey reads with automated DEM-based analysis covering slope degrees, aspect direction, buildable-zone percentage, hazard-zone percentage, elevation profiles, and per-point inspection. Feeds terrain mesh in 3D simulation.

---

## Acceptance Criteria (derived; no Jira ticket)

| # | Acceptance Criterion |
|---|---|
| 1 | Slope analysis returned (mean, min, max, std dev, classification) |
| 2 | Aspect analysis returned (dominant direction + distribution) |
| 3 | Buildable zone percentage calculated (threshold ≤ 15°) |
| 4 | Hazard zone percentage calculated (threshold > 30°) |
| 5 | Suitability score (0–100) with buildability category returned |
| 6 | Elevation profile between two points returned |
| 7 | Per-point elevation/slope/aspect inspection returned |
| 8 | Slope heatmap and elevation greyscale images returned (base64 PNG) |

---

## Code Traceability Matrix

| # | Acceptance Criterion | File | Function / Endpoint |
|---|---|---|---|
| 1 | Slope analysis | `backend/Terrain/app/terrain_utils.py` | `compute_slope_analysis()` |
| 2 | Aspect analysis | `backend/Terrain/app/terrain_utils.py` | `compute_aspect_analysis()` |
| 3 | Buildable zones | `backend/Terrain/app/terrain_utils.py` | `compute_buildable_zones(threshold_deg=15)` |
| 4 | Hazard zones | `backend/Terrain/app/terrain_utils.py` | `compute_hazard_zones(threshold_deg=30)` |
| 5 | Suitability score | `backend/Terrain/app/terrain_utils.py` | `compute_suitability_score()` |
| 5 | Score model | `backend/Terrain/app/models.py` | `SuitabilityScore` — `overall_score`, `buildability_category`, `score_color` |
| 6 | Elevation profile | `backend/Terrain/app/main.py` | `POST /profile` → `ElevationProfileResponse` |
| 7 | Point inspector | `backend/Terrain/app/main.py` | `POST /inspect` → `PointInspectorResponse` |
| 8 | Heatmap images | `backend/Terrain/app/terrain_utils.py` | Returns `images: {slope_heatmap, elevation_greyscale}` as base64 PNG |
| — | Polygon analysis | `backend/Terrain/app/main.py` | `POST /analyze/terrain/polygon` → `TerrainAnalysisResponse` |
| — | Point analysis | `backend/Terrain/app/main.py` | `POST /analyze/terrain` (point + buffer) → `TerrainAnalysisResponse` |
| — | Frontend service | `frontend/src/services/terrainApi.ts` | `analyzeTerrainPolygon()`, `analyzeTerrainPoint()`, `getElevationProfile()`, `inspectPoint()` |
| — | Frontend panel | `frontend/src/components/map/TerrainAnalysisPanel.tsx` | Terrain results display |

---

## Implementation Breakdown

### Architecture

```
POST /analyze/terrain/polygon
    body: { geometry: { type: "Polygon", coordinates: [...] } }
    └── terrain_utils: compute_slope_analysis(), compute_aspect_analysis()
    └── terrain_utils: compute_buildable_zones(threshold_deg=15)
    └── terrain_utils: compute_hazard_zones(threshold_deg=30)
    └── terrain_utils: compute_suitability_score()
    └── Returns: TerrainAnalysisResponse (slope + aspect + buildable + hazard + suitability + images + contours + histograms)

POST /profile
    body: { lat1, lon1, lat2, lon2, n_samples }
    └── Returns: ProfilePoint[] + gain/loss/min/max elevation

POST /inspect
    body: { lat, lon }
    └── Returns: elevation_m, slope_degrees, aspect_degrees, aspect_direction
```

### Technology Stack

| Component | Technology |
|---|---|
| Backend framework | FastAPI (Python) — port 8003 |
| DEM source | Mapbox Terrain-RGB tiles (decoded from RGB pngraw) |
| Elevation decoding | `height = -10000 + ((R × 256 + G + B / 256) × 0.1)` |
| Image output | base64 PNG heatmaps |
| Frontend service | TypeScript — `terrainApi.ts` (POST helper with error handling) |
| Frontend panel | React — `TerrainAnalysisPanel.tsx` |

### Response Models

```typescript
// frontend/src/services/terrainApi.ts
interface SuitabilityScore {
  overall_score: number;          // 0–100
  buildability_category: string;  // e.g. "Highly Buildable"
  buildable_percentage: number;
  hazard_percentage: number;
  slope_risk_score: number;
  aspect_bonus: number;
  score_color: string;
}

interface TerrainAnalysisData {
  suitability_score: SuitabilityScore;
  slope_analysis: SlopeAnalysis;      // mean/min/max/std/classification
  aspect_analysis: AspectAnalysis;    // dominant + distribution
  buildable_zones: BuildableZoneAnalysis;
  hazard_zones: HazardZoneAnalysis;
  recommendations: string[];
  images: { slope_heatmap: string; elevation_greyscale: string }; // base64 PNG
  contour_levels: Record<string, 'minor' | 'major'>;
  elev_range: { min: number; max: number };
  elev_histogram: Array<{ elev: number; count: number }>;
  slope_histogram: Array<{ slope_deg: number; count: number }>;
  meta: { zoom: number; meters_per_pixel: number; grid_shape: number[] };
}
```

---

## Automated Validation Plan

> Backend port: 8003. Start: `uvicorn app.main:app --reload --port 8003` from `backend/Terrain/`

### AC-1 to AC-5: Polygon analysis (slope + buildable + suitability)

```bash
curl -s -X POST http://localhost:8003/analyze/terrain/polygon \
  -H "Content-Type: application/json" \
  -d '{"geometry":{"type":"Polygon","coordinates":[[[77.58,12.97],[77.60,12.97],[77.60,12.99],[77.58,12.99],[77.58,12.97]]]}}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
slope = d['slope_analysis']
aspect = d['aspect_analysis']
buildable = d['buildable_zones']
hazard = d['hazard_zones']
score = d['suitability_score']
print('Slope mean:', slope['mean_slope_degrees'], '°')
print('Slope classification:', slope['slope_classification'])
print('Dominant aspect:', aspect['dominant_aspect'])
print('Buildable %:', buildable['buildable_percentage'])
print('Hazard %:', hazard['hazard_percentage'])
print('Suitability score:', score['overall_score'], '—', score['buildability_category'])
assert 0 <= score['overall_score'] <= 100, 'Score out of range'
assert buildable['buildable_percentage'] + hazard['hazard_percentage'] <= 100, 'Percentages exceed 100'
print('Images present:', 'slope_heatmap' in d['images'], '| elevation_greyscale' in d['images'])
print('✓ Terrain polygon analysis valid')
"
```

### AC-6: Elevation profile

```bash
curl -s -X POST http://localhost:8003/profile \
  -H "Content-Type: application/json" \
  -d '{"lat1":12.97,"lon1":77.58,"lat2":12.99,"lon2":77.60,"n_samples":50}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
profile = d['profile']
print('Profile points:', len(profile))
assert len(profile) > 0, 'Empty profile'
print('Total distance:', d['total_distance_m'], 'm')
print('Elevation gain:', d['elevation_gain_m'], 'm')
print('Range:', d['min_elevation_m'], '–', d['max_elevation_m'], 'm')
assert d['elevation_gain_m'] >= 0
print('✓ Elevation profile valid')
"
```

### AC-7: Point inspector

```bash
curl -s -X POST http://localhost:8003/inspect \
  -H "Content-Type: application/json" \
  -d '{"lat":12.9716,"lon":77.5946}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Elevation:', d['elevation_m'], 'm')
print('Slope:', d['slope_degrees'], '°')
print('Aspect:', d['aspect_degrees'], '° —', d['aspect_direction'])
assert d['elevation_m'] is not None, 'Null elevation'
print('✓ Point inspector valid')
"
```

### Health check

```bash
curl -s http://localhost:8003/health | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d['status'] == 'healthy', f'Unhealthy: {d}'
print('✓ Terrain backend healthy')
"
```

---

## Jira Subtasks (SAT-66)

| Subtask | Summary | Status |
|---|---|---|
| SAT-100 | Investigate DEM Data Sources (GEE vs. Local) | In Progress |
| SAT-101 | Validate Data Resolution with SMEs | To Do |
| SAT-102 | Prototype Backend Contour Generation | To Do |
| SAT-103 | Test Frontend Rendering & Labeling | To Do |
| SAT-104 | Benchmark End-to-End Latency | To Do |

---

## Outstanding Actions

1. **SAT-66 vs SAT-207 duplicate** — Two stories exist for the same feature. SAT-207 is [To Do] assigned to Suraj; SAT-66 is [Backlog]. Resolve duplication — close one, link to V3 implementation.
2. **Jira subtasks open** — SAT-101 through SAT-104 are To Do. V3 backend satisfies SAT-102 (prototype). Update subtask statuses.
3. **Contour overlay on map** — `contour_levels` in response but no frontend contour rendering found. FE work needed.
4. **3D terrain DEM** — Simulation module fetches terrain independently (Mapbox Terrain-RGB in browser). Unify with this backend or document as separate pipeline.
5. **Tests** — No `tests/` directory found under `backend/Terrain/`. Add pytest suite before integration.
