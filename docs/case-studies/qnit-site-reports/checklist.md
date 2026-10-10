# Qnit Site Report — section checklist

Template: *Qnit Report Template (13 pages)*. Reports built: **Site 3 — Kogilu** (`QNIT-BLR-S03`), **Site 1 — Bannerughatta** (`QNIT-BLR-S01`) and **Site 4 — Sadahalli** (`QNIT-BLR-S04`), all 10 Oct 2026, Rev A.
Site 2 is deferred until the survey-record question is answered; its data is cached (see the bottom of this file).

Legend:

| Mark | Meaning |
|---|---|
| ✅ | Real data |
| ≈ | Derived or estimated; the method is stated |
| ⛔ | Unavailable; the reason is stated |

| p | Field | Site 3 — Kogilu | Status | Source / method |
|---|---|---|---|---|
| 01 | Project name, locality, date, rev, ID | Kogilu Site Report · Site 3 · Sy 27 & 28 · 10.84 ac | ✅ | KML + supplied cadastral |
| 01 | Prepared for / presented by | Qnit case-study portfolio / GeoAce Studio | ≈ | Default (editable) |
| 02 | Hero image, boundary, V1–V4, north, scale | Esri imagery z19 | ✅ | Esri World Imagery (Wayback 2026-09-24) |
| 02 | Latitude / longitude | 13.098754 N, 77.609015 E | ✅ | KML centroid (UTM 43N) |
| 02 | Study extent | 346 m (bbox diagonal) | ✅ | KML |
| 02 | Area / perimeter / edges | 43,886 m² (10.84 ac, 434 guntas) · 856 m · 4 | ✅ | KML in EPSG:32643 |
| 02 | Design brief / opportunity / constraint | Residential group housing; west stream buffer + AFS height | ≈ | Synthesis of p03–p11 |
| 03 | Boundary image + edge letters | A–B … D–A, stream, plan roads | ✅ | Esri + Overture water + BDA RMP 2031 roads (Qnit planning bucket) |
| 03 | Survey / village / authority | Sy 27/*/1, 28/*/XX · Kogilu 938519 · BDA (GBA North) | ✅ | Supplied cadastral; Builder-Prod `authority_villages.csv` |
| 03 | RCCMS / mutations | No cases · no mutations | ✅ | Supplied RCCMS lookup |
| 03 | Permitted use | Residential (Main), RMP 2015 PD 3.09; 99.7% Residential on draft RMP 2031 layer | ✅ | RMP 2015 map (research, medium confidence); plan raster sampled at z15 |
| 03 | FAR / coverage | 2.25–2.50 / 55% on an 18 m road (2.00 / 60% under 12 m) | ≈ | RMP 2015 ZR Table 20, as read by research; confirm with BDA |
| 03 | Setbacks | ≥ 5 m all round (plot > 4,000 m²); 5–16 m by height (Table 9) | ✅ | RMP 2015 ZR + 2025 amendment |
| 03 | Height limit | 15 m or more needs Yelahanka AFS NOC; AAI NOCAS | ✅ | BBMP NOC list; MoD/AAI rules (research) |
| 03 | Edge conditions (4 edges) | Tree belt / lane / vacant / stream | ≈ | Overture + imagery reading; road widths are not mapped |
| 04 | Contour map, A–B, low/high points | 1 m contours | ✅ | Copernicus GLO-30 DSM (30 m), S3 |
| 04 | Elevation range / slope / interval | 891–900 m · 2.2% to NNW · 1 m | ✅ | Plane fit on the DSM (the DSM includes trees) |
| 04 | Transect | 506 m · relief 9.5 m · VE ≈ 4× | ✅ | Bilinear DSM sampling |
| 05 | Sun path over site, seasonal polar | 21 Mar / Jun / Dec, IST | ✅ | pvlib (NREL SPA) |
| 05 | Incident solar energy | 1,983 kWh/m²·yr (5.43 /day); walls N 574 to SE 1,025 | ✅ / ≈ | NASA POWER CERES SYN1deg 2015–24; wall split modelled |
| 06 | Wind map, rose, season / height | W in Jun–Sep (5.1 m/s), E in Dec–Feb; 10 m | ✅ | NOAA ISD VOBL hourly 2015–24; checked against MERRA-2 |
| 06 | Local comfort | Canopy 9% site / 18% ring; built 25% ring | ✅ | ESA WorldCover 2021 |
| 06 | Seasonal temperature | Apr mean max 36.3 °C; Jan mean min 14.8 °C | ✅ | NASA POWER MERRA-2 daily 2015–24; station check 24.2 vs 24.0 °C |
| 07 | Surface response map | D8 flow, low point, outfall | ✅ | GLO-30 + BBMP primary drains (SAT `rajakaluve_primary.geojson`) |
| 07 | Monthly rainfall + typical range | 937 mm/yr; P10–P90 | ✅ | MERRA-2 PRECTOTCORR 2015–24 (IMD normal 986–1,077 mm) |
| 07 | Event basis | 95 mm / 24 h, 10-year | ≈ | Gumbel fit on 1981–2025 annual maxima (model grid) |
| 07 | Runoff estimate | ≈ 1,500 m³ now → ≈ 3,100 m³ built (10-yr day) | ≈ | Volume = C·P·A with C 0.35 / 0.75 |
| 07 | Groundwater / geology | 5–30 m bgl (district); over 200% extraction; gneiss | ≈ | CGWB district profile + 2024 assessment (research); section is conceptual |
| 07 | Soil texture | — | ⛔ | rest.isric.org returned 503 |
| 08 | View cones / landscape | Jakkur 419 m, Kogilu 1,172 m, Yelahanka 1,318 m lakes | ✅ | Overture water + Esri |
| 08 | Canopy / permeable / habitat edge | 9% / 100% (2021) / stream 5 m | ✅ | WorldCover 2021; Overture |
| 08 | Tree survey | — | ⛔ | No survey; imagery only |
| 09 | Context map + section A–B | 921 buildings within 500 m, 9% footprint | ✅ | Overture buildings 2026-09 |
| 09 | Skyline heights | Assumed storeys (no tagged heights) | ≈ | Footprint-based storey assumption |
| 09 | Walk isochrones 5/10/15 min | 21 / 54 / 106 ha | ✅ | Overture road graph, 4.8 km/h |
| 09 | Transit / health / education / daily needs | Spathagiri Layout stop 545 m; Sri Maruthi Hospital 14 min; Anand Vidhya 5 min; Spar 23 min | ✅ | Overture places / infrastructure |
| 10 | Land-use change | 2017 orchard → 2026 plotted layout | ✅ | Esri Wayback 2017-02-27 vs 2026-09-24 |
| 10 | People & activity | Built-footprint density | ≈ | Overture buildings (proxy) |
| 10 | Census population | — | ⛔ | No published 2011 village figure for Kogilu |
| 10 | Heritage / contamination | None on site; BSWML waste site planned ≈ 2.4 km NE | ≈ | Research (low-confidence distance) |
| 10 | Vernacular photos | 4 Karnataka examples | ✅ | Wikimedia Commons CC BY-SA 4.0 (credited) |
| 11 | Service map | Drains, substation, transformer, tank, bus stops | ✅ | Overture infrastructure (OSM-derived), BBMP SWD |
| 11 | Capacity / connection status | Not confirmed | ⛔ | Needs BWSSB / BESCOM / GBA records |
| 12 | Priorities 01–03, coverage, run ID | Stream buffer · height NOC · layout + services | ✅ | This checklist |

