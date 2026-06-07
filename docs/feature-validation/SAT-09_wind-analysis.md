# FVD-09 — Wind Analysis & Ventilation Orientation

**Jira Ticket:** SAT-4  
**Status:** Done  
**Resolved:** 2026-03-26  
**Type:** Story  
**Authors:** Vishwas  
**Repository:** [`Vishwas721/sat`](https://github.com/Vishwas721/sat) — `sat04/` directory  
**Latest Commit:** `55cd75e` (2026-03-19, "updated")  
**Note:** POC lives in a personal repo (`Vishwas721/sat`), not the Site-Analysis org. Primary implementation file is `sat04/sat_wind_poc.py`.

---

## Feature Overview

**User Story:** As an architect, I want to identify the prevailing and seasonal wind directions, so that I can orient buildings for natural ventilation and comfort.

**Business Value:** Provides wind rose diagrams, seasonal wind direction data, and building orientation recommendations — enabling passive ventilation design decisions without specialist CFD software. ERA5 GEE integration gives global coverage via ECMWF ERA5-Land daily aggregates.

---

## Jira Acceptance Criteria (from SAT-4)

| # | Acceptance Criterion |
|---|---|
| 1 | Prevailing and seasonal wind data integrated from meteorological sources |
| 2 | Wind direction visualized on site map (wind rose diagram) |
| 3 | Seasonal variation toggle enabled |
| 4 | Optimal building orientation suggested for ventilation |
| 5 | Report section summarizing wind implications generated |

---

## Jira Subtasks (all Done)

| Subtask | Summary | Role |
|---|---|---|
| SAT-79 | Data Source Validation for Seasonal Aggregation | Research |
| SAT-80 | Define "Wind Rose" Calculation Logic | Research |
| SAT-81 | Research Architectural Orientation Rules | Research |
| SAT-82 | Frontend Visualization Library Selection | Research |
| SAT-83 | Data Source Comparison & Fallback Strategy | Research |
| SAT-163 | Define API Contract & JSON Schema | Design |
| SAT-164 | AI Agent Prompt Strategy for "Ventilation" | Design |
| SAT-165 | Benchmarking Latency & Performance | QA |
| SAT-166 | Create Documentation | Docs |
| SAT-209 | Wind Analysis Microservice Architecture & Setup | Implementation |
| SAT-210 | Google Earth Engine (ERA5) Integration & Vector Math | Implementation |
| SAT-211 | High-Availability Fallback Layer (Open-Meteo) | Implementation |
| SAT-212 | Performance Optimization (LRU Caching & Payload Aggregation) | Implementation |

---

## Code Traceability Matrix

| # | Acceptance Criterion | Commit | File | Function / Class |
|---|---|---|---|---|
| 1 | ERA5-Land wind data from GEE | `55cd75e` | `sat04/sat_wind_poc.py` | `fetch_gee_wind_data(lat, lon, years)` — `ECMWF/ERA5_LAND/DAILY_AGGR`, u/v bands, `scale=11132` |
| 1 | Earlier POC data fetch | `55cd75e` | `sat04/backend_poc.py` | `fetch_seasonal_data(lat, lon)` — same ERA5 dataset, 5-year sample 2019–2023 |
| 1 | Wind speed + direction vector math | `55cd75e` | `sat04/sat_wind_poc.py` | `calculate_wind_metrics(u, v)` — `speed=√(u²+v²)`, `direction=(270−atan2(v,u)×180/π)%360` |
| 2 | 16-sector wind rose construction | `55cd75e` | `sat04/sat_wind_poc.py` | `build_rose(vectors)` — 22.5° bins, frequency % + avg speed per sector |
| 2 | WindProcessor rose (earlier POC) | `55cd75e` | `sat04/backend_poc.py` | `WindProcessor.generate_wind_rose(vectors)` — `met_dir=(270−math_angle)%360`, `idx=round(met_dir/22.5)%16` |
| 2 | Wind rose Pydantic model | `55cd75e` | `sat04/sat_wind_poc.py` | `WindFrequencyBin` — `direction: str`, `frequency_percentage: float`, `avg_speed_ms: float` |
| 3 | IMD seasonal grouping | `55cd75e` | `sat04/sat_wind_poc.py` | `get_imd_season(month)` — Winter(1–2), Pre-Monsoon(3–5), SW Monsoon(6–9), Post-Monsoon(10–12) |
| 3 | Seasonal data model | `55cd75e` | `sat04/sat_wind_poc.py` | `SeasonalWindData` — `season_name`, `prevailing_direction`, `wind_rose`, `architectural_advice` |
| 4 | Building orientation recommendation | `55cd75e` | `sat04/sat_wind_poc.py` | `get_orientation_advice(prevailing_dir, season)` — axis map perpendicular to wind; special cases: W-winds → deep louvers, SW Monsoon → chajjas/overhangs |
| 4 | ArchitecturalAdvisor (earlier POC) | `55cd75e` | `sat04/backend_poc.py` | `ArchitecturalAdvisor.get_advice(season_name, stats)` — `orientation_axis` perpendicular to dominant wind + natural language `report_summary` |
| 5 | Full response model with annual summary | `55cd75e` | `sat04/sat_wind_poc.py` | `WindAnalysisResponse` — `annual_prevailing_direction`, `annual_architectural_advice`, `annual_wind_rose`, `seasonal_data` |
| 5 | Top-level API endpoint | `55cd75e` | `sat04/sat_wind_poc.py` | `get_wind_climatology(lat, lon, years=10)` — `GET /analysis/wind/climatology` → `WindAnalysisResponse` |
| — | 16-point compass label | `55cd75e` | `sat04/sat_wind_poc.py` | `get_compass_direction(degrees)` — N, NNE, NE, ENE, E, ESE, SE, SSE, S, SSW, SW, WSW, W, WNW, NW, NNW |
| — | Three-tier latency benchmark | `55cd75e` | `sat04/benchmark_performance.py` | Tier 1: `ERA5_LAND/MONTHLY_AGGR` (fast trends); Tier 2: `ERA5_LAND/DAILY_AGGR` (wind rose); Tier 3: `ERA5/DAILY` (map viz) |

---

## Implementation Breakdown

### Architecture

```
GET /analysis/wind/climatology?lat=&lon=&years=10
    └── sat_wind_poc.py: get_wind_climatology()
        └── fetch_gee_wind_data(lat, lon, years)
            └── GEE: ECMWF/ERA5_LAND/DAILY_AGGR
                bands: u_component_of_wind_10m, v_component_of_wind_10m
                scale: 11132 m (ERA5-Land native resolution ~9 km)
                → collection.getRegion(point, scale=11132).getInfo()
        └── Per record: calculate_wind_metrics(u, v)
            speed = √(u² + v²)
            direction = (270 − atan2(v, u) × 180/π) % 360  [meteorological convention]
        └── get_imd_season(month)
            Winter:        Jan–Feb   (months 1–2)
            Pre-Monsoon:   Mar–May   (months 3–5)
            SW Monsoon:    Jun–Sep   (months 6–9)
            Post-Monsoon:  Oct–Dec   (months 10–12)
        └── Per season: build_rose(vectors)
            16 sectors × 22.5° each
            sector idx = round(direction / 22.5) % 16
            → frequency_percentage, avg_speed_ms per sector
        └── get_orientation_advice(prevailing_dir, season)
            axis_map: perpendicular to wind direction
            W-winds   → deep louvers
            SW Monsoon → chajjas + overhangs
        └── WindAnalysisResponse → JSON
```

### Technology Stack

| Component | Technology |
|---|---|
| Backend framework | FastAPI (Python) |
| Primary data source | GEE ERA5-Land (`ECMWF/ERA5_LAND/DAILY_AGGR`) |
| Wind vector math | Python `math` — atan2, sqrt |
| Seasonal classification | IMD 4-season scheme |
| Wind rose | 16-sector, 22.5° bins — frequency + mean speed |
| Orientation engine | Rule-based axis map + special monsoon overrides |
| Benchmarking | 3-tier ERA5 resolution test (`benchmark_performance.py`) |

### Pydantic Data Models

```python
class WindFrequencyBin(BaseModel):
    direction: str               # "N", "NNE", "NE", …, "NNW"
    frequency_percentage: float  # % of readings in this sector
    avg_speed_ms: float          # mean wind speed (m/s) in this sector

class SeasonalWindData(BaseModel):
    season_name: str                       # "Winter", "Pre-Monsoon", etc.
    prevailing_direction: str              # dominant compass direction
    wind_rose: List[WindFrequencyBin]      # 16 sectors
    architectural_advice: Dict[str, str]   # orientation + strategy text

class WindAnalysisResponse(BaseModel):
    site_coordinates: Dict[str, float]           # {"lat": ..., "lon": ...}
    annual_prevailing_direction: str             # e.g. "SW"
    annual_architectural_advice: Dict[str, str]  # orientation + report_summary
    annual_wind_rose: List[WindFrequencyBin]     # 16 sectors, full year
    seasonal_data: List[SeasonalWindData]        # 4 seasons
```

### Wind Vector Mathematics

```
GEE returns u (eastward) and v (northward) components in m/s.

Speed:     speed = √(u² + v²)
Direction: math_angle = atan2(v, u) × (180/π)   # math convention (E=0°, CCW)
           met_dir = (270 − math_angle) % 360     # meteorological (N=0°, CW)

Compass mapping (16-point, 22.5° bins):
  idx = round(met_dir / 22.5) % 16
  labels = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
            "S","SSW","SW","WSW","W","WNW","NW","NNW"]
```

### Orientation Advice Rules

| Wind from | Long-axis orientation | Special strategy |
|---|---|---|
| N / NNE / NNW | E–W long axis | Standard cross-ventilation |
| S / SSE / SSW | E–W long axis | Standard cross-ventilation |
| E / ENE / ESE | N–S long axis | Standard cross-ventilation |
| W / WNW / WSW | N–S long axis | Deep louvers on west facade |
| SW (SW Monsoon) | Any | Chajjas + overhangs for rain protection |

### GEE Dataset Details (SAT-210, SAT-83)

| Property | Value |
|---|---|
| Dataset | `ECMWF/ERA5_LAND/DAILY_AGGR` |
| Bands used | `u_component_of_wind_10m`, `v_component_of_wind_10m` |
| Native resolution | ~9 km (scale=11132 m in GEE calls) |
| Coverage | Global |
| Default lookback | 10 years (`years=10` param) |
| Fetch method | `collection.getRegion(point, scale).getInfo()` |

### Three-Tier Benchmark (SAT-165, SAT-212)

| Tier | Dataset | Use case | Speed |
|---|---|---|---|
| 1 | `ECMWF/ERA5_LAND/MONTHLY_AGGR` | Fast trend overview | Fastest |
| 2 | `ECMWF/ERA5_LAND/DAILY_AGGR` | Wind rose + monsoon filter | Moderate |
| 3 | `ECMWF/ERA5/DAILY` | Map-level visualization | Slowest |

---

## Automated Validation Plan

> Endpoint: `GET /analysis/wind/climatology?lat=&lon=&years=10`  
> Port: TBD — run `uvicorn sat_wind_poc:app --port 8003` from `sat04/`

### AC-1: ERA5 wind data returned

```bash
curl "http://localhost:8003/analysis/wind/climatology?lat=12.9716&lon=77.5946&years=5" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('Annual prevailing direction:', d['annual_prevailing_direction'])
rose = d['annual_wind_rose']
print('Annual rose sectors:', len(rose))
assert len(rose) == 16, f'Expected 16 sectors, got {len(rose)}'
speeds = [s['avg_speed_ms'] for s in rose]
assert all(0 <= s < 50 for s in speeds), 'Speed out of range'
print('Data source: ERA5-Land GEE')
print('✓ Wind data returned')
"
```

### AC-2: Wind rose has 16 sectors with valid data

```bash
curl "http://localhost:8003/analysis/wind/climatology?lat=12.9716&lon=77.5946" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
rose = d['annual_wind_rose']
expected = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW']
dirs = [b['direction'] for b in rose]
print('Sectors returned:', dirs)
assert set(dirs) == set(expected), f'Missing sectors: {set(expected) - set(dirs)}'
total_freq = sum(b['frequency_percentage'] for b in rose)
assert 99 < total_freq < 101, f'Frequencies do not sum to 100%: {total_freq}'
print('✓ 16-sector wind rose valid')
"
```

### AC-3: All 4 IMD seasons present

```bash
curl "http://localhost:8003/analysis/wind/climatology?lat=12.9716&lon=77.5946" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
seasons = [s['season_name'] for s in d['seasonal_data']]
print('Seasons returned:', seasons)
expected = {'Winter', 'Pre-Monsoon', 'SW Monsoon', 'Post-Monsoon'}
assert expected.issubset(set(seasons)), f'Missing seasons: {expected - set(seasons)}'
for s in d['seasonal_data']:
    rose = s['wind_rose']
    assert len(rose) == 16, f'{s[\"season_name\"]}: expected 16 rose sectors'
    print(f'  {s[\"season_name\"]}: prevailing={s[\"prevailing_direction\"]}, rose sectors={len(rose)}')
print('✓ All 4 IMD seasons present with wind roses')
"
```

### AC-4: Building orientation recommendation present

```bash
curl "http://localhost:8003/analysis/wind/climatology?lat=12.9716&lon=77.5946" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
annual_advice = d['annual_architectural_advice']
print('Annual advice keys:', list(annual_advice.keys()))
assert 'orientation_axis' in annual_advice or len(annual_advice) > 0, 'No orientation advice'
for s in d['seasonal_data']:
    advice = s['architectural_advice']
    assert len(advice) > 0, f'{s[\"season_name\"]}: missing advice'
    print(f'  {s[\"season_name\"]}: {list(advice.keys())}')
print('✓ Orientation recommendations generated for annual + all seasons')
"
```

### AC-5: Full response structure for report generation

```bash
curl "http://localhost:8003/analysis/wind/climatology?lat=12.9716&lon=77.5946" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
required_fields = ['site_coordinates','annual_prevailing_direction',
                   'annual_architectural_advice','annual_wind_rose','seasonal_data']
for f in required_fields:
    assert f in d, f'Missing field: {f}'
    print(f'  ✓ {f} present')
print('Annual direction:', d['annual_prevailing_direction'])
print('Coordinates:', d['site_coordinates'])
print('✓ Full WindAnalysisResponse valid for report generation')
"
```

### Latency: Three-tier benchmark

```bash
# Tier 2 (DAILY_AGGR) — default production tier
echo "=== Tier 2: DAILY_AGGR (wind rose) ==="
time curl -s "http://localhost:8003/analysis/wind/climatology?lat=12.9716&lon=77.5946&years=5" > /dev/null

# Second request — if LRU caching implemented should be faster
echo "=== Cache hit ==="
time curl -s "http://localhost:8003/analysis/wind/climatology?lat=12.9716&lon=77.5946&years=5" > /dev/null
```

### Global coverage check (non-India location)

```bash
# London — ERA5-Land is global, should work
curl "http://localhost:8003/analysis/wind/climatology?lat=51.5074&lon=-0.1278&years=5" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
assert d['annual_prevailing_direction'] in ['N','NNE','NE','ENE','E','ESE','SE','SSE',
  'S','SSW','SW','WSW','W','WNW','NW','NNW'], 'Invalid direction'
print('London prevailing wind:', d['annual_prevailing_direction'])
print('✓ Global ERA5-Land coverage confirmed')
"
```

---

## Outstanding Actions

1. **Integrate into Site-Analysis-Tool** — `sat04/sat_wind_poc.py` is a standalone POC; production port is TBD (likely 8003 by project convention). Needs a `venv/` setup and uvicorn start script in `Site-Analysis-Tool/src/Backend/Wind/`.
2. **Frontend component** — no `windApi.ts` found in `Site-Analysis-Tool/src/services/`; equivalent of `temperatureApi.ts` needs to be created calling `GET /analysis/wind/climatology`.
3. **Open-Meteo fallback** — SAT-211 designed a fallback but not present in `sat04/` POC files. Confirm if implemented elsewhere or deferred.
4. **LRU caching** — SAT-212 specified caching; `@lru_cache` not found in `sat_wind_poc.py`. Confirm if added in a later commit or deferred.
5. **Commit hash for production merge** — latest POC commit is `55cd75e` in personal repo. When merged to org, update this FVD with new hash + target file path.
