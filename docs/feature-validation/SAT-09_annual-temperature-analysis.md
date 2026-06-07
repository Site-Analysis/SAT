# FVD-09 — Annual Temperature Analysis (SAT Monorepo Migration)

**Jira Ticket:** SAT-224 (migration) / SAT-9 (original story)
**Status:** In Progress
**Branch:** `feat/temperature-service`
**Sprint:** SAT Sprint 4
**Assignee:** Chirag D S
**Authors:** Vishwas (original spike + V3 build), Chirag (SAT migration + AC4/AC5 completion)
**Source reviewed:** `SiteAnalysisToolV3/backend/Temperature/`

> **Note:** FVD-08 (`SAT-08_temperature-thermal-profile.md`) documents the original `Site-Analysis-Tool` implementation.
> This document covers the **SAT monorepo migration** and the additional work required to complete AC4 and AC5.

---

## Feature Overview

**User Story (SAT-9):** As an architect, I want to view the temperature range throughout the year, so that I can plan thermal comfort and material selection accordingly.

**Business Value:** Brings the annual thermal analysis feature into the SAT monorepo under a feature flag. Extends the original backend-only recommendations with a data-driven ECBC 2017 envelope recommendation engine (5 climate zones, 7 decision variables) and a wired PDF report export — completing all 5 acceptance criteria for production use.

---

## Spike Reference

Original spike: `[Vishwas]SAT-9.docx.md` (October 2025)

| Data Source | Verdict | Latency | Decision |
|---|---|---|---|
| IMD imdlib (.grd) | Feasible but no data files | 0.0058 s (extraction) | Primary — Enhancement-Later |
| Open-Meteo Archive (ERA5) | Excellent | ~1.2 s | **De-facto primary (100% of requests)** |
| NASA POWER | Too slow | 7.5 s | Rejected |
| GEE (WorldClim / TerraClimate) | Complex, WorldClim too old | Variable | Rejected |

**IMD status (2026-06-02):** No `.grd` files present in repository. imdlib adapter uses incorrect reader names (`read_grd`, `open`, `load`, `read` — none exist in imdlib API). IMD formally demoted to **Enhancement-Later**. All production requests go through Open-Meteo.

---

## Acceptance Criteria — Final Status

| # | Criterion | Status | Delivered by |
|---|---|---|---|
| AC1 | Monthly temperature data visualized in graph format | ✅ PASS | `TemperatureAnalysisPanel.tsx` — ComposedChart (tmax/tmin/tavg/feels-like) + box-plot percentiles |
| AC2 | Annual average, max, and min values summarized | ✅ PASS | Panel summary tiles + `ClimateSummary` from `/weather/thermal-profile` |
| AC3 | Thermal comfort range comparison provided | ✅ PASS | IMAC 20–26°C comfort band on chart; comfort-days %; CDD/HDD tiles; heatwave day count |
| AC4 | Material response and insulation recommendations generated | ✅ PASS | `ecbc-recommendations.ts` — ECBC 2017 Table 3.1 engine, 5 zones, 7 variables |
| AC5 | Temperature-related report insights included | ✅ PASS | `InsightsPanel` `TemperatureInsights` component + `export-pdf.ts` temperature page |

---

## Architecture (verified 2026-06-02)

```
Frontend → SAT Backend → Open-Meteo (ERA5)

TemperatureAnalysisPanel.tsx
  └── fetchClimateAnalysis() [openMeteoApi.ts]
      └── GET /weather/climate-archive?latitude=&longitude=&start_date=&end_date=&daily=...
          └── app/routers/weather.py:climate_archive_proxy()
              └── httpx.get → archive-api.open-meteo.com/v1/archive (disk-cached)
              └── 10 variables: tmax/tmin, feels-like, RH, wind, solar, precip, precipitation_hours

TemperatureResultView.tsx (heatmap)
  └── getThermalGrid() [temperatureApi.ts]
      └── POST /weather/thermal-grid
          └── app/routers/weather.py:get_thermal_grid()
              └── Spatial N×N grid → per-cell annual avg temp via Open-Meteo

DEPRECATED (zero frontend call sites):
  temperatureApi.getThermalProfile()
      └── GET /weather/thermal-profile [dead code — no component calls this]
          └── app/routers/weather.py:get_thermal_profile()
              └── ClimateAnalyticsService → IMD (fails) → OpenMeteo fallback

Wind (separate panel):
  GET /weather/analyze-wind → ERA5 5-year daily wind data
```

