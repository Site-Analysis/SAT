# Test Matrix — SAT Backend Services

Initial run: 2026-06-18 (Overpass rate-limited).
Re-run with Overpass restored: 2026-06-19. All skips resolved.

62 tests collected across 10 services.

| Service | Port | Tests | Pass | Fail | Skip | Notes |
|---|---|---|---|---|---|---|
| temperature | 8000 | 7 | 7 | 0 | 0 | Full pass incl. thermal-grid |
| sunpath | 8001 | 9 | 9 | 0 | 0 | Annual, summer, winter, SVG, orientation |
| flood | 8002 | 7 | 7 | 0 | 0 | Score range, risk category, dual-site |
| wind | 8003 | 5 | 5 | 0 | 0 | Schema, speed domain, dual-site |
| rainfall | 8004 | 6 | 6 | 0 | 0 | Annual total, monthly breakdown |
| geo | 8005 | 7 | 7 | 0 | 0 | All Overpass tests pass with mirror switch |
| planning | 8006 | 6 | 6 | 0 | 0 | FAR domain, airport restriction |
| infrastructure | 8007 | 5 | 5 | 0 | 0 | All pass after mirror fix + query fix |
| future-infra | 8008 | 4 | 4 | 0 | 0 | Pipeline schema, static data |
| land-records | 8009 | 6 | 6 | 0 | 0 | Bhoomi lookup, deep links, score range |
| **Total** | | **62** | **62** | **0** | **0** | |

**62/62 pass. Zero failures. Zero skips.**

## Overpass mirror configuration (resolved 2026-06-19)

Initial run used `overpass-api.de` (set in `.env`) — returned 406/rate-limited.

Switched `.env` → `OVERPASS_URL=https://overpass.openstreetmap.fr/api/interpreter` (geo, planning, flood).

Infrastructure hardcoded to `https://maps.mail.ru/osm/tools/overpass/api/interpreter` in `docker-compose.yml` — `openstreetmap.fr` returns 403 for its 5-query concurrent burst; mail.ru handles it fine.

Also fixed: `[tower:type=communication]` → `["tower:type"=communication]` in infra telecom query (unquoted colon-key rejected by mail.ru).

## Test corrections from re-run

`test_urban_higher_than_rural` → replaced with `test_second_site_schema`. The original assertion (Bellandur score ≥ Devanahalli score) was wrong — Devanahalli (near KIAL airport) has NH-44 directly adjacent, giving it a higher road-access score (34.2) than Bellandur (15.5). This is correct service behaviour, not a bug.

## Test coverage gaps

| Service | Missing coverage |
|---|---|
| temperature | Thermal-grid polygon validation (complex GeoJSON bodies) |
| flood | Coastal / riverine site comparison |
| land-records | Invalid district/taluk (404 vs 422 boundary) |
| all | Auth / feature-flag gating (FLAGS env var enforcement) |
