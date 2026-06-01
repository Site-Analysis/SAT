# FVD-18 — Rainfall & Precipitation Analysis (CHIRPS)

**Jira Ticket:** SAT-11
**Status:** Done — V3 in org repo (`Site-Analysis/SiteAnalysisToolV3`)
**Resolved:** 2026-03-23 (commit `9a548ef`)
**Type:** New Feature
**Authors:** Tanmay C J
**Repository:** [`Site-Analysis/SiteAnalysisToolV3`](https://github.com/Site-Analysis/SiteAnalysisToolV3) — `backend/Rainfall/`, `frontend/src/services/rainfallApi.ts`, `frontend/src/components/map/`
**Latest Commit:** `9a548ef` (2026-03-23, `Site-Analysis/SiteAnalysisToolV3` main)

---

## Feature Overview

**User Story:** As a site analyst, I want to query historical precipitation data for any point or polygon on the map, so that I can assess rainfall patterns, seasonal variability, and water management risk for a proposed site.

**Business Value:** Dedicated precipitation analysis service separate from flood risk scoring (FVD-04). Returns full daily time series + aggregated statistics (mean/sum/min/max/std_dev) for any user-drawn polygon or clicked point. Supports three satellite datasets (CHIRPS Daily, CHIRPS Monthly, PERSIANN-CDR). Full frontend panel with charts and result view wired to the InteractiveMap page.

---

## Acceptance Criteria (derived)

| # | Acceptance Criterion |
|---|---|
| 1 | Query daily precipitation for a lat/lng point over a user-specified date range |
| 2 | Query mean areal precipitation for a polygon over a user-specified date range |
| 3 | Return full daily time series (`DailyPrecipitation[]`) |
| 4 | Return aggregated stats: mean, sum, min, max, std_dev, count |
| 5 | Support three datasets: `CHIRPS_DAILY`, `CHIRPS_MONTHLY`, `PERSIANN_CDR` |
| 6 | Frontend panel (`RainfallAnalysisPanel`) allows date range + dataset selection |
| 7 | Results displayed in `RainfallResultView` (charts + summary stats) |
| 8 | Service runs on port 8004; base URL from `VITE_RAINFALL_API_URL` env var |

---

## Code Traceability Matrix

| # | File | Function / Symbol |
|---|---|---|
| 1 | `backend/Rainfall/app/main.py` | `POST /api/v1/precipitation/point` → `query_point_precipitation()` |
| 2 | `backend/Rainfall/app/main.py` | `POST /api/v1/precipitation/polygon` → `query_polygon_precipitation()` |
| 1–2 | `backend/Rainfall/app/ee_service.py` | `GEEService.get_point_precipitation()` |
| 2 | `backend/Rainfall/app/ee_service.py` | `GEEService.get_polygon_precipitation()` |
| 3–4 | `backend/Rainfall/app/models.py` | `DailyPrecipitation`, `AggregatedStats` |
| 1 | `backend/Rainfall/app/models.py` | `PointPrecipitationRequest`, `PointPrecipitationResponse` |
| 2 | `backend/Rainfall/app/models.py` | `PolygonPrecipitationRequest`, `PolygonPrecipitationResponse` |
| 5 | `backend/Rainfall/app/ee_service.py` | `GEEService.DATASETS: {"CHIRPS_DAILY": "UCSB-CHG/CHIRPS/DAILY", "CHIRPS_MONTHLY": "UCSB-CHG/CHIRPS/MONTHLY", "PERSIANN_CDR": "NOAA/PERSIANN-CDR"}` |
| 6 | `frontend/src/components/map/RainfallAnalysisPanel.tsx` | `RainfallAnalysisPanel` (385 lines) |
| 7 | `frontend/src/components/map/RainfallResultView.tsx` | `RainfallResultView` (231 lines) |
| 1–2 | `frontend/src/services/rainfallApi.ts` | `queryPointPrecipitation()`, `queryPolygonPrecipitation()` |
| 8 | `frontend/src/services/rainfallApi.ts` | `RAINFALL_API_BASE_URL = VITE_RAINFALL_API_URL \|\| 'http://127.0.0.1:8004/api/v1'` |
| — | `frontend/src/pages/InteractiveMap.tsx` | Rainfall panel integrated (+92 lines in commit) |
| — | `frontend/src/components/map/AnalysisResultWindow.tsx` | Rainfall result tab added |

---

## Implementation Breakdown

### Architecture

```
User draws polygon / clicks point on InteractiveMap
    └── RainfallAnalysisPanel
        ├── Dataset selector: CHIRPS_DAILY | CHIRPS_MONTHLY | PERSIANN_CDR
        ├── Date range picker: start_date, end_date (YYYY-MM-DD)
        └── On submit → rainfallApi.ts
            ├── queryPointPrecipitation(lon, lat, start, end, dataset)
            │     POST http://127.0.0.1:8004/api/v1/precipitation/point
            └── queryPolygonPrecipitation(coords[], start, end, dataset)
                  POST http://127.0.0.1:8004/api/v1/precipitation/polygon

Backend (port 8004):
    main.py → GEEService
        ├── ee.ImageCollection(dataset_id).filterDate(start, end)
        ├── Point: .getRegion() at [lon, lat] → daily values list
        └── Polygon: .map(compute_mean) → mean per image over polygon

Response:
    ├── daily_data: [{date, precipitation}] — full time series
    └── aggregated_stats: {mean, sum, min, max, std_dev, count}

RainfallResultView:
    ├── Time series chart (daily_data)
    └── Summary cards (aggregated_stats)
```

### Datasets

| Key | GEE Collection ID | Resolution | Coverage |
|---|---|---|---|
| `CHIRPS_DAILY` (default) | `UCSB-CHG/CHIRPS/DAILY` | 0.05° (~5 km) | 1981–present |
| `CHIRPS_MONTHLY` | `UCSB-CHG/CHIRPS/MONTHLY` | 0.05° | 1981–present |
| `PERSIANN_CDR` | `NOAA/PERSIANN-CDR` | 0.25° (~25 km) | 1983–present |

### Technology Stack

| Component | Technology |
|---|---|
| Backend | FastAPI + Google Earth Engine Python API |
| Precipitation data | CHIRPS Daily/Monthly (UCSB-CHG), PERSIANN-CDR (NOAA) |
| Auth | GEE service account (`GEE_JSON_KEY_PATH` env var) |
| Frontend panel | React + TypeScript — `RainfallAnalysisPanel.tsx` |
| Chart | `RainfallResultView.tsx` (internal chart component) |
| Port | 8004 (distinct from Temperature/8000, SunPath/8001, FloodPlains/8002, Terrain/8003) |

### Data Models

```typescript
// Request
interface PointPrecipitationRequest {
  longitude: number; latitude: number;
  start_date: string; end_date: string;  // YYYY-MM-DD
  dataset?: string;   // default: "CHIRPS_DAILY"
}

interface PolygonPrecipitationRequest {
  coordinates: [number, number][];  // [lng, lat] pairs, auto-closed
  start_date: string; end_date: string;
  dataset?: string;
}

// Response
interface PointPrecipitationResponse {
  query_type: "point";
  location: { longitude: number; latitude: number };
  daily_data: DailyPrecipitation[];       // [{date, precipitation}]
  aggregated_stats: AggregatedStats;      // mean/sum/min/max/std_dev/count
  unit: "mm/day";
}
```

---

## Automated Validation Plan

> Requires Rainfall backend running (`uvicorn app.main:app --port 8004`) with GEE credentials configured.

### AC-1: Point precipitation query

```bash
curl -s -X POST http://127.0.0.1:8004/api/v1/precipitation/point \
  -H "Content-Type: application/json" \
  -d '{
    "longitude": 77.5946,
    "latitude": 12.9716,
    "start_date": "2023-06-01",
    "end_date": "2023-08-31",
    "dataset": "CHIRPS_DAILY"
  }' | python3 -m json.tool
# Expect: daily_data array, aggregated_stats.sum > 0 (Bengaluru monsoon)
```

### AC-2: Polygon precipitation query

```bash
curl -s -X POST http://127.0.0.1:8004/api/v1/precipitation/polygon \
  -H "Content-Type: application/json" \
  -d '{
    "coordinates": [[77.58,12.97],[77.62,12.97],[77.62,13.01],[77.58,13.01]],
    "start_date": "2023-06-01",
    "end_date": "2023-08-31"
  }' | python3 -m json.tool
# Expect: daily_data, description = "Mean precipitation across the polygon area"
```

### AC-4: Aggregated stats sanity

```python
import requests

resp = requests.post("http://127.0.0.1:8004/api/v1/precipitation/point", json={
    "longitude": 77.5946, "latitude": 12.9716,
    "start_date": "2023-01-01", "end_date": "2023-12-31",
    "dataset": "CHIRPS_DAILY"
}).json()

stats = resp["aggregated_stats"]
assert stats["count"] > 300, "Should have ~365 daily records"
assert stats["sum"] > 0, "Annual rainfall must be > 0"
assert stats["max"] >= stats["mean"], "Max >= mean"
assert stats["mean"] >= stats["min"], "Mean >= min"
print(f"Annual rainfall: {stats['sum']:.1f} mm | Mean: {stats['mean']:.2f} mm/day | Days: {stats['count']}")
```

### AC-5: Dataset fallback (PERSIANN-CDR)

```bash
curl -s -X POST http://127.0.0.1:8004/api/v1/precipitation/point \
  -H "Content-Type: application/json" \
  -d '{"longitude":77.5946,"latitude":12.9716,"start_date":"2020-01-01","end_date":"2020-03-31","dataset":"PERSIANN_CDR"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('dataset:', d['dataset'], '| count:', d['aggregated_stats']['count'])"
```

### Health check

```bash
curl http://127.0.0.1:8004/health
# Expect: {"status": "ok", ...}
```

---

## Outstanding Actions

1. **Port 8004 not in docker-compose** — `backend/run_server.py` adds port 8004 but `docker-compose.yml` may not expose it. Verify Rainfall service is in compose config alongside Temperature (8000), SunPath (8001), FloodPlains (8002), Terrain (8003).
2. **No `contracts/rainfall.yaml`** — OpenAPI contract not written. Required before SAT monorepo integration (see integration-rules.md). Derive from `models.py`.
3. **`VITE_RAINFALL_API_URL` not in `.env.example`** — New env var for frontend. Add to example env and CI secrets.
4. **Attribution confusion** — SAT Open Issues listed this as "Karthik claims Done." Actual author is Tanmay C J (commit `9a548ef`). Correct in Jira SAT-11 and team planning docs.
5. **FVD-04 overlap note** — FVD-04 (Flood Risk) uses CHIRPS annual rainfall as one input to the flood score. That is read-only usage inside `gee_utils.py`. This FVD-18 feature exposes full daily time series as a standalone API — no duplication of logic, but the two should share or re-use the GEE CHIRPS query rather than duplicating.
6. **Jira ticket** — SAT-11 (In Progress). Close once port 8004 is confirmed in docker-compose and contract written.
