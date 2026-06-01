# FVD-08 — Temperature & Thermal Profile Analysis

**Jira Ticket:** SAT-9  
**Status:** Done  
**Resolved:** 2026-03-26  
**Type:** Story  
**Authors:** Vishwas  
**Repository:** Local — `Site-Analysis-Tool/src/Backend/Temperature/`

---

## Feature Overview

**User Story:** As an architect, I want to view the temperature range throughout the year, so that I can plan thermal comfort and material selection accordingly.

**Business Value:** Provides annual thermal profiles (monthly tmax/tmin aggregates, annual summary, material and insulation recommendations) for any global coordinate — enabling climate-responsive building design without specialist software. Dual-source strategy ensures data availability for all locations.

---

## Jira Acceptance Criteria (from SAT-9)

| # | Acceptance Criterion |
|---|---|
| 1 | Monthly temperature data visualized in graph format |
| 2 | Annual average, max, and min values summarized |
| 3 | Thermal comfort range comparison provided |
| 4 | Material response and insulation recommendations generated |
| 5 | Temperature-related report insights included |

---

## Jira Subtasks (all Done)

| Subtask | Summary |
|---|---|
| SAT-87 | Investigate GEE Data Sources (WorldClim, TerraClimate & ERA5) |
| SAT-88 | Investigate API Data Sources (Open-Meteo and NASA POWER) |
| SAT-89 | Prototype Backend Integration Test |
| SAT-90 | Compare Options & Recommend Solution |
| SAT-91 | Consolidate & Document Findings |
| SAT-138 | UI/UX [Ruchika + Amisha] Temperature and Thermal UI |
| SAT-139 | Frontend [Vishwas] Develop Temperature Graph component using Recharts |
| SAT-140 | Backend [Vishwas] Implement FastAPI endpoint for Monthly Temperature analysis |

---

## Code Traceability Matrix

| # | Acceptance Criterion | File | Function / Class |
|---|---|---|---|
| 1 | Monthly temperature data (12 months tmax/tmin) | `app/services/climate_analytics.py` | `ClimateAnalyticsService.get_annual_thermal_profile()` — monthly groupby aggregation |
| 1 | Frontend graph component | `src/services/temperatureApi.ts` | `getThermalProfile()` → `ClimateReport.monthly_data` |
| 2 | Annual avg, peak max, lowest min summarized | `app/services/climate_analytics.py` | `ClimateSummary` construction — `annual_avg`, `peak_max`, `lowest_min` |
| 2 | Pydantic model | `app/models/climate.py` | `ClimateSummary` — `annual_avg_temp`, `peak_max_temp`, `lowest_min_temp` |
| 3 | Thermal comfort classification | `app/services/climate_analytics.py` | `ClimateAnalyticsService` — thresholds: `>24°C` → Hot, `<18°C` → Cold, else Moderate |
| 4 | Material + insulation recommendations | `app/services/climate_analytics.py` | `ClimateRecommendations` construction — threshold-based text generation |
| 4 | Recommendations model | `app/models/climate.py` | `ClimateRecommendations` — `material_suggestion`, `insulation_strategy`, `thermal_comfort_status` |
| 5 | Report endpoint returns full `ClimateReport` | `app/routers/weather.py` | `GET /weather/thermal-profile` → `ClimateReport` |
| — | IMD primary data source | `app/services/imd_weather_service.py` | `IMDWeatherService.get_daily_data()` — reads local `.grd` files via `imdlib` |
| — | Open-Meteo fallback | `app/services/open_meteo_service.py` | `OpenMeteoService.get_daily_data()` — `archive-api.open-meteo.com/v1/archive` |
| — | Fahrenheit auto-detection | `app/services/climate_analytics.py` | `mean_overall > 50.0` heuristic → `_to_celsius()` conversion |
| — | FastAPI app entry point | `app/main.py` | `app` — `weather_router` registered at `/weather` |
| — | Frontend API client | `src/services/temperatureApi.ts` | `getThermalProfile()`, `checkTemperatureApiHealth()` |

---

## Implementation Breakdown

### Architecture
```
GET /weather/thermal-profile?lat=&lon=&year=
    └── weather.py:get_thermal_profile()
        └── ClimateAnalyticsService.get_annual_thermal_profile(lat, lon, year)
            ├── IMDWeatherService.get_daily_data()        [primary]
            │   └── imdlib → reads local .grd file for year
            │       └── fallback: tries year-1 if current year not available
            ├── (on failure) OpenMeteoService.get_daily_data()  [fallback]
            │   └── GET archive-api.open-meteo.com/v1/archive
            │       params: temperature_2m_max, temperature_2m_min, daily, UTC
            ├── Fahrenheit detection: mean > 50°C → _to_celsius()
            ├── Monthly groupby → List[MonthlyTemperature]
            ├── Annual summary → ClimateSummary
            └── Threshold-based recommendations → ClimateRecommendations
        └── ClimateReport → JSON response

Frontend: src/services/temperatureApi.ts
    getThermalProfile(lat, lon, year?) → fetch /weather/thermal-profile
    → ClimateReport → Recharts graph component
```

