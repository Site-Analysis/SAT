# Frontend Changelog

All notable changes to the Qnit web application are documented here.

## [Unreleased]

### Added
- **`RainfallRadar` component** — SVG spider/radar chart rendered in the Rainfall right panel. 12 month spokes clockwise from Jan, concentric dashed scale rings, single data polygon (blue fill + stroke), monsoon months (Jun–Sep) labelled in dark blue. Scales to panel width via `viewBox`. Sits between the metrics grid and the horizontal bar chart.

### Changed
- **Rainfall map overlay** — Removed `RainfallRose` petal polygon (Leaflet layers). Map now shows `RainfallOverlay` cards only (annual badge + legend). Spider chart moved to right panel.
- **Rainfall right panel — monthly chart** — Replaced vertical mini bars with a horizontal bar chart: Jan–Dec rows on Y-axis, mm bars + value labels on X-axis, monsoon months dark blue. Month labels updated from single letters to 3-letter abbreviations.
- **`/project/new` — nav search bar removed** — `SearchBar` component (search input + "Use current location" in TopNav `centerContent`) removed. Replaced with: floating "Use current location" button at map bottom (pre-pin), "Start Analysis" button moved to bottom of `ModuleSelector` card (post-pin). `MapSearch` (Nominatim geocoder, already on map) is the sole address search.
- **Landing page copy** — "Ranjita" → "Ranjitha". Headline "sources that don't trust each other" → "data that was never built for architects". All "Architecture Dialogue" firm citations removed; replaced with "Bengaluru" / "Bengaluru practice". Removed "How adoption works" PLG section.
- **`RainfallOverlay` restored** — Was accidentally removed when removing the petal rose; annual badge + legend cards are back on the map for the rainfall module.

### Removed
- **`RainfallRose.tsx`** — petal rose polygon map overlay (confusing, visually similar to wind rose).
- **`SearchBar` component** — inline nav search bar on `/project/new` (geocoding was not implemented; `MapSearch` handles address lookup).

### Fixed
- **`/project/new` — `ModuleSelector` count** — subtitle now reads "X of 5 selected" correctly (was showing stale count when `SearchBar` held the start flow).

### Docs
- **`CLAUDE.md` (root)** — 5 new gotchas: Supabase `PUBLISHABLE_KEY` vs `ANON_KEY`, `AuthHydrator` render block, dynamic import double-removal, `RainfallRose` vs `RainfallOverlay` naming, `TopNav centerContent` pattern. Supabase key name corrected in services table.
- **`apps/web/CLAUDE.md`** — CSS Modules bracket-notation pattern, monthly rainfall data path.

### Added
- **Rebrand: Qnit by GeoKnit** — full product rename from "SAT / Site Analysis Tool" to "Qnit by GeoKnit". All user-facing strings updated across TopNav, login, dashboard, settings, export report, land records panel, and module detail card. Code identifiers, layer names (e.g. `sat-buildings`), and internal comments unchanged.
- **Public landing page** — `/` now renders a full marketing page (`LandingPage.tsx` + `landing.module.css`) for logged-out visitors. Sections: nav → hero → anchor quote → problem-architect → problem-builder → modules → how-it-works → data-trust → PLG → pricing → final CTA → footer. Logged-in users are redirected to `/dashboard` via client-side `useEffect`.
- **`qnit-logo.svg`** — logo asset added to `public/`; replaces the old "SAT" diamond icon in TopNav and the login page.
- **Fonts: Inter + Space Grotesk + Space Mono** — Geist fonts replaced. `layout.tsx` loads three `next/font/google` fonts as CSS vars (`--font-inter`, `--font-space-grotesk`, `--font-space-mono`). Backward-compat aliases `--font-geist-sans` and `--font-geist-mono` kept in `:root` so existing inline styles resolve without touching every file.

### Changed
- **SiteConfigCard** — new floating card (left panel, below AnalysisConfigCard) showing editable site name (pencil/check inline edit), lat/long coordinates, perimeter, area, vertex angles as chips, and a Dimensions toggle switch wired to `showDimensions` in the draw store.
- **Polygon measurement overlay (live)** — while drawing a polygon, a DOM-mutation overlay (outside React render cycle) renders: segment midpoint length labels, interior angle chips at each placed vertex, and a cursor tooltip showing `↔ distance`, `∠ angle`, `▣ area`, `⌁ perimeter` updating on every mouse move.
- **Static dimension labels (committed boundary)** — after polygon/rect commit, segment length labels appear at each edge midpoint and an area + perimeter pill appears at the polygon centroid (or above the boundary if the bbox is too small to fit it inside). All labels gated on `showDimensions` toggle; `setMode(null)` called in `commit()` so static labels render immediately.
- **`SiteMeasurements` store** — `draw.ts` extended with `siteMeasurements` / `setSiteMeasurements` (area m², perimeter m, vertex angles[]) and `showDimensions` / `setShowDimensions` (default `true`).
- **Profile dropdown** — avatar button in TopNav now opens a dropdown showing user name/email, a Settings link, and Sign out. Wired across dashboard, new-analysis, and analysis pages with supabase signOut + store clear.

