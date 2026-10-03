# Plan — Org feature-gap list + "Qnit Bengaluru Case Studies" capability showcase

## Context
The 11-page Tubarahalli report was made offline on 01 Oct 2026 by a matplotlib script outside the repo, because GEE and
Overpass were failing (`docs/builder-arch-integ-status.md`). It covers 11 of 14 analysis areas and names its data
sources on every page. The user wants:
1. **A feature-gap list:** what exists anywhere in the Site-Analysis org (6 repos, every branch) but not in SAT
   `builder-arch-integ`, plus what this branch can compute that the report never showed.
2. **A lead-generation showcase PDF** built on the same report structure, with richer visuals. It covers 5 Bengaluru case-study sites
   (Whitefield, Sarjapur Road, Devanahalli, Electronic City, Yelahanka/Hebbal) and **removes Tubarahalli entirely**.
   - Every number is real, produced by SAT's own services run here.
   - Projected capabilities carry a small **"Illustrative preview"** tag.
   - No data source or method is named in the body.
   - Footer: "© 2026 Qnit. All rights reserved." plus one small-print line of the credits third-party licences require.

## Recorded decisions
- Gap scope: the whole org, all branches. Output: `docs/org-feature-gap.md` on `builder-arch-integ` (commit and push) plus a chat summary.
- Showcase: 5 sites; Tubarahalli removed, so no survey numbers, owners or court cases. Per-panel Illustrative tag. Qnit © plus licence credits.
- User will open network access. User will upload `site.json`; with Tubarahalli removed, it is only a reference for chart styling and figure formats.
- **Flagship (full detail): Sarjapur Road site.** It has lakes and storm-drain buffers, a planned metro line (Phase 3 Hebbal–Sarjapur) and residential growth.
  The other 4 sites are compact case studies. The user can swap the flagship at approval.

## Update 2026-10-03 (latest user message)
- **No auth of any kind.** This build only generates the report. Run SAT services exactly as they are (they have no auth in this
  branch). Do not add login, tokens, Supabase or Keycloak anywhere, and do not use Builder-Prod's planning-2031 service
  (it needs Keycloak JWT); its panel stays *Illustrative*. Do not touch `.env`, `apps/web` or any repo code.
- User says the 7 domains are now on the allowed list. **Step 0 on approval:** re-run the reachability check. As of this
  turn every host still returned 403 CONNECT from the egress proxy (status endpoint shows rejections at 16:57:59–16:58:01Z),
  so the change likely applies only to new sessions or needs a container restart. If it still fails, stop and ask the user to
  re-apply it or start a new session. Do not work around the policy.
- Already done: `docs/org-feature-gap.md` written (uncommitted; the commit/push was denied by the permission classifier
  and is left to the user); scratchpad venvs (`venv-svc`, `venv-temp`), `showcase/` with Inter fonts, and
  `run_services.sh` (7 services healthy on 8000–8007).

## Update — uploaded originals (`build_report.py`, `run.js`, `site.json`)
Read in full. They change the build approach in three ways; nothing else in the plan changes.
- **Reuse the frontend's analysis layer instead of raw service calls.** `run.js` compiles `apps/web/lib/api/analysis.ts` to
  `out/api/analysis.js` and calls `getFloodAnalysis`, `getWindAnalysis`, `getZoningAnalysis`, `getPlanningAnalysis`,
  `getSoilAnalysis`, `getWaterConstraintsAnalysis`, `getAmenitiesAnalysis` and so on, writing `results.json`. That layer
  already turns service output into `indicators`, `detailMetrics`, `qualitative` chips, `recommendations` and chart series,
  which `build_report.py` renders. Do the same per site: compile the file with `tsc` into the scratchpad (no repo edits), point it at the
  local services (first verify how `analysis.ts` reads its service base URLs; fall back to the raw-service calls in the plan if it can't be pointed at them), run it against each site's lat/lng and plot area.
- **Reuse `build_report.py`'s layout, not its content.** Keep the helpers (`page()`, `table()`, `note()`, `img()`, `rows_of()`,
  `detail_tables()`, `qual()`, `satellite_map()` tile stitcher, `mercator_px`, `dms`, `kxy/area_m2/dist_m`), the CSS and the palette
  (`GREEN #306223`, `MINT #DAEBE3`, `BG #F2EDE8`), and the 0–100 confidence rubric (40% authority + 30% site fit + 30% recency),
  re-rated per site. Rendering stays HTML → PDF, but with Playwright Chromium here (it used Mac Chrome).