### Feature Flag

All 4 endpoints gated by `feature.temperature.thermal-profile` (reads `FLAGS` env var).
`FLAGS=feature.temperature.thermal-profile` in `.env` to enable locally.

---

## Code Traceability Matrix

### AC1 — Monthly temperature data in graph format

| File | Location | Role |
|---|---|---|
| `SiteAnalysisToolV3/frontend/src/components/map/TemperatureAnalysisPanel.tsx` | `ComposedChart` block (lines ~362–402) | Recharts ComposedChart renders tmax, tmin, tavg, feels-like per month; box-plot percentile bars |
| `SiteAnalysisToolV3/frontend/src/services/openMeteoApi.ts` | `_parseClimateResponse()`, `MonthStat` interface | Aggregates daily ERA5 data into 12 monthly records with 14 derived variables each |
| `SAT/services/temperature/app/routers/weather.py` | `climate_archive_proxy()` | Backend proxy returning raw Open-Meteo JSON (disk-cached) |

### AC2 — Annual average, max, and min summarized

| File | Location | Role |
|---|---|---|
| `SiteAnalysisToolV3/frontend/src/components/map/TemperatureAnalysisPanel.tsx` | Summary tiles block (lines ~316–335) | Renders annual avg, peak max, lowest min, temperature range |
| `SiteAnalysisToolV3/frontend/src/services/openMeteoApi.ts` | `ClimateAnalysis.annual` | `tavg`, `tmax`, `tmin`, `tRange`, `feelsAvg` annual aggregates |
| `SAT/services/temperature/app/models/climate.py` | `ClimateSummary` | `annual_avg_temp`, `peak_max_temp`, `lowest_min_temp` (from deprecated `/thermal-profile`) |

### AC3 — Thermal comfort range comparison

| File | Location | Role |
|---|---|---|
| `SiteAnalysisToolV3/frontend/src/services/openMeteoApi.ts` | Lines 18–21 | `COMFORT_LOW=20`, `COMFORT_HIGH=26` (IMAC), `CDD_BASE=18`, `HEATWAVE_THRESHOLD=35` |
| `SiteAnalysisToolV3/frontend/src/services/openMeteoApi.ts` | `_parseClimateResponse()` | Computes `comfortDays`, `heatwaveDays`, `cdd`, `hdd` per month |
| `SiteAnalysisToolV3/frontend/src/components/map/TemperatureAnalysisPanel.tsx` | Comfort tiles (lines ~339–343) | `comfortPct` tile: "X% of year within IMAC range" |
| `SiteAnalysisToolV3/frontend/src/components/map/TemperatureAnalysisPanel.tsx` | Chart `ReferenceLine` | 20°C and 26°C comfort band drawn on monthly chart |
| `SiteAnalysisToolV3/frontend/src/lib/thermal-comfort.ts` | `calculatePMV()`, `calculatePPD()`, `calculateUTCI()` | ISO 7730 PMV/PPD + UTCI (Bröde 2012 polynomial) — used in microclimate grid |

### AC4 — Material response and insulation recommendations

| File | Location | Role |
|---|---|---|
| `SiteAnalysisToolV3/frontend/src/lib/ecbc-recommendations.ts` | `ECBC_ENVELOPE_TABLE` | ECBC 2017 Table 3.1 U-values for Hot & Dry / Warm & Humid / Composite / Temperate / Cold |
| `SiteAnalysisToolV3/frontend/src/lib/ecbc-recommendations.ts` | `generateEnvelopeRecommendations()` | Decision engine: zone → isHotDominant / isColdDominant / isHumid → thermalMass / insulationPriority / glazingSpec / seasonalFlags |
| `SiteAnalysisToolV3/frontend/src/components/map/TemperatureAnalysisPanel.tsx` | "Envelope Recommendations" section | Renders ECBC U-value grid, thermal mass, insulation, glazing, seasonal flags, CDD/HDD ratio |
| `SAT/services/temperature/app/services/climate_analytics.py` | `ClimateAnalyticsService.get_annual_thermal_profile()` lines 91–107 | Backend stub (3-category, annual avg only) — used only by deprecated `/thermal-profile` endpoint |
| `SAT/services/temperature/app/models/climate.py` | `ClimateRecommendations` | `material_suggestion`, `insulation_strategy`, `thermal_comfort_status`, `climate_zone` (optional), `cdd_hdd_ratio` (optional) |

**ECBC 2017 Table 3.1 U-value targets (transcribed from BEE, Government of India):**

