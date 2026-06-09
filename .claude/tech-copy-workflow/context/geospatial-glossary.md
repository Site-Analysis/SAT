# SAT Geospatial Glossary — Plain English Translations

Purpose: every technical data source and term SAT references must be translatable to architect-legible copy without losing accuracy. This glossary is the authoritative lookup. Never invent translations outside this file.

Format per entry:
- **Technical name** — what engineers call it
- **What it is** — plain English, one sentence
- **What it means for architects** — the output value, not the algorithm
- **Copy-safe phrase** — drop-in replacement for technical writing
- **Do not say** — common mistranslations

---

## Data Sources

### MERIT DEM (Multi-Error-Removed Improved-Terrain Digital Elevation Model)
**What it is:** A global digital elevation model derived from satellite radar data, with vegetation and building heights mathematically removed to show true bare-earth elevation.
**What it means for architects:** The flood analysis uses ground-level elevation, not rooftop or treetop elevation — so the risk score reflects actual terrain, not obstruction.
**Copy-safe phrase:** "bare-earth elevation data" / "ground-level terrain elevation"
**Accuracy:** ~90m horizontal resolution; vertically ±1–2m typical for India
**Do not say:** "LiDAR data" (MERIT DEM is radar-derived, not LiDAR); "high-resolution elevation" without context (90m is medium resolution)

---

### JRC GSW (JRC Global Surface Water)
**What it is:** A dataset from the European Commission's Joint Research Centre that maps every body of surface water visible from satellite across 38 years (1984–2021).
**What it means for architects:** SAT knows where water has historically appeared near a site — rivers, seasonal lakes, flood-prone land — and uses this to weight flood risk.
**Copy-safe phrase:** "38 years of historical flood and water body data" / "historical surface water mapping"
**Do not say:** "real-time flood data" (this is historical, not live); "flood prediction" (it informs risk scoring, not prediction)

---

### NREL SPA (National Renewable Energy Laboratory Solar Position Algorithm)
**What it is:** A peer-reviewed algorithm from the US National Renewable Energy Laboratory that calculates sun position (altitude and azimuth) for any location and time to ±0.0003° accuracy.
**What it means for architects:** SAT's solar analysis uses the same precision algorithm used in utility-scale solar farm design — sun position results are publication-grade, not approximations.
**Copy-safe phrase:** "NREL-grade solar position accuracy" / "sun position accurate to within 1/100th of a degree"
**Do not say:** "NASA solar data" (NREL ≠ NASA); "±0.0003° solar accuracy" in casual copy (fine for technical docs, not onboarding)

---

### pvlib
**What it is:** An open-source Python library for simulating photovoltaic (solar panel) energy systems, used by researchers and solar engineers globally.
**What it means for architects:** SAT uses pvlib to model how much solar radiation reaches a surface at different orientations, enabling passive solar design recommendations.
**Copy-safe phrase:** "solar radiation modeling" / "incident solar energy per surface"
**Do not say:** "solar panel optimization" (SAT is for passive design, not PV system sizing unless that feature is confirmed live)

---

### Open-Meteo
**What it is:** An open-source weather API that provides historical and forecast climate data from multiple global weather models (ERA5, GFS, ECMWF).
**What it means for architects:** Temperature, wind, and rainfall data for any site in India without requiring proprietary API access. Used as the primary climate data source and IMD fallback.
**Copy-safe phrase:** "global climate archive" / "multi-model weather data"
**Do not say:** "real-time weather" without specifying which endpoint is live vs. archive; "satellite weather data" (Open-Meteo is model-based, not direct satellite)

---

### IMD (India Meteorological Department)
**What it is:** The official Indian government body for meteorological observations and climate data. Its gridded rainfall dataset covers India at 0.25° resolution (~28km grid).
**What it means for architects:** Rainfall analysis uses government-source data, not international proxies — important for regulatory credibility and India-specific accuracy.
**Copy-safe phrase:** "India Meteorological Department rainfall data" / "IMD gridded rainfall"
**Coverage limitation:** India only; 0.25° grid (~28km); remote/island areas may have gaps
**Do not say:** "real-time rainfall" unless confirmed; "IMD weather" (SAT uses IMD rainfall specifically, not all IMD products)

---