## Site 1 — Bannerughatta (`QNIT-BLR-S01`): what differs from Site 3

| p | Field | Site 1 value | Status | Source / method |
|---|---|---|---|---|
| 02 | Area / perimeter / edges | 34,902 m² (8.62 ac) · 861 m · 13 | ✅ | KML in UTM 43N |
| 03 | Survey points | Sy 22/*/1 inside; Sy 21/*/* label 63 m outside | ✅ | Point-in-polygon test |
| 03 | Records | Sy 22: 4 RCCMS disposed; **MR 2/2026-27 pending** (dispute verdict) | ✅ | Supplied RCCMS / mutation lookup |
| 03 | Permitted use | Agricultural (RMP 2015, PD 30); 97.6% Agriculture on draft RMP 2031 layer | ✅ / ≈ | Plan raster z15; RMP 2015 AG rules via research (PD 30 sheet not seen) |
| 03 | FAR / height | Farm house ≤ 250 m² plinth, G+1, ≤ 1.2 ha; other uses need DC conversion | ≈ | RMP 2015 ZR (research) |
| 03 | Plan road | 45 m (Bannerghatta Rd / SH-87) 104 m ESE | ✅ | BDA RMP 2031 draft roads |
| 04 | Terrain | 931–948 m · 6.8% to NW · 2 m contours; 9% of the site under 5% slope | ✅ | Copernicus GLO-30 |
| 05 | Solar | 1,952 kWh/m²·yr | ✅ | NASA POWER CERES |
| 06 | Wind / temperature | HAL (VOBG) 17.4 km: annual E, Jun–Sep W 4.5 m/s; hottest day 38.0 °C | ✅ | NOAA ISD + MERRA-2 |
| 07 | Drains | No BBMP SWD coverage this far south; lake 134 m W | ⛔ / ✅ | SAT dataset extent; Overture water |
| 07 | Groundwater | Anekal 106% (2025-26), over-exploited | ≈ | IN-GRES via third-party compilation |
| 08 | Park edge | Bannerghatta NP 456 m W (OSM boundary); ESZ line not mapped | ✅ / ⛔ | Overture land use; ESZ not in available data |
| 08 | Quarries / industry | 4 quarries within 1 km (nearest 361 m N); industrial 21 m SSE | ✅ | Overture land use |
| 09 | Access | Bus stop 128 m; SH-87 123 m E; no public road on the boundary | ✅ | Overture |
| 11 | Power | Substation "BG Road" 436 m N; HT line 237 m N | ✅ | Overture infrastructure |