| ECBC Zone | Wall U (W/m²K) | Roof U (W/m²K) | Window U | SHGC |
|---|---|---|---|---|
| Hot & Dry | 0.44 | 0.33 | 3.0 | 0.25 |
| Warm & Humid | 0.44 | 0.33 | 3.0 | 0.25 |
| Composite | 0.44 | 0.33 | 3.0 | 0.25 |
| Temperate | 0.44 | 0.33 | 3.0 | 0.40 |
| Cold | 0.44 | 0.20 | 2.0 | 0.51 |

**Decision variables used:** ECBC zone, CDD/HDD ratio (dominance), peak monthly RH (humidity), peak monthly solar sum, monthly heatwave days, monthly tavg (cold provision).

### AC5 — Temperature-related report insights

| File | Location | Role |
|---|---|---|
| `SiteAnalysisToolV3/frontend/src/components/map/InsightsPanel.tsx` | `TemperatureInsights` component | Renders ECBC zone, U-value targets, envelope strategy (thermal mass / insulation / glazing), CDD/HDD tile, heatwave count, seasonal flags — for `mapType="temperature"` |
| `SiteAnalysisToolV3/frontend/src/components/map/TemperatureResultView.tsx` | Line ~221 + `InsightsPanel` call | `climateAnalysis = useMapStore(s => s.temperatureAnalysis.results)` — reactive store read; passed as `climateData` prop |
| `SiteAnalysisToolV3/frontend/src/lib/export-pdf.ts` | `addTemperaturePage()` | PDF page: annual stats table, ECBC zone + U-value row, envelope recommendations (thermal mass, insulation, glazing), monthly tmax/tmin table, ERA5 + ECBC citation |
| `SiteAnalysisToolV3/frontend/src/lib/export-pdf.ts` | `PdfReportOptions.temperatureData` | `temperatureData?: ClimateAnalysis` field added; page 6 of report when populated |
| `SiteAnalysisToolV3/frontend/src/components/map/TemperatureAnalysisPanel.tsx` | "Download Temperature Report" button | Calls `downloadProjectReport({ temperatureData: data })` — triggers PDF generation |

---

## SAT Monorepo File Inventory

```
SAT/services/temperature/
├── app/
│   ├── main.py                          # FastAPI app; GET /health; CORS from env
│   ├── models/
│   │   └── climate.py                   # ClimateReport, ThermalGridRequest/Response
│   ├── routers/
│   │   └── weather.py                   # 4 endpoints; _require_flag() at each
│   └── services/
│       ├── climate_analytics.py         # IMD→OpenMeteo fallback; monthly aggregation
│       ├── imd_weather_service.py       # IMD .grd reader (Enhancement-Later)
│       └── open_meteo_service.py        # Open-Meteo Archive API client (active fallback)
├── Dockerfile                           # Python 3.11-slim; data/ volume mount
├── requirements.txt                     # Pinned exact versions
├── AGENTS.md                            # Migration context + checklist
└── README.md                            # Service docs

SAT/contracts/
└── temperature.yaml                     # v1.1.0; all 4 live endpoints documented

SAT/tests/
├── temperature_smoke.py                 # 5 pytest cases (Open-Meteo mocked)
└── temperature_imd_validation.py        # 2 xfail cases documenting Enhancement-Later

SiteAnalysisToolV3/frontend/src/
├── lib/ecbc-recommendations.ts          # NEW — ECBC 2017 engine (AC4)
├── tests/ecbc-recommendations.test.ts  # 17/17 vitest passing
├── components/map/
│   ├── TemperatureAnalysisPanel.tsx     # MODIFIED — ECBC cards replace stub (AC4)
│   ├── TemperatureResultView.tsx        # MODIFIED — climateData from store (AC5)
│   └── InsightsPanel.tsx               # MODIFIED — TemperatureInsights added (AC5)
├── lib/export-pdf.ts                    # MODIFIED — temperature page + wiring (AC5)
└── services/openMeteoApi.ts            # FIXED — CACHE_KEY_PREFIX bug (line 23)
```

---

## Endpoints

| Endpoint | Method | Flag-gated | Status | Frontend caller |
|---|---|---|---|---|
| `/health` | GET | No | Active | smoke test |
| `/weather/climate-archive` | GET | Yes | **Primary** | `fetchClimateAnalysis()` |
| `/weather/thermal-grid` | POST | Yes | **Primary** | `getThermalGrid()` |
| `/weather/analyze-wind` | GET | Yes | Active | wind panel |
| `/weather/thermal-profile` | GET | Yes | **Deprecated** (zero callers) | none |