- **Do not carry over:** the Tubarahalli polygon, the WhatsApp survey sketch, RCCMS owner/party names, cadastral calls to
  `localhost:8011`, the `/tmp/om.json` ERA5 file (re-fetch per site), hard-coded 1,944 m² / "Survey 54" text, and every "Data sources",
  "Source: …" and "Esri World Imagery" caption. Its footers lack a © line; add it. `site.json` is used only as the pattern for each
  site's `{lat, lng, pts}`.
- **Fixes the original needs:** its confidence table names sources (ERA5, NREL SPA, ISRIC, OpenStreetMap), so the case-study
  version shows only Source / Site fit / Recency scores with a neutral basis line; its zoning page links to OpenCity URLs, which are removed.

## Prerequisite (user action)
In the environment settings (Network access → Custom; keep the package-manager defaults), allow:
`archive-api.open-meteo.com`, `api.open-meteo.com`, `rest.isric.org`, `overpass-api.de`, `server.arcgisonline.com`,
`bhuvan-vec2.nrsc.gov.in`, `kgis.ksrsac.in`. GEE has no working key, so contour/slope/hillshade and the satellite-index layers are
**Illustrative**.

---

## Part 1 — `docs/org-feature-gap.md`
**A. What `builder-arch-integ` does today:** 12 services (one line each, with live, degraded or stub status) and frontend modules.

**B. Computed by the branch but missing from the Oct-1 report:**
- Shadow studies (single, time series, cumulative) and the sunlight-hours grid.
- Seasonal wind roses and comfort chips.
- Thermal grid heatmap.
- Rainfall seasonality, anomaly and climate profile.
- Connectivity: road attributes, transit, power and telecom.
- Growth pipeline.
- Contour, slope, aspect, buildability and transect (blocked by GEE).
- Flood components.
- KGIS and Bhuvan land use.
- TOD/metro FAR.
- Setback plan, FAR gauge and height-envelope HUDs.
- 3D massing and sun view.

**C. Elsewhere in the org, missing from SAT:**
- Builder-Prod `feat/planning-2031-phase0` (WIP, draft PR):
  - 2031 statutory zoning at a parcel (`/zones/at`: overlap %, edge distance, uncertainty) for BDA RMP 2031, Hoskote and Anekal.
  - Zone map layers, NGT/forest/stream overlays, planning-authority and coverage resolver, plan and source register.
  - Port and name clash with SAT `services/planning`.
- Builder-Prod `Cadestral`: Esri satellite 2D basemap toggle.
- Builder-Prod `feat/sme-round2-fixes`: single-image deploy (supervisord). Not a feature. It also commits a plaintext Keycloak admin password, which needs flagging.
- SiteAnalysis_GEE `main`:
  - NDVI/EVI/SAVI and NDBI/NDWI.
  - ESA WorldCover land cover.
  - FAO GAUL admin boundaries.
  - Open Buildings v3 footprint statistics.
  - 4-DEM comparison.
  - Satellite-based flood score (MERIT, LLAI sinks, HydroSHEDS, Global Flood DB, JRC).
  - Flood mitigation advice with ₹ costs.
  - Server-side ReportLab PDF with north arrow and scale.
- SiteAnalysis_GEE `Karthik`:
  - JRC water occurrence, change and transitions.
  - MERIT Hydro HAND, river width and drainage area.
  - Hansen forest loss.
  - VIIRS NDVI time series.
  - Open Buildings Temporal urban growth.
