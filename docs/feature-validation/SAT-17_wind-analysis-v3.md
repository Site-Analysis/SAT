# FVD-17 — Wind Analysis V3 (Production Backend)

**Jira Ticket:** SAT-4 [Done] (supersedes FVD-09 POC)
**Status:** Done — V3 in org repo (`Site-Analysis/SiteAnalysisToolV3`)
**Resolved:** SAT-4 resolved 2026-03-26; V3 production backend merged 2026-05
**Type:** Story (supersedes FVD-09)
**Authors:** Vishwas + V3 team
**Repository:** [`Site-Analysis/SiteAnalysisToolV3`](https://github.com/Site-Analysis/SiteAnalysisToolV3) — `backend/Temperature/app/routers/weather.py` + `frontend/src/services/windApi.ts`
**Key Commits:** `685547b` (complete wind analysis frontend), `07b25c9` (open-meteo fallback added), `3657c61` (GEE part completed)

---

## Feature Overview

**User Story:** As an architect, I want wind rose diagrams, monthly statistics, seasonal summaries, and building orientation recommendations for a site, so that I can orient buildings for natural ventilation.

**Supersedes FVD-09:** The original FVD-09 documented a POC at `Vishwas721/sat` (personal repo, commit `55cd75e`) using GEE ERA5 data. V3 replaces this with a production-ready backend endpoint in the Temperature service (`GET /weather/analyze-wind`) using **Open-Meteo Archive API** (ERA5 daily wind data, 10-year lookback), a robust frontend service (`windApi.ts`) with in-flight deduplication, and a `WindResultsPanel.tsx` UI component.

---

## Differences from FVD-09

| Dimension | FVD-09 (POC) | FVD-17 (V3 Production) |
|---|---|---|
| Repository | `Vishwas721/sat` personal repo | `SiteAnalysisToolV3` org target |
| Backend | Standalone `sat_wind_poc.py` | Integrated in Temperature service port 8000 |
| Data source | GEE ERA5-Land `ECMWF/ERA5_LAND/DAILY_AGGR` | Open-Meteo Archive API (no GEE dependency) |
| Wind rose | 16 sectors, GEE-derived | 16 sectors, Open-Meteo daily derived |
| Frontend service | None (no windApi.ts in original) | `windApi.ts` with in-flight dedup + `WindResultsPanel.tsx` |
| Seasonal data | IMD 4-season via GEE | India 4-season (Winter/Pre-Monsoon/Monsoon/Post-Monsoon) |
| Caching | LRU (SAT-212, status unknown) | In-flight deduplication Map in `windApi.ts` |
| Port | TBD (POC only) | 8000 (Temperature service) |

---

## Acceptance Criteria (SAT-4, verified in V3)

| # | Acceptance Criterion | V3 Status |
|---|---|---|
| 1 | ERA5/historical wind data from meteorological source | ✓ Open-Meteo Archive API (ERA5 derived) |
| 2 | Wind rose diagram data — 16 sectors with frequency + speed | ✓ `rose: WindDirectionBucket[]` (16 entries) |
| 3 | Seasonal variation data | ✓ India 4-season grouping |
| 4 | Optimal building orientation recommendation | ✓ `summary.crossVentDir` — perpendicular to dominant direction |
| 5 | Report section / summary data | ✓ `summary: {avgSpeedKph, maxGustKph, calmPct, dominantDir, beaufort, crossVentDir}` |

---

## Code Traceability Matrix

| # | Acceptance Criterion | File | Function / Symbol |
|---|---|---|---|
| 1 | Open-Meteo ERA5 data fetch | `backend/Temperature/app/routers/weather.py` | `analyze_wind(lat, lon)` — `GET /weather/analyze-wind` |
| 1 | Daily wind data fields | `backend/Temperature/app/routers/weather.py` | `wind_speed_10m_max`, `wind_gusts_10m_max`, `wind_direction_10m_dominant` from Open-Meteo |
| 2 | 16-sector wind rose | `frontend/src/services/windApi.ts` | `rose: WindDirectionBucket[]` — frequency % + avg speed kph + max gust kph |
| 2 | Direction labels | `frontend/src/services/windApi.ts` | `DIRS_16 = ["N","NNE","NE","ENE","E","ESE","SE","SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]` |
| 3 | 12-month stats | `frontend/src/services/windApi.ts` | `monthly: WindMonthStat[]` — avg speed, max gust, dominant dir per month |
| 3 | India 4-season groups | `frontend/src/services/windApi.ts` | `seasonal[]`: Winter(Dec-Feb), Pre-Monsoon(Mar-May), Monsoon(Jun-Sep), Post-Monsoon(Oct-Nov) |
| 4 | Cross-vent orientation | `frontend/src/services/windApi.ts` | `summary.crossVentDir` = perpendicular to `dominantDir` (dominant index + 4 sectors = +90°) |
| 5 | Full summary object | `frontend/src/services/windApi.ts` | `summary: {avgSpeedKph, maxGustKph, calmPct, dominantDir, beaufort, crossVentDir}` |
| — | In-flight dedup | `frontend/src/services/windApi.ts` | `_inflight: Map<string, Promise<WindAnalysis>>` — same lat/lon re-uses in-flight promise |
| — | Beaufort scale | `frontend/src/services/windApi.ts` | `beaufort(ms)` — 0 Calm → 8 Severe Gale+ |
| — | Frontend panel | `frontend/src/components/map/WindResultsPanel.tsx` | `WindResultsPanel` — displays rose, monthly, seasonal |
| — | Integration in map | `frontend/src/pages/InteractiveMap.tsx` | `fetchWindAnalysis(lat, lon)` called on polygon draw |

---

## Implementation Breakdown

### Architecture

```
GET /weather/analyze-wind?lat=&lon=
    └── backend/Temperature/app/routers/weather.py: analyze_wind()
        └── Open-Meteo Archive API:
            endpoint: archive-api.open-meteo.com/v1/archive
            fields: wind_speed_10m_max, wind_gusts_10m_max, wind_direction_10m_dominant
            period: current_year - 10  to  current_year - 1
            → daily JSON time series

Frontend: windApi.ts: _doFetch(lat, lon)
    ├── fetch(TEMPERATURE_API_URL + /weather/analyze-wind?lat=&lon=)
    ├── Parse D.time[], D.wind_speed_10m_max[], D.wind_gusts_10m_max[], D.wind_direction_10m_dominant[]
    ├── Build 16-sector rose (22.5° bins, frequencyPct + avgSpeedKph + maxGustKph)
    ├── Build 12-month stats (avgSpeedKph, maxGustKph, dominantDir per month)
    ├── Build India 4-season groups
    └── Return WindAnalysis { lat, lon, startYear, endYear, rose[], monthly[], summary, seasonal[] }
```

### Response Type

```typescript
// frontend/src/services/windApi.ts

interface WindDirectionBucket {
  dir: string;           // "N", "NNE", ...
  deg: number;           // 0, 22.5, 45, ...
  frequencyPct: number;  // % of days wind from this direction
  avgSpeedKph: number;
  maxGustKph: number;
}

interface WindMonthStat {
  month: number;       // 1–12
  label: string;       // "Jan", ...
  avgSpeedKph: number;
  maxGustKph: number;
  dominantDir: string;
}

interface WindAnalysis {
  lat: number; lon: number;
  startYear: number; endYear: number;
  rose: WindDirectionBucket[];    // 16 entries
  monthly: WindMonthStat[];       // 12 entries
  summary: {
    avgSpeedKph: number;
    maxGustKph: number;
    calmPct: number;
    dominantDir: string;
    beaufort: string;
    crossVentDir: string;   // perpendicular to dominant (building orientation guide)
  };
  seasonal: { label: string; avgSpeedKph: number; dominantDir: string; }[];
}
```

### Technology Stack

| Component | Technology |
|---|---|
| Backend | FastAPI (Python) — Temperature service port 8000 |
| Data source | Open-Meteo Archive API (ERA5 daily, no GEE dependency) |
| Date range | 10-year lookback from current year |
| Wind math | `math.round(((dir % 360 + 360) / 22.5)) % 16` — sector binning |
| Frontend service | TypeScript — `windApi.ts`, in-flight dedup via `Map<key, Promise>` |
| UI | `WindResultsPanel.tsx` |

---

## Automated Validation Plan

> Backend port: 8000. Start: `uvicorn app.main:app --reload --port 8000` from `backend/Temperature/`

### AC-1 & AC-2: Wind rose data

```bash
curl -s "http://localhost:8000/weather/analyze-wind?lat=12.9716&lon=77.5946" \
  | python3 -c "
import sys, json
d = json.load(sys.stdin)
# Backend returns raw daily data; frontend post-processes into rose
# Verify raw fields present:
daily = d.get('daily', d)  # may be nested
print('Data source: Open-Meteo Archive API')
print('Keys:', list(d.keys()))
"
```

### Frontend service test (browser or node)

```typescript
import { fetchWindAnalysis } from '@/services/windApi';

const result = await fetchWindAnalysis(12.9716, 77.5946);
console.assert(result.rose.length === 16, `Expected 16 rose sectors, got ${result.rose.length}`);

const totalFreq = result.rose.reduce((s, b) => s + b.frequencyPct, 0);
console.assert(Math.abs(totalFreq - 100) < 5, `Frequencies should sum to ~100, got ${totalFreq}`);

console.assert(result.monthly.length === 12, 'Expected 12 months');
console.assert(result.seasonal.length === 4, 'Expected 4 seasons');

console.log('Dominant direction:', result.summary.dominantDir);
console.log('Cross-vent direction:', result.summary.crossVentDir);
console.log('Avg speed:', result.summary.avgSpeedKph.toFixed(1), 'km/h');
console.log('Beaufort:', result.summary.beaufort);
console.log('Data range:', result.startYear, '–', result.endYear);
```

### In-flight deduplication check

```typescript
// Two simultaneous calls to same lat/lon should share one fetch:
const start = Date.now();
const [r1, r2] = await Promise.all([
  fetchWindAnalysis(12.9716, 77.5946),
  fetchWindAnalysis(12.9716, 77.5946),
]);
const elapsed = Date.now() - start;
console.assert(r1 === r2, 'Both calls should return same object reference (dedup)');
console.log('Elapsed for both (should be ~1 fetch):', elapsed, 'ms');
```

---

## Outstanding Actions

1. **Push to org** — `backend/Temperature/` + `frontend/src/services/windApi.ts` exist only in local V3. Push to `Site-Analysis` org before integration.
2. **Close FVD-09 gap** — Outstanding actions in FVD-09 (no `windApi.ts`, no frontend) are now resolved in V3. Update FVD-09 to mark "Superseded by FVD-17" and record V3 as the integration target.
3. **Open-Meteo rate limits** — Unlike GEE, Open-Meteo Archive API has public rate limits (~10,000 req/day free tier). Confirm if production volume needs a commercial key.
4. **Missing fallback** — FVD-09 mentioned SAT-211 (Open-Meteo fallback to GEE). V3 uses Open-Meteo as primary (no GEE); no fallback to a secondary source found. Acceptable if Open-Meteo uptime is sufficient.
5. **LRU server cache** — SAT-212 specified server-side LRU caching. V3 has client-side in-flight dedup only. Server-side caching for repeated lat/lon queries not implemented.
