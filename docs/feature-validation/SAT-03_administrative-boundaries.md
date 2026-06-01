# FVD-03 — Administrative Boundaries Analysis

**Jira Ticket:** SAT-TBD  
**Status:** Done  
**Resolved:** 2025-10-09  
**Type:** Story  
**Authors:** TanmayCJ (Tanmay)  
**Repository:** [SiteAnalysis_GEE](https://github.com/Site-Analysis/SiteAnalysis_GEE)

---

## Feature Overview

**User Story:** As a site analyst, I want the platform to automatically identify the Country → State/Province → District/County hierarchy for any analysis location so that I can understand the administrative and regulatory context of a site without manual lookup.

**Business Value:** Enables regulatory compliance research, jurisdiction identification, and contextual site reporting across 195+ countries using authoritative UN FAO boundary data.

---

## Commit Traceability

| Commit | Date | Author | Description |
|---|---|---|---|
| [`13afab7`](https://github.com/Site-Analysis/SiteAnalysis_GEE/commit/13afab7bca32541a862b5481b3788c96b79dcabd) | 2025-10-09 | TanmayCJ | Administrative boundaries engine + FAO GAUL integration |

---

## Code Traceability Matrix

| # | Acceptance Criterion | Commit | File | Function / Class |
|---|---|---|---|---|
| 1 | Country identified for any global coordinate | `13afab7` | `app/gee_utils.py` | `analyze_administrative_boundaries()` — FAO GAUL ADM0 |
| 2 | State / Province identified | `13afab7` | `app/gee_utils.py` | `analyze_administrative_boundaries()` — FAO GAUL ADM1 |
| 3 | District / County identified | `13afab7` | `app/gee_utils.py` | `analyze_administrative_boundaries()` — FAO GAUL ADM2 |
| 4 | Full administrative path string returned | `13afab7` | `app/models.py` | `AdministrativeHierarchy.full_path` |
| 5 | Area within ROI computed per unit | `13afab7` | `app/models.py` | `AdministrativeUnit.area_within_roi_ha` |
| 6 | Administrative codes (country/state/district) returned | `13afab7` | `app/models.py` | `AdministrativeUnit.country_code`, `.state_code`, `.district_code` |
| 7 | Summary with count of overlapping units returned | `13afab7` | `app/models.py` | `AdministrativeSummary` — `total_units`, `countries_count`, etc. |
| 8 | Visualization URL returned (boundary polygon tiles) | `13afab7` | `app/gee_utils.py` | `get_administrative_visualization()` |
| 9 | Layer accessible via `/analyze-location` | `13afab7` | `app/main.py` | `analyze_location_endpoint()` — `gee_results.get('administrative')` |
| 10 | Layer accessible via `/analyze-polygon` | `13afab7` | `app/main.py` | `analyze_polygon_endpoint()` — `elif layer == 'administrative'` |
| 11 | Polygon-clipped boundary visualizations | `13afab7` | `app/main.py` | `analyze_polygon_endpoint()` — `get_administrative_visualization(roi)` |
| 12 | "administrative" in validated layer list | `13afab7` | `app/models.py` | `LocationRequest.validate_layers()` |
| 13 | EarthEngineData model includes administrative field | `13afab7` | `app/models.py` | `EarthEngineData.administrative: Optional[AdministrativeData]` |

---

## Implementation Breakdown

### Architecture
- **Trigger:** `POST /analyze-location` with `layers=["administrative"]` OR `POST /analyze-polygon` with `layer="administrative"`
- **GEE Dataset:** FAO GAUL (Global Administrative Unit Layers)
  - `FAO/GAUL/2015/level0` — Country (ADM0)
  - `FAO/GAUL/2015/level1` — State / Province (ADM1)
  - `FAO/GAUL/2015/level2` — District / County (ADM2)
- **Coverage:** 195+ countries, UN FAO official boundaries

### Response Data Model
```
AdministrativeData
├── administrative_summary: AdministrativeSummary
│   ├── total_units: int
│   ├── countries_count: int
│   ├── states_count: int
│   ├── districts_count: int
│   ├── countries: List[str]
│   ├── states_provinces: List[str]
│   └── districts_counties: List[str]
├── administrative_units: List[AdministrativeUnit]
│   ├── country, state_province, district_county
│   ├── country_code, state_code, district_code
│   └── area_within_roi_ha
├── administrative_hierarchy: AdministrativeHierarchy
│   ├── country, state_province, district_county
│   └── full_path (e.g. "India > Karnataka > Bengaluru Urban")
└── admin_boundaries_url: str  (GEE tile URL)
```

### Key Design Decisions
- **3-tier independent queries:** Each ADM level queried separately from GEE (allows partial results if one level is missing)
- **Area calculation:** Uses GEE `.intersection(roi).area()` to compute how much of each admin unit falls inside the analysis ROI
- **Polygon mode:** Passes exact `ee.Geometry.Polygon` instead of buffer — boundary tiles clipped to drawn shape

---

## Automated Validation Plan

### AC-1, 2, 3: 3-tier hierarchy for Bangalore
```bash
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 12.9716, "lon": 77.5946, "buffer_m": 1000, "layers": ["administrative"]}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
h = d['earth_engine']['administrative']['administrative_hierarchy']
print('Country:', h['country'])       # Expected: India
print('State:', h['state_province'])  # Expected: Karnataka
print('District:', h['district_county'])  # Expected: Bengaluru Urban / Bangalore Urban
print('Full path:', h['full_path'])
"
```

### AC-4: Full path string
```bash
# Expected: "India > Karnataka > Bengaluru Urban" (or similar)
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 28.6139, "lon": 77.2090, "buffer_m": 1000, "layers": ["administrative"]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['earth_engine']['administrative']['administrative_hierarchy']['full_path'])"
# Expected: India > Delhi > ...
```

### AC-7: Summary counts
```bash
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 12.9716, "lon": 77.5946, "buffer_m": 5000, "layers": ["administrative"]}' \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
s = d['earth_engine']['administrative']['administrative_summary']
print('Total units:', s['total_units'])
print('Countries:', s['countries_count'])
print('States:', s['states_count'])
print('Districts:', s['districts_count'])
"
```

### AC-8: Visualization URL returned
```bash
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 12.9716, "lon": 77.5946, "buffer_m": 1000, "layers": ["administrative"]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('admin_url:', d['earth_engine']['administrative'].get('admin_boundaries_url', 'MISSING')[:80])"
```

### AC-1 (Global coverage): New York City
```bash
curl -X POST http://localhost:8001/analyze-location \
  -H "Content-Type: application/json" \
  -d '{"lat": 40.7128, "lon": -74.0060, "buffer_m": 1000, "layers": ["administrative"]}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); h=d['earth_engine']['administrative']['administrative_hierarchy']; print(h.get('full_path'))"
# Expected: United States > New York > ...
```

### AC-10, 11: Polygon mode
```bash
curl -X POST http://localhost:8001/analyze-polygon \
  -H "Content-Type: application/json" \
  -d '{
    "geometry": {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[77.59, 12.97], [77.61, 12.97], [77.61, 12.99], [77.59, 12.99], [77.59, 12.97]]]
      }
    },
    "layer": "administrative"
  }' | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('analysis_type'))"
# Expected: "polygon_administrative"
```
