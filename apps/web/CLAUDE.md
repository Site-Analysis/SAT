@AGENTS.md

## Frontend Patterns

### CSS Modules — hyphenated class names
Use `const $ = styles as Record<string, string>` then `$["class-name"]` for bracket access. Dot notation fails for hyphenated names. Pattern in `components/landing/LandingPage.tsx`.

### Monthly rainfall data path
`result.charts?.find(c => c.title === "Monthly rainfall")?.points` → 12 `{label: "Jan"…"Dec", value: mm}` objects. Reuse the `monthly()` helper at `components/layout/RainfallPanel.tsx:26` instead of re-extracting.

### react-leaflet GeoJSON does not update after mount
`<GeoJSON data={...}>` ignores subsequent `data` changes. Remount with a store nonce in `key` (see `resultNonce` in `lib/stores/contour.ts` and `ContourLinesLayer`). Do not pass a static `key="slope"`.

### Imperative map markers for pointer-rate updates
Do not drive a Leaflet marker from React state at `pointermove` rate. Subscribe with `useContourStore.subscribe(selector, cb)` and call `marker.setLatLng()` (and mutate SVG `transform` through a ref). Pattern: `TransectCursorMarker` + `TransectProfileChart`. The textual readout is the only React state, coalesced with `requestAnimationFrame`.
