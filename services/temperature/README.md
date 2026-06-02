# Temperature Service

Annual thermal profile and spatial temperature analysis. Powers the Temperature tab in the SAT frontend.

## Data source

**Primary:** Open-Meteo Archive API (ERA5 reanalysis, 1940-present, no API key required)  
**Enhancement-Later:** IMD imdlib gridded data (`.grd` files) — requires local data files; see AGENTS.md

## Port

8000

## Contract

`contracts/temperature.yaml` (v1.1.0) — live endpoints: `climate-archive`, `thermal-grid`, `analyze-wind`, `health`

## Feature flag

`feature.temperature.thermal-profile`

## Run (from source)

```bash
cd /Volumes/LocalDrive/SiteAnalysisToolV3/backend/Temperature
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

## Run (SAT, after migration)

```bash
cd /Volumes/LocalDrive/SAT
docker-compose up temperature
```

## Key endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/health` | GET | Health check |
| `/weather/climate-archive` | GET | Main panel data (Open-Meteo proxy, disk-cached) |
| `/weather/thermal-grid` | POST | Spatial heatmap for polygon ROI |
| `/weather/analyze-wind` | GET | 5-year wind rose data |
| `/weather/thermal-profile` | GET | **Deprecated** — no frontend callers |
