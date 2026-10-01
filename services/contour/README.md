# Contour Service

FastAPI service for SAT-19 contour analysis. It uses Google Earth Engine's
Copernicus DEM GLO-30 2024 collection (`COPERNICUS/DEM/GLO30_2024_1`, band
`DEM`) to derive contour lines, slope classes, buildability zones, hillshade,
and transect elevation profiles for polygon site boundaries.

## Local Run

```bash
cd services/contour
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
FLAGS=feature.contour.analysis uvicorn app.main:app --port 8010 --reload
```

## Data Source

- Active source: Copernicus DEM GLO-30 2024, DSM, 30m pixels, EGM2008 vertical datum.
- Future source layer: local DEM ingestion for downloaded DEM datasets.

## Limits

- Minimum contour interval: 10m.
- Maximum contour interval: 60m.
- Projects require a polygon boundary.
- Sites below 0.5 ha are rejected because 30m DEM pixels are too coarse.
