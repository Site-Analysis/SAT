# Contour Service Notes

The contour service computes terrain context for polygon site boundaries:
contour LineStrings, slope/aspect statistics, slope classification polygons,
buildability zones, hillshade, and transect elevation profiles.

Current DEM source:
- Copernicus DEM GLO-30 2024: `COPERNICUS/DEM/GLO30_2024_1`, band `DEM`.

Source selection:
- `select_dem_source()` currently returns `copernicus`.
- A later ingestion layer will add support for local downloaded DEM datasets.

Rules:
- Enforce contour interval `10m <= interval <= 60m`.
- Run on port `8010`.
- Gate analysis endpoints with `feature.contour.analysis`.
- Do not use GDAL contour CLI tools; contour lines use `skimage.measure.find_contours`.

Local run:

```bash
FLAGS=feature.contour.analysis uvicorn app.main:app --port 8010
```
