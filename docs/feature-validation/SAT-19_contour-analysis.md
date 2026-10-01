# FVD-19 - Contour Analysis

**Jira Ticket:** SAT-19
**Status:** In Progress — backend + frontend on `feat/contour-analysis`; remaining UI QA in the playbook
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

## Frontend Acceptance Criteria (SAT-19 UI)

| # | Criterion | Implementation |
|---|---|---|
| F1 | Polygon projects can run contour analysis from the UI | `ContourPanel`, `useContourStore.runAnalysis` |
| F2 | Point and circle-buffer projects show a disabled contour state | `deriveContourEligibility`, `ContourEligibilityNotice` |
| F3 | Contour, slope, buildability, and hillshade layers toggle independently | `ContourMapLayers`, `ContourLayerControl`, store `layers` |
| F4 | DEM metadata and warnings visible after analysis | `DemMetadataCard` |
| F5 | Slope statistics include hover/focus/click explanations | `InfoTip`, `SlopeStatsSection` |
| F6 | Transect line has distinct Start and End markers on the map | `TransectPathOverlay` |
| F7 | Transect graph Start/End labels match the map | `TransectProfileChart` |
| F8 | Hovering or scrubbing the graph moves a marker along the map line | `TransectCursorMarker` (imperative subscribe) |
| F9 | Graph point readout shows distance, elevation, slope %, slope class | `TransectPointReadout` |
| F10 | Error states are mapped and preserve prior results | `mapContourError`, store AD-13 |
| F11 | Export/report includes contour summaries, disclaimer, and transect when present | `ContourReportVisual`, `ReportFeaturePage` |
| F12 | Ineligible contour does not contribute a 0 to the site score | WP-8: no `ModuleResult` registered when ineligible |

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

Backend smoke (no live GEE — DEM is monkeypatched):

```bash
pytest tests/contour_smoke.py -v
```

Frontend agent playbook and results: `docs/SAT-19_contour-frontend-agent-qa.md`.
Fix backlog: `docs/SAT-19_contour-frontend-qa-findings.md`.
Implementation plan: `docs/SAT-19_contour-frontend-plan.md`.

Pass 3 (2026-08-25): original blockers QA-001–QA-005 closed. Still open for
sign-off: C-30 (module collapse, human re-check), C-28/C-29 (need a sloped
site — Bellandur fixture was nearly flat), C-53 (full keyboard-only pass).

Local UI check (testing env, flag default-off):

```bash
cd services/contour
FLAGS=feature.contour.analysis uvicorn app.main:app --reload --port 8010

cd apps/web
# .env.local: NEXT_PUBLIC_CONTOUR_API_URL=http://localhost:8010
npm run dev
```