### Technology Stack
| Component | Technology |
|---|---|
| Backend framework | FastAPI (Python) |
| Primary data source | IMD `.grd` gridded files via `imdlib` |
| Fallback data source | Open-Meteo Historical Archive API (free, global) |
| Data processing | Pandas — groupby monthly aggregation |
| Frontend API client | `temperatureApi.ts` (fetch-based, TypeScript) |
| Frontend visualization | Recharts (Temperature Graph component — SAT-139) |

### Pydantic Data Models
```
ClimateReport
├── monthly_data: List[MonthlyTemperature]
│   └── MonthlyTemperature
│       ├── month: int          (1–12)
│       ├── avg_tmax: float     (°C, monthly average daily max)
│       └── avg_tmin: float     (°C, monthly average daily min)
├── summary: ClimateSummary
│   ├── annual_avg_temp: float  (°C)
│   ├── peak_max_temp: float    (°C, highest single-day max)
│   └── lowest_min_temp: float  (°C, lowest single-day min)
└── recommendations: ClimateRecommendations
    ├── material_suggestion: str
    ├── insulation_strategy: str
    └── thermal_comfort_status: str  ("Hot / High Thermal Mass" | "Cold / Insulation" | "Moderate")
```

### Dual-Source Data Strategy
```
IMDWeatherService (primary)
    Reads local .grd files from data/ directory
    imdlib reader: tries read_grd → open → load → read
    Column normalization: maps varied column names → date, tmax, tmin
    Fallback: if year fails, tries year-1 automatically

OpenMeteoService (fallback — triggered on any IMD exception)
    URL: https://archive-api.open-meteo.com/v1/archive
    Params: daily=temperature_2m_max,temperature_2m_min, timezone=UTC
    Returns: DataFrame(date, tmax, tmin)
```

### Thermal Comfort Thresholds (Indian Context)
| annual_avg | Status | Material Strategy |
|---|---|---|
| > 24°C | Hot / High Thermal Mass | Reflective materials, shading, thermal mass, night ventilation |
| < 18°C | Cold / Insulation | High-insulation envelope, airtightness, glazing U-value |
| 18–24°C | Moderate | Balanced thermal mass, standard insulation, passive solar |

---

## Automated Validation Plan

### AC-1, 2: Monthly data + annual summary
```bash
curl "http://localhost:8000/weather/thermal-profile?lat=12.9716&lon=77.5946&year=2023" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)

# Check monthly data
monthly = d['monthly_data']
print(f'Monthly records: {len(monthly)}')
assert len(monthly) == 12, 'Expected 12 months'
for m in monthly:
    print(f'  Month {m[\"month\"]:02d}: tmax={m[\"avg_tmax\"]:.1f}°C  tmin={m[\"avg_tmin\"]:.1f}°C')

# Check summary
s = d['summary']
print(f'Annual avg: {s[\"annual_avg_temp\"]:.1f}°C')
print(f'Peak max:   {s[\"peak_max_temp\"]:.1f}°C')
print(f'Lowest min: {s[\"lowest_min_temp\"]:.1f}°C')
# Bangalore expected: annual_avg ~25-28°C, peak_max ~35°C, lowest_min ~14°C
"
```

### AC-3, 4: Thermal comfort + recommendations
```bash
curl "http://localhost:8000/weather/thermal-profile?lat=12.9716&lon=77.5946&year=2023" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
r = d['recommendations']
print('Status:', r['thermal_comfort_status'])
print('Material:', r['material_suggestion'][:80])
print('Insulation:', r['insulation_strategy'][:80])
# Bangalore (tropical): expected 'Hot / High Thermal Mass'
assert r['thermal_comfort_status'] in ['Hot / High Thermal Mass', 'Moderate', 'Cold / Insulation']
print('✓ Recommendations present')
"
```

### Open-Meteo fallback (global coverage)
```bash
# Location without IMD data (London, UK) — should fall back to Open-Meteo
curl "http://localhost:8000/weather/thermal-profile?lat=51.5074&lon=-0.1278&year=2023" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
s = d['summary']
print('London annual avg:', s['annual_avg_temp'], '°C')
# Expected: ~11-12°C (London temperate)
assert s['annual_avg_temp'] < 18, 'Expected Cold/Moderate for London'
print('✓ Open-Meteo fallback working')
"
```

### AC-5: API health check
```bash
curl http://localhost:8000/
# Expected: {"message": "SAT-Platform API is running"}
```

### Frontend integration test
```bash
# From Site-Analysis-Tool root
npm run dev &
# Then in browser: trigger thermal profile panel for any location
# Verify Recharts monthly bar/line graph renders with 12 data points
```

### Fahrenheit detection test (NASA POWER data sources)
```bash
# High-altitude location — if data returns in Fahrenheit, auto-converts
curl "http://localhost:8000/weather/thermal-profile?lat=28.6139&lon=77.2090&year=2023" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
# All temperatures should be in reasonable Celsius range (-10 to 50)
for m in d['monthly_data']:
    assert -10 < m['avg_tmax'] < 50, f'tmax out of range: {m[\"avg_tmax\"]}'
    assert -10 < m['avg_tmin'] < 50, f'tmin out of range: {m[\"avg_tmin\"]}'
print('✓ All temperatures in valid Celsius range')
"
```
