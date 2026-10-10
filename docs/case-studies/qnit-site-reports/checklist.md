# Qnit Site Report — section checklist

Template: *Qnit Report Template (13 pages)*. Report built: **Site 3 — Kogilu** (`QNIT-BLR-S03`, 10 Oct 2026, Rev A).
Sites 1, 2 and 4 were deferred at the user's request. Their data is partly cached (see the bottom of this file).

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
| 1 Bannerughatta | DEM, WorldCover, climate, Overture, Esri + Wayback 2017 | RMP 2015 Agricultural zone; Bannerghatta NP ESZ under Supreme Court review (CEC Jan 2026); mutation MR 2/2026-27 pending; Anekal over-exploited |
| 2 Tindlu | DEM, WorldCover, climate, Overture, Esri + Wayback 2014 | Survey points (Sy 21–26) lie about 450 m S of the KML; the parcel map shows Sy 27/28/35/36/37 instead; Hoskote MP 2031 Agriculture; next to the STRR |
| 4 Sadahalli | DEM, WorldCover, climate, Overture, Esri + Wayback 2014 | BIAAPA MP 2021 (no 2031 plan); about 4 km W of the KIA 09L threshold, so an AAI height NOC is needed; Devanahalli extraction 169% |
