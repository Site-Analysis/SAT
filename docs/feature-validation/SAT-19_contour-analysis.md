# FVD-19 - Contour Analysis

**Jira Ticket:** SAT-19
**Status:** In Progress
**Type:** New Feature
**Repository:** `Site-Analysis/SAT`

---

## Feature Overview

**User Story:** As an architect or site analyst, I want contour, slope, aspect,
buildability, and transect profiles for a drawn site polygon, so that I can
assess terrain constraints before concept design.

**Business Value:** Replaces early manual DEM inspection with cited terrain
layers that can be shown directly on the map and included in feasibility reports.

---

## Acceptance Criteria

| # | Acceptance Criterion |
|---|---|
| 1 | Generate contour LineStrings for a polygon site boundary |
| 2 | Compute slope percentage and classify slope into six classes |
| 3 | Compute dominant aspect plus north-facing and south-facing percentages |
| 4 | Generate buildability zones from slope classes |
| 5 | Generate a hillshade image overlay |
| 6 | Draw a transect line and return sampled elevation profile points |
| 7 | Enforce contour interval range of 10m to 60m |
| 8 | Reject non-polygon or too-small sites for DEM analysis |

---

## Data Sources

| Source | Earth Engine ID | Resolution | Notes |
|---|---|---|---|
| Copernicus DEM GLO-30 2024 | `COPERNICUS/DEM/GLO30_2024_1` | 30m | DSM, EGM2008 vertical datum |

Future work will add a local DEM ingestion layer for the downloaded DEM model
dataset. That layer should plug into the contour service behind the same DEM
fetch interface.

---

## Known Limitations

- Copernicus GLO-30 is a DSM, not bare-earth terrain; buildings and canopy can
  affect elevations.
- 30m pixels are not reliable for very small parcels; sites below 0.5 ha are
  rejected.
- Minimum contour interval is fixed at 10m even if local data later supports
  finer contours.
- Live DEM fetch requires Google Earth Engine credentials.

---

## Validation Plan

```bash
pytest tests/contour_smoke.py -v
```

Smoke tests monkeypatch DEM fetches with deterministic arrays so CI does not
need live GEE.