### Changed
- **Accent color → forest green** — `--color-brand-primary` changed from `#657166` (sage) to `#306223` across all 14 frontend files (57 instances). Secondary dark tint `#4D5850` → `#24491a`. Affects buttons, sliders, borders, icon tints, draw stroke, measurement label borders, angle chips, and the dimensions toggle.
- **Flood risk zones — polygon-shape** — `FloodZoneRings` now scales the drawn site boundary polygon outward for each intensity zone instead of drawing concentric circles. Each zone follows the exact site shape (cosLat-corrected). Falls back to concentric circles when no polygon is drawn.
- **Flood risk zones — single dominant factor** — instead of 4 stacked zones, renders ONE zone colored by whichever flood driver has the highest normalised value (`overallRisk`, `lowLyingRisk`, `waterOccurrence`, `riverProximity`). Zone buffer distance and fill color match that factor's legend entry.
- **"Flood" → "Risks"** — module label in new-project analysis list changed from "Flood" to "Risks" (subtext unchanged: "Risk, terrain, hydrology").
- **AnalysisConfigCard positioning** — own absolute position styles removed; parent `project/new/page.tsx` now owns the left-panel flex column (`top: 70, left: 16, width: 248, zIndex: 500, gap: 8`) containing AnalysisConfigCard + SiteConfigCard stacked.
- **TopNav — Settings tab removed** — "Settings" text pill removed from left nav on both dashboard and settings contexts; gear icon remains and is now always visible (no longer hidden on the settings page).
- **MapCompass redesign** — north indicator replaced with a centered diamond needle (orange tip = north, neutral tail = south) with a pivot dot. Fixes "N" letter being obscured by the old floating wedge.
- **Map toggles repositioned** — Amenities and Climate toggles moved below the compass (top: 84→130 and top: 132→178) so they no longer overlap with the compass widget.
- **CORS fix** — `docker-compose.yml` temperature (8000) and rainfall (8004) services: `CORS_ORIGINS` corrected from `http://localhost:5173` → `http://localhost:3000`.
- **React Strict Mode disabled** — `next.config.ts` sets `reactStrictMode: false` to prevent Leaflet double-mount error ("Map container is being reused") in development.
- **Overpass mirror** — switched from `overpass-api.de` (rate-limited) to `overpass.openstreetmap.fr` for geo/planning/flood and `maps.mail.ru` for infrastructure (which fires 5 concurrent queries that openstreetmap.fr rate-limits with 403).