---

## Known Gaps / Enhancement-Later

| Item | Status | Notes |
|---|---|---|
| IMD .grd data files | Enhancement-Later | No files in repo; adapter needs rewrite to use correct imdlib API (`get_data()` + `open_data().get_xarray()`). Tests in `temperature_imd_validation.py` are `xfail`. |
| CMIP6 climate projections | Enhancement-Later | `openMeteoApi.ts` header references `climate-api.open-meteo.com` but not implemented. Stale comment removed. |
| `/weather/thermal-profile` cleanup | Enhancement-Later | Formally deprecated; zero callers. Remove in a future cleanup PR once wind down confirmed. |

---

## Automated Validation

### Smoke tests (CI)
```bash
cd SAT
# Requires: app/ running on localhost:8000 OR FastAPI TestClient
# Open-Meteo is mocked — no live network calls
pytest tests/temperature_smoke.py -v
# Expected: 5 passed

pytest tests/temperature_imd_validation.py -v
# Expected: 2 xfailed (documents Enhancement-Later gap)
```

### Frontend unit tests (CI)
```bash
cd SiteAnalysisToolV3/frontend
npx vitest run src/tests/ecbc-recommendations.test.ts
# Expected: 17 passed — covers all 5 ECBC zones, CDD/HDD dominance, humidity,
# solar threshold, heatwave/cold/humidity seasonal flags, edge cases
```

### Manual QA — draw point
```
1. Open SAT frontend (npm run dev --workspace apps/web)
2. Enable flag: FLAGS=feature.temperature.thermal-profile in .env
3. Draw a point on the map → select Temperature tab
4. AC1: Monthly ComposedChart renders 12 months of tmax/tmin/tavg/feels-like
5. AC2: Annual avg, peak max, lowest min shown in summary tiles
6. AC3: IMAC 20–26°C comfort band visible on chart; comfort-days % tile present
7. AC4: "Envelope Recommendations" section shows ECBC zone, U-value table,
        thermal mass text, insulation priority, glazing spec, seasonal flags
8. AC5: Scroll to bottom → click "Download Temperature Report"
        → 6-page PDF opens; page 6 = temperature analysis with ECBC data
```

### Manual QA — draw polygon (heatmap)
```
1. Draw a polygon on the map → Temperature tab → heatmap renders
2. C/K unit toggle switches colour scale and hover popup
3. Date slider updates displayed title text
4. InsightsPanel (right column) shows "Temperature Insights" — NOT rainfall data
5. ECBC zone badge visible; envelope strategy section rendered
```

### Feature flag gate test
```bash
# Flag OFF:
FLAGS="" curl http://localhost:8000/weather/climate-archive?latitude=12.97&longitude=77.59&start_date=2023-01-01&end_date=2023-12-31&daily=temperature_2m_max
# Expected: HTTP 403 {"detail": "Feature flag disabled: feature.temperature.thermal-profile"}

# Flag ON:
FLAGS=feature.temperature.thermal-profile curl "http://localhost:8000/weather/climate-archive?latitude=12.97&longitude=77.59&start_date=2023-01-01&end_date=2023-12-31&daily=temperature_2m_max,temperature_2m_min"
# Expected: HTTP 200 JSON with daily.temperature_2m_max array
```

### ECBC recommendation spot-check (Bangalore)
```bash
# Bangalore (Hot Semi-Arid, Köppen BSh, ECBC: Hot & Dry, high CDD)
# After running temperature analysis at lat=12.97, lon=77.59:
# Expected ECBC output:
#   Zone: Hot & Dry
#   Wall U: 0.44 W/m²K, Roof U: 0.33 W/m²K, SHGC: 0.25
#   Thermal mass: "High thermal mass (>200 kg/m²)"
#   Insulation: "Roof-first: U-roof ≤ 0.33 W/m²K"
#   Seasonal flags: HEATWAVE (Mar–May), HIGH_HUMIDITY (Jun–Sep)
```

---

## Contract Reference

`SAT/contracts/temperature.yaml` v1.1.0 — see `contracts/CHANGELOG.md` entry for 2026-06-02.

Key schema: `ClimateReport` → `ClimateRecommendations` has optional `climate_zone: string` and `cdd_hdd_ratio: number` added for future backend enrichment (currently populated only by frontend engine).
