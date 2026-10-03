# Org-wide feature gap vs `builder-arch-integ` (2026-10-03)

Compares every repo and branch in the `Site-Analysis` GitHub org against SAT branch `builder-arch-integ` (`ecbc072`).
Method: shallow clones of all branches. Features are compared by file tree, routes and code content, not commit history,
because most repos share no history with SAT. Each "missing" item was confirmed absent from SAT with a grep over
`services/`, `apps/` and `packages/`.

Repos compared: `SAT`, `Builder-Prod` (17 branches), `Builder-Phase-II` (10), `SiteAnalysis_GEE` (2),
`SiteAnalysisV2` (3), `Sprint0_User_Stories` (6).

---

## A. What `builder-arch-integ` has today

### Backend services
| Service | What it computes | Runtime state |
|---|---|---|
| `cadastral` | Karnataka parcel search, district → village hierarchy, parcel GeoJSON, village outlines, nearby LGD villages, live RTC owners and mutations | Live; needs the local parquet lake and `survey_index.db` |
| `contour` | Copernicus GLO-30 contours, 6 slope classes, aspect, 5 buildability classes, hillshade, 5 m transect profile | Code complete; **blocked** by the GEE 403 |
| `flood` | 0–100 flood score and 5-level category, 4 component scores, recommendations | **Mostly heuristic**: only point elevation, rainfall and water distance are measured; the rest are constants |
| `wind` | 5-year mean and max, prevailing direction, 8-point rose, 3 seasons, comfort and wind-load chips | Live; `gust_risk` is always "High" (#90) |
| `temperature` | 12-month max/min profile, thermal-grid heatmap, climate-archive passthrough | Live; falls back to an "Estimated" profile when IMD/Open-Meteo fail |
| `rainfall` | archive, summary, climate profile, anomaly, seasonality, site analysis | **Synthetic** without a GEE key, while still labelled CHIRPS |
| `geo` | OSM zone inference, Bhuvan LULC, KGIS admin context, SoilGrids soil, water bodies and rajakaluve buffers, amenities in 7 categories | Live (depends on Overpass) |
| `infrastructure` | Road access attributes, transit (up to 10), utilities (power line kV, substation, telecom) | Live (depends on Overpass) |
| `planning` | FAR, setbacks, height cap and limiting factor, TOD (metro within 500 m), airport obstacle surface from a 22-airport table | Rule-based; road width defaults to 9 m |
| `future-infra` | Curated growth pipeline (12 Bengaluru + 3 pan-India items, as of 2024-Q4) | **Always empty**: path bug (§E) |
| `land-records` | Deep links to Bhoomi, KAVERI, eCourts, CERSAI, MCA21 | Stub (no data retrieved) |
| `sunpath` | Solstice/equinox paths, solar day, events, orientation, polar SVG, sunlight-hours grid, shadows (single, time series, cumulative), building heights | Live; building heights fall back to category defaults |

### Frontend (`apps/web`)
- Landing page and login, dashboard (mock and session projects), New Analysis map (pin, rectangle or polygon), 7 selectable modules.
- Project workspace with 15 module sections, composite score, detail cards, 2D/3D toggle.
- 3D view (`Scene3D`): extruded OSM buildings, CPU ground shadows, solar arcs, date and hour controls.
- Zoning HUDs: FAR gauge, buildable donut, height envelope with airport line, setback plan, context radar, compliance matrix.
- Contour panel with a transect tool; cadastral explorer (behind `NEXT_PUBLIC_ENABLE_CADASTRAL_EXPLORER`).
- Client-side PDF export (html2canvas + jsPDF, image-only pages), plus CSV, PNG and JSON.

## B. Computed by this branch but missing from the 01-Oct Tubarahalli report
- Shadow studies (single time, time series, cumulative shadow-hour zones) and the sunlight-hours grid.
- Seasonal wind roses and per-season gusts; thermal-grid heatmap.
- Rainfall seasonality, anomaly and climate profile (blocked: synthetic without GEE).
- Connectivity: road attributes, transit, power and telecom (Overpass was down).
- Growth pipeline (path bug).
- Contour, slope, aspect, buildability and transect (GEE 403).
- Flood component breakdown (withheld: defaults).
- KGIS admin context and Bhuvan land use.
- TOD/metro FAR check.
- Setback plan diagram, FAR gauge and height-envelope visuals; 3D massing and sun view.

## C. Features elsewhere in the org that SAT does not have

### Builder-Prod
| Feature | Branch / status | What it adds to a site report |
|---|---|---|
| **2031 statutory zoning at a parcel** (`/zones/at`): plan zones touching the parcel, overlap %, distance to zone edge, position uncertainty, near-edge and inferred flags, sheet QA | `feat/planning-2031-phase0`, WIP (draft PR #20) | "BDA RMP 2031 (Draft): Residential 96.4 %, near edge (±11 m)" in place of OSM-inferred zoning |
| 2031 zone map layers (`/zones`) with native legend; one switch per plan | same | Master-plan extract around the site |
| Drawn plan overlays (`/overlays`): NGT buffer, forest, stream centrelines | same | "NGT buffer covers 12 % of parcel" |
| Planning authority and plan coverage (`/authority`): BDA / Hoskote / Anekal / Nelamangala / BIAAPA / STRR / BMICAPA / DPA, operative vs draft plan | same (UI does not call it yet) | Authority, operative plan, GO reference |
| Plan and source register (`/plans`, `/docs/{id}`): 12 plans, ~203 documents with sha256 | same | Citation table |
| Satellite 2D basemap toggle (white parcel outlines on imagery) | `Cadestral` (default), merged | Parcel on satellite imagery. SAT hard-codes the base map. |
| Single-image deploy (supervisord), `docker-compose.builders.yml` | `feat/sme-round2-fixes` | None (deployment) |

Notes:
- The planning-2031 service clashes with SAT's `services/planning` on name and port; port it as `planning-zones`.
- Its `FLAGS` parser splits on spaces, the same bug SAT fixed for cadastral.
- Kalianpur datum, CockroachDB and the "no data" chips were removed or abandoned upstream, so they are not gaps.

### Builder-Phase-II (`main` / `Builder`; `Builders` where noted)
| # | Feature | Status | Report value |
|---|---|---|---|
| 1 | **GO / CAUTION / NO-GO verdict report** (`services/report`, `/report/go-no-go`, `VerdictReport.tsx`, results page) | Complete; PDF needs WeasyPrint, share link needs Supabase | Headline verdict, red flags first, ranked "confirm to upgrade" list with citations |
| 2 | Parcel verdict dock (`ParcelVerdictDock.tsx`) | Complete | Per-survey verdict on the map |
| 3 | **Deal-killer overlays** (`/geo/overlays`): wetlands, Ramsar, eco-sensitive zones, forest, flood, lakes, rajakaluve, airport, HT lines, gas | Partial (several data files not bundled → "unresolved") | Red/amber/green constraint table with rule and buffer |
| 4 | Authority detection (`/geo/authority`): GBA/BDA/BMRDA/BIAAPA | WIP (best effort) | Governing authority and approval route |
| 5 | Ring and zone resolver (`/geo/ring`, `/geo/zone-resolve`) | Ring complete; official zone layer inactive | Ring I/II/III, TDR zone |
| 6 | **FAR permissible vs achievable** (`/planning/far`) from RMP-2015 tables; road-width band (`/planning/road-width`) | Partial-verified tables | By-right vs entitlement FAR |
| 7 | Development obligations (`/planning/obligations`) | Complete | Parking ECS, mixed-use %, access-road adequacy |
| 8 | Utilities and NOC checklist (`/infrastructure/utilities`) | Complete | BWSSB, BESCOM, KSPCB, Fire, AAI checklist |
| 9 | Connectivity scoring (`/infrastructure/connectivity`) | Complete | Airport/metro/rail/highway distances, access score |
| 10 | Power grid (`/infrastructure/power-grid`) and map overlays | Complete | Nearest line and substation, LT/HT flags |
| 11 | Ownership screen (`/land-records/ownership`) | Complete (no owner names) | Kharab / Gomala / restricted-tenure flags |
| 12 | Price upside and nearest metro (`/future-infra/price-upside`, `/metro-nearest`) | Needs guidance value input | Indicative price-upside range |
| 13 | Terrain (`/flood/terrain`): slope, HAND, cut/fill | Needs GEE | Cut/fill and drainage height |
| 14 | Transport access (`/geo/transport-access`) and overlay | Complete | Metro/rail/highway/airport map |
| 15 | **13 cadastral overlay layers**: encroachment, road width, BWSSB sewerage, power lines, gas, drainage, WRIS lakes, BESCOM, HydroRivers, BBMP storm drains, CGD zones; `/rccms`, `/mutations`, `/parcels-by-bbox` | Complete; needs parquet data | Encroachment flag, utilities near the site |
| 16 | Architect / Builder profile selector (`select-profile`, `ProfileGate`) | Complete (`Builders`, `main`) | Not in the report; filters the module list |
| 17 | KGIS survey-number → parcel (`/geo/parcel`, `ParcelOverlay`) | Complete (`Builders`) | Parcel polygon from a survey number |
| 18 | Site planning card and context dock on New Analysis | Complete | Setbacks, premium FAR, ring, authority for a pin |
| 19 | Confidence scale (authoritative / derived / inferred / unresolved): `packages/confidence`, `LadderBadge` | Complete | A confidence label on every result |
| 20 | Standalone builder report HTML (`builderReportHtml.ts`) | WIP (unused) | Feasibility report with embedded map |
| 21 | OSM building footprints on the 2D map | Complete (flagged) | Existing structures on or near the plot |
| 22 | Satellite basemap (MapTiler) and night mode | Complete; SAT's MapTiler key is revoked | Satellite context |

Flags present in Builder-Phase-II and missing from SAT `packages/flags/src/flags.py`:
- `feature.cadastral.overlays`, `feature.cadastral.explorer`
- `feature.flood.terrain`
- `feature.geo.authority`, `feature.geo.overlays`, `feature.geo.parcel-geometry`, `feature.geo.transport-access`, `feature.geo.zone-resolver`
- `feature.infrastructure.power-grid`, `feature.infrastructure.utilities`
- `feature.land.ownership`
- `feature.planning.far-assembly`, `feature.planning.mixed-use`, `feature.planning.road-width-resolver`
- `feature.report.go-no-go`
- `feature.terrain.analysis`, `feature.simulation.3d` (both unused)

Dropped from SAT by decision (status log issue 11): Keycloak + next-auth, Supabase project API routes, OpenTelemetry, EC2 builder deploy.
Builder-Phase-II is not a superset of SAT: it has no contour service, `/rtc`, `/boundary`, `/nearby` or Parcel & Title page.

### SiteAnalysis_GEE
| Feature | Branch / maturity | Report value |
|---|---|---|
| Sentinel-2 NDVI / NDBI / NDWI with statistics and thumbnails | `main`, working | Vegetation, built-up and water index maps |
| Vegetation health: NDVI, EVI, SAVI, 4 density classes (Sentinel-2 + MODIS) | `main`, working | % vegetated, health gauge |
| ESA WorldCover land cover and class histogram | `main`, working | Land-cover map and % by class |
| FAO GAUL admin boundaries | `main`, `Karthik`, working | Admin context map |
| Open Buildings v3 footprint statistics (count, area spread, per-building NDVI) | `main`, working | Building density, size classes |
| 4-DEM comparison (MERIT, ALOS, SRTM, Copernicus) | `main`, working | Elevation confidence |
| **Satellite flood score**: MERIT DEM, LLAI sinks, MERIT Hydro, HydroSHEDS river distance, Global Flood DB event count, JRC recurrence, CHIRPS | `main`, working | Real component breakdown, historical flood count. SAT's flood score is heuristic. |
| Flood mitigation advice with ₹-lakh cost ranges | `main`, rule-based | Costed recommendations |
| Server-side ReportLab PDF: cover, sections, matplotlib charts, polygon map with north arrow and approximate scale | `main`, basic | Text-selectable PDF (SAT's PDF is image-only) |
| JRC surface water: occurrence, seasonality, change, transitions | `Karthik`, prototype | Water history since 1984 |
| MERIT Hydro HAND, river width, drainage area | `Karthik`, prototype | Height above drainage |
| Hansen forest cover, loss and gain by year | `Karthik`, prototype | Tree-cover loss chart |
| VIIRS NDVI time series | `Karthik`, prototype | Seasonal greenness |
| Open Buildings Temporal (built-up by year) | `Karthik`, prototype | Urbanisation trend |

VIIRS night lights, WorldPop and Landsat LST exist only as dead code with hard-coded defaults, so treat them as missing everywhere.

### SiteAnalysisV2
- `main`: GEE indices (NDVI/NDBI/NDWI, slope, WorldCover, Open Buildings, GAUL), a smaller copy of SiteAnalysis_GEE. Geoman draw and measure tools.
  SAT already has its Bhuvan, KGIS, OSM and auth parts.
- `Karthik`, `Lohith`: UI mockups and placeholders only.

### Sprint0_User_Stories
| Feature | Branch / maturity | Report value |
|---|---|---|
| 34 OSM road-attribute routes: speed, lanes, width, surface, lighting, sidewalks, crosswalks, signals, cycle, parking, bridges, turn restrictions, speed bumps | `Ruchika`, prototype (no tests) | Walkability and street-quality table |
| GIS file upload (SHP, GeoJSON, KML, GeoTIFF) via MinIO | `Vishwas`, proof of concept | Client boundary or survey layers on report maps |
| Cartesian (altitude vs azimuth) sun-path chart | `SolarAnalysis(Karthik)`, working | Second sun-path style |

## D. Roadmap items with no code anywhere in the org
- SAT-11 3D simulation editor (place and edit buildings, terrain mesh, GFA metrics)
- SAT-12 NBC generative engine (typologies, variant scoring)
- SAT-13 energy and embodied carbon (ECBC)
- SAT-14 wind, noise and thermal comfort simulation; UTCI
- SAT-15 BIM/CAD exports (IFC, GLB)
- SAT-16 realtime collaboration and sharing
- Rainfall IDF curves and return periods; 16-sector wind rose (SAT-17 v3); PV yield and irradiance
- Cut/fill exists only in Builder-Phase-II `/flood/terrain` (needs GEE)

## E. Defects found during the inventory (SAT `builder-arch-integ`)
| Defect | Location | Effect |
|---|---|---|
| `_DATA_DIR = parents[3] / "data"` should be `parents[2]` | `services/future-infra/app/services/pipeline_service.py:13` | Resolves to `/data` in the container (the data is at `/app/data`), so the pipeline is silently empty |
| Annual rainfall = 30-year sum of monthly totals ÷ 12 | `services/rainfall/app/services/rainfall_service.py:125` | Annual figure about 2.5× too high |
| Rainfall season labels: "summer" = Jun–Aug, "monsoon" = Sep–Nov | `services/rainfall` | The SW monsoon is labelled summer |
| Two top-level `paths:` keys | `contracts/rainfall.yaml:16,681` | Parsers keep only the second block (archive and summary) |
| Lists `/buildings/extract`, which doesn't exist; omits shadow bbox/address, timeseries and cumulative routes | `contracts/sunpath.yaml` | Contract drift |
| Synthetic rainfall labelled CHIRPS; temperature "Estimated" fallback; flood constants | see `docs/builder-arch-integ-status.md` issue 6 | Breaks the "stubs must be honest" rule |
| Export page reads only Point boundaries | `apps/web/app/project/[id]/export/page.tsx` | Polygon and parcel projects export with Bangalore defaults (status M5) |

## Suggested porting order (report value ÷ effort)
1. Fix §E defects (small, unblock growth pipeline and honest labelling).
2. Satellite basemap toggle (Builder-Prod `Cadestral`): small, high visual value.
3. Builder-Phase-II confidence scale, deal-killer overlays and GO / CAUTION / NO-GO verdict.
4. Builder-Phase-II FAR permissible vs achievable, development obligations, utilities and NOC checklist.
5. Builder-Prod planning-2031 zoning at parcel (once its WIP defects are closed), as `planning-zones`.
6. SiteAnalysis_GEE vegetation, land cover and satellite flood score (once GEE access is restored).

Each port still needs an FVD, contract, flag and smoke test per `docs/integration-rules.md`.