### GEE (Google Earth Engine)
**What it is:** Google's cloud computing platform for processing satellite and geospatial data at planetary scale.
**What it means for architects:** Some SAT analyses (flood, vegetation) process satellite imagery server-side using GEE — no large downloads, fast results.
**Copy-safe phrase:** "satellite image analysis" / "cloud-processed satellite data"
**Do not say:** "Google Maps data" (GEE ≠ Google Maps); "Google Earth" (GEE is an API platform, not the consumer product)

---

### OSM / OpenStreetMap
**What it is:** A crowd-sourced global map database containing roads, buildings, land use, water features, and more, maintained by a global volunteer community.
**What it means for architects:** SAT pulls nearby building footprints, roads, and landmarks from OpenStreetMap to contextualize analysis results — no proprietary mapping license required.
**Copy-safe phrase:** "open map data" / "building and infrastructure data from OpenStreetMap"
**Accuracy note:** Quality varies by city. Tier-1 Indian cities (Mumbai, Delhi, Bengaluru, Chennai) have good coverage; smaller towns may be sparse.
**Do not say:** "real-time building data" (OSM is contributor-updated, not live sensor data)

---

## Coordinate System Terms

### WGS84 (World Geodetic System 1984)
**What it is:** The standard coordinate reference system used by GPS and most web maps. Coordinates are in decimal degrees of latitude and longitude.
**Copy-safe phrase:** "standard GPS coordinates" / "latitude/longitude coordinates"
**Do not say:** "GPS projection" (WGS84 is a datum, not a projection)

### EPSG:4326
**What it is:** The EPSG code that identifies WGS84 geographic coordinate reference system. Used in GeoJSON, APIs, and GIS software to specify the coordinate system.
**Copy-safe phrase:** "GeoJSON standard coordinates" / "standard lat/lon format"
**Do not say:** Just "4326" without context in user-facing copy; use "standard coordinates" instead.

### GeoJSON
**What it is:** An open standard for encoding geographic features as JSON — points, polygons, lines, and their properties.
**Copy-safe phrase:** "standard geographic file format" / "GeoJSON export"
**Critical rule:** GeoJSON coordinates are always [**Longitude, Latitude**] — never [Lat, Lon]. See style-guide.md Coordinate Law.

---

## Analysis Metrics

### NDVI (Normalized Difference Vegetation Index)
**What it is:** A ratio derived from satellite infrared imagery that measures plant health and density. Range: -1 to +1. Above 0.5 = dense vegetation. Below 0.1 = bare soil or built surface.
**What it means for architects:** SAT can show how much greenery surrounds a site and how that affects microclimate (evapotranspiration cooling, urban heat island effect).
**Copy-safe phrase:** "vegetation health score" / "green cover index"
**Do not say:** "greenery percentage" (NDVI is a ratio, not percentage coverage)

### Flood Risk Score (0–100)
**What it is:** SAT's composite flood risk metric, calculated from 4 components: terrain elevation, proximity to historical surface water, soil drainage capacity, and seasonal rainfall intensity.
**What it means for architects:** A single number that summarizes flood vulnerability — usable in design briefs, planning applications, and regulatory submissions.
**Copy-safe phrase:** "0–100 flood risk score" / "4-component flood risk rating"
**Do not say:** "100% accurate flood prediction" (risk score, not prediction); claim specific component weights without confirming against FVD

### Shadow Coverage %
**What it is:** The percentage of a surface area in shadow at a given hour and day, calculated from sun position and surrounding building geometry.
**What it means for architects:** Quantified shadow data supports orientation decisions, outdoor space programming, and glazing ratio analysis.
**Copy-safe phrase:** "shadow coverage at [time/date]" / "% shaded area"
**Do not say:** "real-time shadow" (calculated from geometric model, not live sensor)

---

## Common Mistranslations to Avoid

| Technical phrase | Bad translation | Correct translation |
|---|---|---|
| "MERIT DEM elevation data" | "Google terrain data" | "bare-earth elevation from satellite radar" |
| "NREL SPA solar position" | "NASA sun tracking" | "research-grade sun position calculation" |
| "JRC Global Surface Water" | "flood prediction data" | "38-year historical flood mapping" |
| "Open-Meteo climate archive" | "live weather data" | "historical climate data (ERA5 / ECMWF)" |
| "GEE-processed imagery" | "Google Maps analysis" | "cloud-processed satellite imagery" |
| "EPSG:4326 coordinates" | "GPS format" | "standard lat/lon coordinates (WGS84)" |
| "pvlib solar simulation" | "solar panel calculation" | "solar radiation modeling" |
| "OSM building footprints" | "real-time building data" | "building and infrastructure data (OpenStreetMap)" |