### Fixed
- **Dimension labels — zoom stability** — label containers appended to `map.getContainer()` (outside `.leaflet-map-pane`) were frozen at stale pixel positions during Leaflet's CSS scale animation. Fixed: `zoomstart` hides both label containers, `zoomend` redraws at final positions. `move` event retained for smooth pan tracking.
- **Dimension labels — zoom-out congestion** — segment labels now skip rendering when pixel segment length < 70 px, preventing label pile-up on zoomed-out views. Area/perimeter pill always renders.
- **Buffer circle — disappears after polygon draw** — `!pinFromDraw` condition was hiding the site circle once a polygon was drawn. Removed condition; circle now renders whenever `pinDropped` is true regardless of draw state.
- **Buffer circle — moves on stray clicks** — `handleMapClick` in `project/new/page.tsx` was updating center on every map click. Added `if (pinDropped) return` guard so center locks after first pin.
- **DrawTools delete button — site circle not cleared** — `hasDrawing` check excluded the site radius circle so the trash button stayed disabled. Added `hasSiteCircle` prop (counts toward `hasDrawing`) and `onClear` callback; `project/[id]/page.tsx` manages `showSiteCircle` state and resets it on clear.
- **3D view blank canvas** — `Scene3D.tsx` `onAdd` called `renderer.setPixelRatio(window.devicePixelRatio)` on the shared MapLibre canvas. MapLibre had already set `canvas.width = cssWidth × dpr`; Three.js re-read that as the CSS width and multiplied by dpr again, doubling the drawing buffer (3680×2400 instead of 1840×1200). MapLibre's WebGL viewport origin (bottom-left) meant tiles rendered only into the bottom-left quarter of the oversized buffer. Fix: removed the `setPixelRatio` call. Three.js now uses the existing buffer via the explicit `setViewport(gl.drawingBufferWidth, gl.drawingBufferHeight)` call already present in `render()`.
- **DrawTools delete button** — `L.DomEvent.disableClickPropagation` was killing React's delegated `onClick` handlers on all toolbar buttons (pan, rect, poly, trash). Now stops only `mousedown`/`dblclick`/scroll to prevent map drag/zoom without blocking click events.
- **Zoning infinite loading** — `svcFetch` had no timeout; Overpass-backed endpoints (zone, infrastructure) could hang indefinitely. Added 30 s `AbortController` timeout across all services. `getZoningAnalysis` now catches zone fetch failure and falls back to `zone_class: Unknown` so planning data still renders.
- **Amenities graceful fallback** — `getAmenitiesAnalysis` now returns an empty `ModuleResult` (amenityPoints=[]) on Overpass failure instead of throwing; toggle still renders with a rate-limit message rather than an error badge.
- **land-records healthcheck** — `services/land-records/Dockerfile` missing `apt-get install curl`; container was marked unhealthy despite serving correctly. Added curl install step.
- **Infrastructure telecom query** — unquoted `[tower:type=communication]` key rejected by mail.ru Overpass; fixed to `["tower:type"=communication]`.

### Changed
- **TopNav — Settings tab removed** — "Settings" text pill removed from left nav on both dashboard and settings contexts; gear icon remains and is now always visible (no longer hidden on the settings page).
- **MapCompass redesign** — north indicator replaced with a centered diamond needle (orange tip = north, neutral tail = south) with a pivot dot. Fixes "N" letter being obscured by the old floating wedge.
- **Map toggles repositioned** — Amenities and Climate toggles moved below the compass (top: 84→130 and top: 132→178) so they no longer overlap with the compass widget.
- **CORS fix** — `docker-compose.yml` temperature (8000) and rainfall (8004) services: `CORS_ORIGINS` corrected from `http://localhost:5173` → `http://localhost:3000`.
- **React Strict Mode disabled** — `next.config.ts` sets `reactStrictMode: false` to prevent Leaflet double-mount error ("Map container is being reused") in development.
- **Overpass mirror** — switched from `overpass-api.de` (rate-limited) to `overpass.openstreetmap.fr` for geo/planning/flood and `maps.mail.ru` for infrastructure (which fires 5 concurrent queries that openstreetmap.fr rate-limits with 403).

### Fixed
- **3D view blank canvas** — `Scene3D.tsx` `onAdd` called `renderer.setPixelRatio(window.devicePixelRatio)` on the shared MapLibre canvas. MapLibre had already set `canvas.width = cssWidth × dpr`; Three.js re-read that as the CSS width and multiplied by dpr again, doubling the drawing buffer (3680×2400 instead of 1840×1200). MapLibre's WebGL viewport origin (bottom-left) meant tiles rendered only into the bottom-left quarter of the oversized buffer. Fix: removed the `setPixelRatio` call. Three.js now uses the existing buffer via the explicit `setViewport(gl.drawingBufferWidth, gl.drawingBufferHeight)` call already present in `render()`.
- **DrawTools delete button** — `L.DomEvent.disableClickPropagation` was killing React's delegated `onClick` handlers on all toolbar buttons (pan, rect, poly, trash). Now stops only `mousedown`/`dblclick`/scroll to prevent map drag/zoom without blocking click events.
- **Zoning infinite loading** — `svcFetch` had no timeout; Overpass-backed endpoints (zone, infrastructure) could hang indefinitely. Added 30 s `AbortController` timeout across all services. `getZoningAnalysis` now catches zone fetch failure and falls back to `zone_class: Unknown` so planning data still renders.
- **Amenities graceful fallback** — `getAmenitiesAnalysis` now returns an empty `ModuleResult` (amenityPoints=[]) on Overpass failure instead of throwing; toggle still renders with a rate-limit message rather than an error badge.
- **land-records healthcheck** — `services/land-records/Dockerfile` missing `apt-get install curl`; container was marked unhealthy despite serving correctly. Added curl install step.
- **Infrastructure telecom query** — unquoted `[tower:type=communication]` key rejected by mail.ru Overpass; fixed to `["tower:type"=communication]`.