- SiteAnalysisV2 `main`: GEE indices plus a Geoman measure UI. SAT already has Bhuvan, KGIS and auth.
- Sprint0 `Ruchika`: 34 OSM road-attribute routes (walkability, signals, sidewalks, cycle, parking).
- Sprint0 `Vishwas`: GIS file upload (SHP, GeoJSON, KML, GeoTIFF).
- Sprint0 `SolarAnalysis`: Cartesian sun-path chart.
- Builder-Phase-II `main`/`Builder`:
  - GO / CAUTION / NO-GO verdict report service (`services/report`, `VerdictReport.tsx`, WeasyPrint PDF, share link).
  - Parcel verdict dock.
  - Deal-killer overlays (`/geo/overlays`: wetlands, Ramsar, eco-sensitive zones, rajakaluve, airport, HT lines, gas).
  - Authority detection (`/geo/authority`, GBA/BDA/BMRDA/BIAAPA).
  - Ring and zone resolver.
  - FAR permissible vs achievable from RMP-2015 tables (`/planning/far`), road-width band.
  - Development obligations (parking ECS, mixed use).
  - Utilities and NOC checklist.
  - Connectivity scoring, power grid and transport access overlays.
  - Ownership screen (kharab/gomala flags).
  - Price upside and nearest metro.
  - `/flood/terrain` (HAND, cut/fill).
  - 13 cadastral overlay layers (encroachment, road width, sewerage, storm drains, gas, lakes, rivers, BESCOM).
  - Confidence scale (authoritative/derived/inferred/unresolved).
  - OSM building footprints on 2D, MapTiler satellite and night mode.
  - 16 flags missing from SAT's `flags.py`.
- Builder-Phase-II `Builders`: Architect/Builder profile selector, KGIS survey→parcel (`/geo/parcel`).
- Builder-Phase-II, dropped by decision: Keycloak, Supabase project API, OpenTelemetry, EC2 deploy.

**D. Roadmap FVDs with no code anywhere:** 3D simulation editor, NBC generative, energy/carbon, wind/noise comfort simulation,
BIM/CAD export, realtime collaboration, UTCI, IDF curves, cut/fill, PV yield.

**E. Defects found during inventory:**
- future-infra `_DATA_DIR` path bug (`parents[3]` should be `parents[2]`).
- rainfall `climate-profile` annual total is about 2.5× too high.
- Rainfall season labels are shifted.
- `rainfall.yaml` has duplicate `paths:` keys.
- `sunpath.yaml` drift.
- The planning-2031 flag parser splits on spaces.

Commit `docs: org-wide feature gap vs builder-arch-integ` and run `git push -u origin builder-arch-integ`. No code changes.

## Part 2 — Showcase PDF
### Tooling (scratchpad `showcase/`, not in the repo)
- `sites.json`: 5 polygons of about 0.5–1.5 ha each.
  - Each plot is chosen from satellite tiles as open or under development, in its corridor.
  - Labels read "Site B — Sarjapur Road corridor" etc. No survey numbers.
- `fetch.py`: calls the SAT services and caches the raw JSON per site.
- `build.py`: Jinja2 HTML, with charts from matplotlib (SVG). Geometry uses shapely and pyproj; sun calculations use pvlib; satellite tiles are stitched with Pillow.
- `render.mjs`: global Playwright 1.56 with `/opt/pw-browsers` Chromium renders A4 PDFs with real text, vector charts, CSS page counters and running footers.
- Fonts come from `@fontsource/inter` (npm), inlined. The palette reuses the report's Qnit green and orange.
- Services run from the repo with python3.11 venvs in the scratchpad: wind, geo, sunpath, temperature, planning, infrastructure and flood.
  `FLAGS=` lists their flags. No repo files change.

### Data pipeline and honesty gate (`fetch.py`)
**Calls per site:**
- `/wind/analyze`.
- `/geo/zone|soil|water-constraints|amenities` (with KGIS).
- `/planning/analyze`, using the measured plot area.
- `/infrastructure/analyze`.
- Sunpath `/annual`, `/orientation` and `/shadow/sunlight-hours` (+ `/shadow/cumulative/bbox` if buildings resolve).
- Temperature `/weather/climate-archive` (last 12 months of daily rain, Tmax and Tmin).
- Flood `/flood/analyze`, using only point elevation, days over 100 mm and distance to water.
- Growth items come straight from `services/future-infra/data/bengaluru_pipeline.json`, because the endpoint has a path bug. They are shown by distance, with
  status labelled "as last reviewed".
- Satellite tiles at zoom 17–18.

