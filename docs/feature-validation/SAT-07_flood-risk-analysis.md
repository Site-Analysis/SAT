# FVD-04 — Flood Risk Analysis System (v3.0)

**Jira Ticket:** SAT-TBD  
**Status:** Done  
**Resolved:** 2025-11-25  
**Type:** Story  
**Authors:** TanmayCJ (Tanmay)  
**Repository:** [SiteAnalysis_GEE](https://github.com/Site-Analysis/SiteAnalysis_GEE)

---

## Feature Overview

**User Story:** As an architect or urban planner, I want a comprehensive, multi-dataset flood risk score (0–100) broken down into Elevation, Hydrology, Historical Events, and Low-Lying Area components so that I can assess a site's flood vulnerability with high accuracy and understand *why* a site is high or low risk.

**Business Value:** Enables site selection decisions that account for climate risk, supporting regulatory compliance (BFRS / NDMA guidelines), insurance assessments, and sustainable design. Fixed critical scoring bugs that previously returned incorrect results for oceans, deserts, and high-altitude terrain.

---

## Commit Traceability

| Commit | Date | Author | Description |
|---|---|---|---|
| [`edd4c29`](https://github.com/Site-Analysis/SiteAnalysis_GEE/commit/edd4c29c1deb05797e1ca698b63b2691bf975b81) | 2025-11-25 | TanmayCJ | v3.0: Comprehensive flood risk system + bug fixes |

### Bug Fixes in this Commit
| Bug | Fix |
|---|---|
| Rainfall score always maxed out globally | Normalized against location-specific max rainfall |
| Ocean/water bodies assigned high risk | Permanent water bodies now correctly get 0 risk score |
| Elevation thresholds too sensitive | Realistic thresholds calibrated for different terrain types |
| Hydrology scoring for permanent water | Permanent water bodies excluded from river-proximity scoring |

---

## Code Traceability Matrix

| # | Acceptance Criterion | Commit | File | Function / Class |
|---|---|---|---|---|
| 1 | Composite flood risk score (0–100) returned | `edd4c29` | `app/gee_utils.py` | `compute_flood_risk_score()` |
| 2 | 5 risk categories: Very Low / Low / Moderate / High / Very High | `edd4c29` | `app/gee_utils.py` | `get_primary_risk_category()` |
| 3 | Elevation component score (MERIT DEM + ALOS + SRTM) | `edd4c29` | `app/gee_utils.py` | `get_elevation_data()`, `calculate_elevation_risk_score()` |
| 4 | Hydrology component score (flow accumulation, river proximity, drainage) | `edd4c29` | `app/gee_utils.py` | `get_hydrology_data()`, `calculate_hydrology_risk_score()` |
| 5 | Historical flood component (JRC GSW + DFO + Cloud-to-Street + CHIRPS) | `edd4c29` | `app/gee_utils.py` | `get_flood_history()` |
| 6 | LLAI (Low-Lying Area Index) component | `edd4c29` | `app/gee_utils.py` | `compute_low_lying_area_index()` |
| 7 | Per-component scores exposed in response | `edd4c29` | `app/models.py` | `FloodRiskScore.elevation_risk`, `.hydrology_risk`, `.historical_risk`, `.llai_risk` |
| 8 | Terrain classification (flat/hilly/mountainous) | `edd4c29` | `app/gee_utils.py` | `classify_terrain()` |
| 9 | Drainage density classification | `edd4c29` | `app/gee_utils.py` | `calculate_drainage_density()` |
| 10 | River proximity risk classification | `edd4c29` | `app/gee_utils.py` | `classify_river_proximity()` |
| 11 | Smart flood mitigation recommendations generated | `edd4c29` | `app/gee_utils.py` | `generate_flood_recommendations()` |
| 12 | Ocean / permanent water body correctly scored 0 risk | `edd4c29` | `app/gee_utils.py` | `compute_flood_risk_score()` — permanent water mask |
| 13 | Multiple visualization map URLs returned | `edd4c29` | `app/gee_utils.py` | flood analysis result dict — `visualization_urls` |
| 14 | Full flood Pydantic models typed | `edd4c29` | `app/models.py` | `FloodAnalysis`, `FloodRiskScore`, `ElevationAnalysis`, `HydrologyAnalysis`, `FloodHistory`, `LowLyingAreaIndex` |
| 15 | "flood" in validated layer list | `edd4c29` | `app/models.py` | `LocationRequest.validate_layers()` |

---

## Implementation Breakdown

### Architecture
- **Trigger:** `POST /analyze-location` with `layers=["flood"]`
- **GEE Dataset Stack (10+ sources):**

| Component | Datasets | Purpose |
|---|---|---|
| Elevation | MERIT DEM, ALOS AW3D30, SRTM | Terrain-corrected elevation + slope |
| Hydrology | MERIT Hydro, HydroSHEDS | Flow accumulation, river proximity, drainage |
| Historical | JRC GSW, DFO Flood Archive, Cloud-to-Street | 30+ years flood events + water recurrence |
| LLAI | MERIT DEM derived | Low-lying area depression analysis |
| Rainfall | CHIRPS Daily | Annual + daily rainfall statistics |

### 4-Component Scoring Formula
```
overall_score = (
    0.30 × elevation_risk +
    0.25 × hydrology_risk +
    0.25 × historical_risk +
    0.20 × llai_risk
)
```
Each component scored 0–100; weighted sum produces composite score.

### Risk Category Thresholds
| Score | Category | Color |
|---|---|---|
| 0–20 | Very Low | Green |
| 20–40 | Low | Light Green |
| 40–60 | Moderate | Yellow |
| 60–80 | High | Orange |
| 80–100 | Very High | Red |

### Key Bug Fixes (v3.0)
- **Permanent water detection:** `get_flood_history()` uses JRC occurrence > 80% as mask → assigns 0 elevation/hydrology risk (ocean is not a flood risk to a building)
- **Rainfall normalization:** Score = `min(annual_rainfall / location_specific_max, 1) * 100` rather than global fixed denominator
- **Elevation thresholds:** `classify_terrain()` uses relative elevation (percentile within ROI) not absolute meters — correct for both coastal plains and mountain valleys

### Response Data Model
```
FloodAnalysis
├── risk_score: FloodRiskScore
│   ├── overall_score: float [0-100]
│   ├── risk_category: str
│   ├── elevation_risk, hydrology_risk, historical_risk, llai_risk: float
├── elevation: ElevationAnalysis
│   ├── mean/min/max/range elevation, slope, low_lying_area_pct, terrain_classification
├── hydrology: HydrologyAnalysis
│   ├── flow_accumulation, nearest_river_distance_m, water_occurrence_pct
│   ├── drainage_density, river_proximity_risk
├── flood_history: FloodHistory
│   ├── historical_flood_events, annual_rainfall_mm, flood_risk_score
├── llai: LowLyingAreaIndex
│   ├── llai_mean/min/max, risk_distribution, primary_risk_category
└── recommendations: List[str]
```

---

## Automated Validation Plan

### AC-1: Composite score in [0, 100]
```bash
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 28.6139, "lon": 77.2090, "buffer_m": 1000, "layers": ["flood"]}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
rs = d['earth_engine']['flood_analysis']['risk_score']
print('Overall score:', rs['overall_score'])
print('Category:', rs['risk_category'])
assert 0 <= rs['overall_score'] <= 100, 'Score out of range!'
print('✓ Score in valid range')
"
```

### AC-2: Risk category validation
```bash
# High-flood-risk location: Dhaka, Bangladesh (low-lying riverine city)
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 23.8103, "lon": 90.4125, "buffer_m": 1000, "layers": ["flood"]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); rs=d['earth_engine']['flood_analysis']['risk_score']; print('Dhaka score:', rs['overall_score'], '|', rs['risk_category'])"
# Expected: High or Very High

# Low-risk location: Swiss Alps
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 46.8182, "lon": 8.2275, "buffer_m": 1000, "layers": ["flood"]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); rs=d['earth_engine']['flood_analysis']['risk_score']; print('Alps score:', rs['overall_score'], '|', rs['risk_category'])"
# Expected: Very Low or Low
```

### AC-7: All 4 component scores present
```bash
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 12.9716, "lon": 77.5946, "buffer_m": 1000, "layers": ["flood"]}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
rs = d['earth_engine']['flood_analysis']['risk_score']
for comp in ['elevation_risk', 'hydrology_risk', 'historical_risk', 'llai_risk']:
    val = rs.get(comp)
    status = '✓' if val is not None else '✗ MISSING'
    print(f'{status} {comp}: {val}')
"
```

### AC-12: Ocean correctly scored 0 (or very low)
```bash
# Mid-Atlantic Ocean point
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 35.0, "lon": -40.0, "buffer_m": 1000, "layers": ["flood"]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); rs=d['earth_engine']['flood_analysis']['risk_score']; print('Ocean score:', rs['overall_score'])"
# Expected: 0 or near-0 (not Very High)
```

### AC-11: Recommendations returned
```bash
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 23.8103, "lon": 90.4125, "buffer_m": 1000, "layers": ["flood"]}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
recs = d['earth_engine']['flood_analysis']['recommendations']
print(f'Recommendations count: {len(recs)}')
for i, r in enumerate(recs[:3], 1):
    print(f'{i}. {r[:80]}')
"
# Expected: ≥3 context-aware recommendations
```
