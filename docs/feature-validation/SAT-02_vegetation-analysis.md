# FVD-02 — Comprehensive Vegetation Analysis

**Jira Ticket:** SAT-TBD  
**Status:** Done  
**Resolved:** 2025-10-09  
**Type:** Story  
**Authors:** TanmayCJ (Tanmay)  
**Repository:** [SiteAnalysis_GEE](https://github.com/Site-Analysis/SiteAnalysis_GEE)

---

## Feature Overview

**User Story:** As a site analyst, I want multi-index vegetation health analysis (NDVI, EVI, SAVI) using dual-source satellite data (Sentinel-2 + MODIS) so that I can assess vegetation health with maximum reliability and global coverage, even in areas with frequent cloud cover.

**Business Value:** Enables evidence-based green space planning, urban heat island assessment, and environmental impact evaluation for any global site — not limited to India or clear-sky conditions.

---

## Commit Traceability

| Commit | Date | Author | Description |
|---|---|---|---|
| [`13afab7`](https://github.com/Site-Analysis/SiteAnalysis_GEE/commit/13afab7bca32541a862b5481b3788c96b79dcabd) | 2025-10-09 | TanmayCJ | Complete vegetation engine rewrite + MODIS integration |

---

## Code Traceability Matrix

| # | Acceptance Criterion | Commit | File | Function / Class |
|---|---|---|---|---|
| 1 | NDVI computed from Sentinel-2 (10m resolution) | `13afab7` | `app/gee_utils.py` | `calculate_vegetation_indices()` — `(NIR-Red)/(NIR+Red)` |
| 2 | EVI computed (enhanced, handles dense canopy) | `13afab7` | `app/gee_utils.py` | `calculate_vegetation_indices()` — `2.5*(NIR-Red)/(NIR+6*Red-7.5*Blue+1)` |
| 3 | SAVI computed (soil-adjusted) | `13afab7` | `app/gee_utils.py` | `calculate_vegetation_indices()` — `(NIR-Red)/(NIR+Red+0.5)*1.5` |
| 4 | MODIS fallback when Sentinel-2 unavailable | `13afab7` | `app/gee_utils.py` | `analyze_viirs_vegetation()` → `get_viirs_vegetation_data()` → fallback path |
| 5 | Vegetation health index (combined metric) reported | `13afab7` | `app/gee_utils.py` | `analyze_viirs_vegetation()` — health index field in result dict |
| 6 | 4-class vegetation distribution returned (non-veg / low / moderate / dense) | `13afab7` | `app/gee_utils.py` | `analyze_viirs_vegetation()` — `vegetation_distribution` key |
| 7 | 5 visualization URLs returned (NDVI, EVI, SAVI, health, classification maps) | `13afab7` | `app/gee_utils.py` | `get_viirs_visualization_urls()` |
| 8 | Analysis accessible via polygon boundary | `13afab7` | `app/main.py` | `analyze_polygon_endpoint()` — `elif layer == 'vegetation'` branch |
| 9 | Response includes data source metadata | `13afab7` | `app/gee_utils.py` | `analyze_viirs_vegetation()` — `data_source` field |
| 10 | Vegetation layer supported in LocationRequest validator | `13afab7` | `app/models.py` | `LocationRequest.validate_layers()` — `"vegetation"` in supported list |
| 11 | EarthEngineData model includes vegetation field | `13afab7` | `app/models.py` | `EarthEngineData.vegetation: Optional[Dict[str, Any]]` |
| 12 | Polygon-clipped vegetation maps for precise boundaries | `13afab7` | `app/main.py` | `analyze_polygon_endpoint()` — clips VIIRS to polygon ROI |

---

## Implementation Breakdown

### Architecture
- **Trigger:** `POST /analyze-location` with `layers=["vegetation"]` OR `POST /analyze-polygon` with `layer="vegetation"`
- **Primary source:** Sentinel-2 MSI Level-2A (10m, cloud-masked composite via `get_sentinel2_composite()`)
- **Secondary/fallback source:** MODIS Terra/Aqua 16-day composite — loaded via `get_viirs_vegetation_data()` when Sentinel-2 data quality is insufficient
- **Dual-source strategy:** `analyze_viirs_vegetation()` attempts Sentinel-2 first; if result is null/zero, falls back to `create_fallback_vegetation_data()` using MODIS

### Vegetation Indices (computed in `calculate_vegetation_indices()`)
| Index | Formula | Use Case |
|---|---|---|
| NDVI | `(NIR - Red) / (NIR + Red)` | General vegetation health |
| EVI | `2.5 * (NIR - Red) / (NIR + 6*Red - 7.5*Blue + 1)` | Dense canopy, atmospheric correction |
| SAVI | `(NIR - Red) / (NIR + Red + 0.5) * 1.5` | Sparse vegetation / exposed soil |

### Distribution Classification
4-class density scheme returned in `vegetation_distribution`:
- `non_vegetated`: NDVI ≤ 0.1
- `low_vegetation`: 0.1 < NDVI ≤ 0.3
- `moderate_vegetation`: 0.3 < NDVI ≤ 0.6
- `dense_vegetation`: NDVI > 0.6

### Failover Mechanism
```
Sentinel-2 composite → cloud masking → NDVI calculation
    ↓ (if null or coverage < threshold)
MODIS 16-day composite → create_fallback_vegetation_data()
    ↓
Returns data_source = "MODIS fallback" in response
```

### Polygon Mode
When called via `/analyze-polygon` with `layer="vegetation"`:
- GEE geometry is `ee.Geometry.Polygon(coordinates)` — exact boundary, not circular buffer
- `analyze_viirs_vegetation(roi)` receives polygon ROI directly
- Visualization URLs clipped to polygon extent

---

## Automated Validation Plan

### AC-1, 2, 3: All vegetation indices returned
```bash
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 12.9716, "lon": 77.5946, "buffer_m": 1000, "layers": ["vegetation"]}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
v = d['earth_engine']['vegetation']
print('mean_ndvi:', v.get('mean_ndvi') or v.get('ndvi_mean'))
print('mean_evi:', v.get('mean_evi') or v.get('evi_mean'))
print('mean_savi:', v.get('mean_savi') or v.get('savi_mean'))
print('data_source:', v.get('data_source'))
"
# Expected: float values for NDVI [-1,1], EVI, SAVI; data_source string
```

### AC-6: Distribution sums to 100%
```bash
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 12.9716, "lon": 77.5946, "buffer_m": 1000, "layers": ["vegetation"]}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
dist = d['earth_engine']['vegetation']['vegetation_distribution']
total = sum(dist.values())
print(f'Distribution total: {total:.1f}%')
print(dist)
"
# Expected: total ≈ 100%
```

### AC-7: 5 visualization URLs present
```bash
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 12.9716, "lon": 77.5946, "buffer_m": 1000, "layers": ["vegetation"]}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
v = d['earth_engine']['vegetation']
for key in ['ndvi_map', 'evi_map', 'savi_map', 'health_map', 'classification_map']:
    url = v.get('visualization_urls', {}).get(key) or v.get(key + '_url')
    status = '✓' if url else '✗'
    print(f'{status} {key}')
"
```

### AC-4: Fallback verification (high-cloud location)
```bash
# Iceland (frequent cloud cover) — should trigger MODIS fallback
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 64.1466, "lon": -21.9426, "buffer_m": 1000, "layers": ["vegetation"]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('data_source:', d['earth_engine']['vegetation'].get('data_source'))"
# Expected: may show "MODIS" or "Combined Sentinel-2 and MODIS"
```

### AC-8: Polygon mode
```bash
curl -X POST http://localhost:8001/analyze-polygon \
  -H "Content-Type: application/json" \
  -d '{
    "geometry": {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[77.59, 12.97], [77.60, 12.97], [77.60, 12.98], [77.59, 12.98], [77.59, 12.97]]]
      }
    },
    "layer": "vegetation"
  }'
# Expected: 200 with analysis_type = "polygon_vegetation"
```