## Site 4 — Sadahalli (`QNIT-BLR-S04`): what differs

| p | Field | Site 4 value | Status | Source / method |
|---|---|---|---|---|
| 02 | Area / perimeter / edges | 309,050 m² (76.37 ac) · 3,232 m · 18 | ✅ | KML in UTM 43N |
| 03 | Survey points | Sy 168, 169, 186, 188, 189 inside; Sy 190 7 m outside | ✅ | Point-in-polygon test |
| 03 | Records | Sy 189: 1 RCCMS case, disposed; others none or not reported | ✅ | Supplied RCCMS |
| 03 | Permitted use / FAR | BIAAPA RMP 2021; zone not published online | ⛔ | biaapa.tpa.gov.in blocked; no plan layer in the Qnit bucket |
| 03 | Airport height | Inner horizontal ≈ 960 m AMSL → 32–56 m above ground; south edge in 09L approach funnel | ≈ | Overture runways (match published thresholds within ~10 m) + ICAO Annex 14 code-4 geometry; AAI CCZM value not retrieved |
| 03 | Boundary overlaps | Villa layout 5,862 m², neighbouring project 2,208 m² inside the KML | ✅ | Overture land use |
| 04 | Terrain | 915–928 m · 1.0% to S; 97% of the site under 5% slope | ✅ | Copernicus GLO-30 |
| 06 | Wind / temperature | VOBL 5.4 km: Jun–Sep W 5.1 m/s, Dec–Feb E 3.1 m/s | ✅ | NOAA ISD + MERRA-2 |
| 07 | Groundwater | Devanahalli 169% (2024); shallow aquifer desaturated | ✅ | CGWB / GWD 2024; NAQUIM 2022 (research) |
| 09 | Access | NH-44 25 m; bus stop 299 m; KIA Halt 2.8 km; Doddajala metro ≈ 1.4 km (2027–28) | ✅ | Overture; research |
| 11 | Power | Substation 683 m; HT line to BIAL 991 m | ✅ | Overture infrastructure |

## Blocked hosts and the fallbacks used

| Need | Blocked host | Fallback used |
|---|---|---|
| Hourly climate | `api.open-meteo.com`, `archive-api.open-meteo.com` | NASA POWER Zarr on S3 (MERRA-2, CERES) + NOAA ISD/GHCN |
| OSM features | `overpass-api.de` | Overture Maps 2026-09-23.0 (S3) |
| Zoning PDFs | `hoskote.tpa.gov.in`, `biaapa.tpa.gov.in`, `strrpa.karnataka.gov.in` | Desk research (needed for Sites 2 and 4) |
| Soil | `rest.isric.org` (503) | None; marked ⛔ |

## Other sites (deferred)

| Site | Cached so far | Key research findings (`research/siteN.json`) |
|---|---|---|
| 2 Tindlu | DEM, WorldCover, climate, Overture, Esri + Wayback 2014 | Survey points (Sy 21–26) lie about 450 m S of the KML; the parcel map shows Sy 27/28/35/36/37 instead; Hoskote MP 2031 Agriculture; next to the STRR |