**Dropped or never used:**
- The rainfall service (CHIRPS needs GEE, so its data would be synthetic).
- The temperature "Estimated" fallback.
- Flood constant defaults (elevation range 10, slope 0, flow accumulation).
- Soil default fills.
- `gust_risk`, which is always "High" (#90).

**Labelled as assumptions:** road width "assumed 9 m" when nothing is mapped.

`build.py` reads only the cache and asserts that every printed number traces to it or to a deterministic calculation.

### Document (about 26–30 A4 pages)
1. **Cover:** "Bengaluru Site Intelligence — Case Studies 2026", a collage of the 5 site thumbnails.
2. **What Qnit analyses:** capability matrix of about 18 areas with icons, marked *Live* or *Illustrative preview*.
3. **Bengaluru overview map:** 5 pins with a one-line headline each.
4. **Side-by-side dashboard:**
   - Metrics for all 5 sites: buildable area, FAR, height cap or airport limit, 12-month rain, mean wind, soil bearing, amenities within 2 km, nearest water buffer, connectivity score, growth projects within 10 km.
   - A radar overlay of the scores.
5. **Flagship, Sarjapur Road (about 11 pages):**
   - Snapshot: satellite hero, KPI tiles, overall score gauge, coverage ring (14 of 14, with projected areas tagged).
   - Boundary geometry and edge and orientation table.
   - Zoning and capacity: FAR gauge, setback plan (inward buffers with shapely), height envelope with the airport line, FAR scenarios by road width, TOD check.
   - 3D massing envelope *(Illustrative)*.
   - Sun: polar diagram, elevation chart, annual sunrise/sunset band, shadow-length table, facade exposure, sunlight-hours grid.
   - Wind: annual rose plus 3 seasonal roses, comfort chips, orientation arrow over the site.
   - Climate: monthly rain and temperature band, rainy days, hottest day and coolest night, seasonal donut.
   - Terrain: point elevation (real); contour, slope and buildability map *(Illustrative)*.
   - Water and drainage: real buffer rings and storm-drain distances; flood-depth map *(Illustrative)*.
   - Soil: texture triangle with the site point, bearing class.
   - Connectivity: nearest road attributes and transit distances (real); drive-time isochrones *(Illustrative)*.
   - Amenities: category pins on satellite imagery, 2 km ring, bars.
   - Growth pipeline timeline.
   - Title and records workflow *(Illustrative, no records)*.
   - 2031 zoning-at-parcel panel *(Illustrative, from planning-2031 WIP)*.
   - Deal-killer overlay table, red/amber/green. Rows use real SAT data where it exists: storm-drain and water buffers, airport height surface,
     HT line distance. The other rows are *Illustrative*.
   - Development obligations and NOC checklist *(Illustrative)*.
   - Opening **GO / CAUTION / NO-GO verdict card** built from the real constraint rows, using the confidence scale
     (confirmed / derived / indicative).
   - Recommendations.
6. **Four compact case studies (3 pages each):** hero map plus KPIs; sun, wind, climate and soil strip; zoning, constraints and highlights.
7. **What's next on the platform:** gap-list features as *Illustrative preview* (NDVI/land cover, HAND/flood history,
   energy and carbon, BIM/CAD export, generative massing, collaboration).
8. **Back page:** call to action and a disclaimer: this is a desk-based screening, Illustrative panels show platform capability and are not site measurements,
   and figures should be verified with the authorities. Then the © line and credits:
   "Map data © OpenStreetMap contributors · Imagery © Esri and its data providers · Soil data © ISRIC (CC BY 4.0) ·
   Weather data by Open-Meteo.com, contains modified Copernicus Climate Change Service information".

## Verification
- **`pdftotext` gate (scripted):** ERA5, Open-Meteo, OpenStreetMap/OSM, SoilGrids/ISRIC, Esri, pvlib, NREL, GEE/Earth Engine,
  Copernicus, Overpass, CHIRPS, Bhuvan, KGIS and opencity must appear **only** on the credits line. The © line must appear on every page.
- **Build assertions:** every figure is traceable to the cache, and every Illustrative panel has its tag.
- **Visual check:** `pdftoppm` every page to PNG and inspect each one for overflow, legibility and tag placement. The PDF must be under 15 MB.
- **Gap doc:** spot-check its claims with `git -C <clone> show origin/<branch>:<path>` and SAT greps.
- **Delivery:** the PDF goes out with SendUserFile. Build scripts stay in the scratchpad unless the user asks to commit them (no PR).
