# FVD-01 — GEE Interactive Map (Core Platform)

**Jira Ticket:** SAT-TBD  
**Status:** Done  
**Resolved:** 2025-10-05  
**Type:** Story  
**Authors:** TanmayCJ (Tanmay), chiraghontec (Chirag)  
**Repository:** [SiteAnalysis_GEE](https://github.com/Site-Analysis/SiteAnalysis_GEE)

---

## Feature Overview

**User Story:** As an urban planner / architect, I want to click a location on an interactive map and receive a comprehensive multi-layer satellite analysis (vegetation indices, elevation, slope, land cover, water occurrence, rainfall) so that I can make data-driven site assessment decisions.

**Business Value:** Provides the foundational geospatial intelligence layer for the entire SAT platform — all other analysis features (vegetation, flood, solar) plug into this core pipeline.

---

## Commit Traceability

| Commit | Date | Author | Description |
|---|---|---|---|
| [`0815bc7`](https://github.com/Site-Analysis/SiteAnalysis_GEE/commit/0815bc73d3f6a93a09cd5b833ea5a006069def25) | 2025-10-05 | TanmayCJ | Main GEE interactive map (merge) |
| [`f0ab078`](https://github.com/Site-Analysis/SiteAnalysis_GEE/commit/f0ab07800a6f703ddb406983b3b37d754890c491) | 2025-10-05 | TanmayCJ | Initial GEE map with core layers |
| [`ee33390`](https://github.com/Site-Analysis/SiteAnalysis_GEE/commit/ee333904445cf52e34383bf043cb04f6514a8cc5) | 2025-10-04 | chiraghontec (Chirag D S) | Initial commit — repo scaffold |

---

## Code Traceability Matrix

| # | Acceptance Criterion | Commit | File | Function / Class |
|---|---|---|---|---|
| 1 | User can click a map coordinate to trigger analysis | `0815bc7` | `interactive_map.html` | Leaflet `click` event handler |
| 2 | System accepts lat/lon + buffer radius as input | `0815bc7` | `app/models.py` | `LocationRequest` (Pydantic model) |
| 3 | NDVI calculated from Sentinel-2 imagery | `0815bc7` | `app/gee_utils.py` | `calculate_ndvi()`, `get_sentinel2_composite()` |
| 4 | NDBI (built-up index) calculated | `0815bc7` | `app/gee_utils.py` | `calculate_ndbi()` |
| 5 | NDWI (water index) calculated | `0815bc7` | `app/gee_utils.py` | `calculate_ndwi()` |
| 6 | Elevation data retrieved (SRTM 30m) | `0815bc7` | `app/gee_utils.py` | `get_elevation_data()` |
| 7 | Slope derived from elevation | `0815bc7` | `app/gee_utils.py` | `calculate_slope()` |
| 8 | Land cover classification (ESA WorldCover 11-class) | `0815bc7` | `app/gee_utils.py` | `get_landcover_data()`, `calculate_landcover_histogram()` |
| 9 | Water occurrence frequency retrieved (JRC GSW) | `0815bc7` | `app/gee_utils.py` | `get_water_occurrence()` |
| 10 | Annual rainfall retrieved (CHIRPS) | `0815bc7` | `app/gee_utils.py` | `get_rainfall_data()` |
| 11 | Statistics computed per layer | `0815bc7` | `app/gee_utils.py` | `calculate_statistics()` |
| 12 | Map tile URLs returned for frontend display | `0815bc7` | `app/gee_utils.py` | `get_visualization_url()`, `get_visualization_parameters()` |
| 13 | Buffer radius configurable (100–5000m) | `0815bc7` | `app/gee_utils.py` | `create_roi_buffer()` |
| 14 | India-bounds warning for out-of-bounds coords | `0815bc7` | `app/main.py` | `analyze_location_endpoint()` L83–84 |
| 15 | Full analysis orchestrated through single endpoint | `0815bc7` | `app/main.py` | `analyze_location_endpoint()` → calls `analyze_location()` |
| 16 | Response structured as typed Pydantic model | `0815bc7` | `app/models.py` | `LocationResponse`, `EarthEngineData`, `EarthEngineSummary` |
| 17 | Health check endpoint verifies GEE connectivity | `0815bc7` | `app/main.py` | `health_check()` — tests S2 image fetch |
| 18 | CORS enabled for frontend integration | `0815bc7` | `app/main.py` | `CORSMiddleware` (all origins) |

---

## Implementation Breakdown

### Architecture
The core analysis pipeline is:
1. **Frontend:** `interactive_map.html` (Leaflet.js) captures user click → sends `POST /analyze-location`
2. **API Layer:** `app/main.py:analyze_location_endpoint()` validates request via `LocationRequest`, calls `gee_utils.analyze_location()`
3. **GEE Engine:** `app/gee_utils.py:analyze_location()` orchestrates parallel GEE calls — builds ROI buffer via `create_roi_buffer()`, then conditionally runs each requested layer
4. **Response:** Results assembled into `LocationResponse` (Pydantic) with typed sub-models for summary stats, land cover histogram, visualization URLs, and ROI info

### GEE Dataset Stack
| Layer | GEE Dataset | Resolution |
|---|---|---|
| NDVI / NDBI / NDWI | `COPERNICUS/S2_SR_HARMONIZED` | 10m |
| Elevation / Slope | `USGS/SRTMGL1_003` | 30m |
| Land Cover | `ESA/WorldCover/v200` | 10m |
| Water Occurrence | `JRC/GSW1_4/GlobalSurfaceWater` | 30m |
| Rainfall | `UCSB-CHG/CHIRPS/DAILY` | ~5.5km |

### Key Design Decisions
- **Layer-based request model:** `layers: List[str]` allows selective analysis — frontend sends only what it needs; GEE calls skipped for unused layers
- **Cloud masking:** `mask_clouds()` applied to Sentinel-2 composite before index calculation
- **Visualization URLs:** `get_visualization_url()` returns pre-rendered tile URLs from GEE (no server-side image storage)
- **Buffer geometry:** `create_roi_buffer()` creates GEE `ee.Geometry.Point().buffer()` for circular ROI

---

## Automated Validation Plan

### Prerequisites
```bash
cd SiteAnalysis_GEE
source venv/bin/activate
uvicorn app.main:app --reload --port 8001
```

### AC-17: Health check passes
```bash
curl http://localhost:8001/health
# Expected: {"status": "healthy", "earth_engine": "connected", ...}
```

### AC-2, AC-15: Location analysis endpoint accepts valid request
```bash
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 12.9716, "lon": 77.5946, "buffer_m": 750, "layers": ["ndvi", "elevation", "landcover"]}'
# Expected: 200 OK with LocationResponse JSON
```

### AC-3, AC-11: NDVI returned with statistics
```bash
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 12.9716, "lon": 77.5946, "buffer_m": 500, "layers": ["ndvi"]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); s=d['earth_engine']['summary']; print(f'NDVI mean: {s[\"ndvi_mean\"]}, min: {s[\"ndvi_min\"]}, max: {s[\"ndvi_max\"]}')"
# Expected: NDVI values in range [-1, 1] for Bangalore (~0.1–0.5)
```

### AC-7: Slope layer
```bash
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 12.9716, "lon": 77.5946, "buffer_m": 500, "layers": ["slope"]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('slope_mean:', d['earth_engine']['summary']['slope_mean'])"
# Expected: float > 0
```

### AC-8: Land cover histogram sums to ~100%
```bash
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 12.9716, "lon": 77.5946, "buffer_m": 750, "layers": ["landcover"]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); h=d['earth_engine']['landcover_histogram']; total=sum(v for v in h.values() if v); print(f'Land cover total: {total:.1f}%')"
# Expected: ~100%
```

### AC-13: Buffer radius validation
```bash
# Should reject buffer < 100
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 12.9716, "lon": 77.5946, "buffer_m": 50}'
# Expected: 422 Unprocessable Entity

# Should reject buffer > 5000
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 12.9716, "lon": 77.5946, "buffer_m": 9999}'
# Expected: 422 Unprocessable Entity
```

### AC-12: Visualization URLs returned
```bash
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 12.9716, "lon": 77.5946, "buffer_m": 750, "layers": ["ndvi"]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('NDVI URL:', d['earth_engine']['visuals']['ndvi_url'][:60])"
# Expected: URL starting with https://earthengine.googleapis.com/...
```
