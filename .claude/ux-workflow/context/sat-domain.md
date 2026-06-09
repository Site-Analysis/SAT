# SAT Domain Context

## What SAT does

Pre-design geospatial site analysis for Indian construction sites.
User drops a pin → SAT returns environmental analysis of that location.

## The 5 live analysis modules

| Module      | What it shows                            | Data sources                          |
|-------------|------------------------------------------|---------------------------------------|
| Sun Path    | Sun movement + shadow simulation          | pvlib/NREL SPA, OSM buildings, GEE    |
| Flood Risk  | 4-component risk score                   | MERIT DEM, JRC water surface, rainfall, soil |
| Temperature | Seasonal thermal heatmap                 | Open-Meteo climate archive            |
| Wind        | Ventilation / prevailing wind analysis   | Open-Meteo                            |
| Rainfall    | Water management analysis                | IMD, Open-Meteo                       |

## Indian regulatory standards (Architecture SME validates these)

| Standard  | What it covers                                         |
|-----------|--------------------------------------------------------|
| NBC 2016  | National Building Code — setbacks, FSI, building norms |
| BBMP DCR  | Bangalore development control regulations              |
| BDA rules | Bangalore Development Authority plot norms             |
| IMD data  | India Meteorological Department — official climate data |

IMPORTANT: The Architecture SME is the authority on these standards.
The agent does not interpret or apply regulatory rules without SME confirmation.

## Target users

**Phase 1 research complete (2026-06-10). Profiles below are confirmed, not hypotheses.**
Full findings: `ux-workflow/context/phase-1-findings.md`

| Persona | Profile | Primary concern | Key tool dependency |
|---------|---------|-----------------|---------------------|
| P01 type — Junior Architect (intern) | 0–3 yrs; thesis or firm intern | Speed, reducing manual data collection, tool simplicity | SketchUp + Ventrysky + data portals (KSRSAC, IMD) |
| P02 type — Junior Architect (practice) | 0–3 yrs; small studio | Dashboard-first, conversational AI, auto-report | Ventrysky + Andrew Marsh + site visits |
| P03 type — Senior Architect Studio Lead | 5–12 yrs | Accurate outputs, professional export, Revit compatibility | SketchUp paid plugins + Revit + Google Earth Pro |
| P04 type — Senior Principal / Director | 12+ yrs | Org data ingest, team adoption, data credibility, licensing | Revit (non-negotiable) + Mapbox + OSM |
| P05 type — Urban Planner / M.Arch | Any | Geospatial overlays, zoning, multi-layer resolution | QGIS + Bhuvan + Survey of India + KSRSAC |

Note: P03, P04, P05 are synthetic SME-derived — verify with real senior interviews in Phase 2+.

## Competitive landscape

| Competitor         | Positioning vs SAT                                      |
|--------------------|----------------------------------------------------------|
| Autodesk Forma     | Global, enterprise, expensive, no India-specific data    |
| TestFit            | Financial feasibility focus, not environmental analysis  |
| QGIS / ArcGIS      | GIS-expert tools — high learning curve for architects    |
| Hypar              | Generative design — SAT's roadmap, not current scope     |

SAT's differentiation: Indian data sources (IMD, GEE India corpus), NBC 2016
compliance, accessible to non-GIS architects, web-first (no install).

## Glossary (use exact terms in all outputs)

| Term   | Meaning                                                       |
|--------|---------------------------------------------------------------|
| FSI    | Floor Space Index — ratio of built area to plot area          |
| NBC    | National Building Code of India (2016 edition)                |
| BBMP   | Bruhat Bengaluru Mahanagara Palike (Bangalore municipal body) |
| BDA    | Bangalore Development Authority                               |
| DEM    | Digital Elevation Model                                       |
| GEE    | Google Earth Engine                                           |
| OSM    | OpenStreetMap                                                 |
| JRC    | Joint Research Centre (EU) — water surface dataset            |
| IMD    | India Meteorological Department                               |
| MERIT  | Multi-Error-Removed Improved-Terrain DEM                      |
