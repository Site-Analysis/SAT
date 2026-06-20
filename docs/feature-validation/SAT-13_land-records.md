# FVD — SAT-13 Land Records Service

**Jira Ticket:** SAT-13
**Status:** Migrating (Phase 1 code integration)
**Type:** Story
**Source repo:** TanmayCJ/SAT-Fallback (`ux/phase-1-research`)

---

## Feature Overview

**User Story:** As a buyer doing due diligence, I want a single place that points me to
the right Karnataka land-records portals (RTC, encumbrance, court cases, bank charges)
pre-filled for my survey number, so I can verify ownership and litigation directly.

**Business Value:** Consolidates fragmented government portals into one deep-link set
with an honest completeness score. **Deliberately does not scrape** — the portals
require CAPTCHA/session auth — so it never fabricates ownership or litigation data.

---

## Commit Traceability

| Commit | Repo | Description |
|---|---|---|
| `141ef0c` | SAT-Fallback | checkpoint(web): … + land-records buildout |
| `7480002` | SAT-Fallback | feat(web): profile dropdown, nav cleanup, … infra fixes |

Ported into `Site-Analysis/SAT` as branch `feat/land-records-service` (Phase 1).

---

## Code Traceability Matrix

| # | Acceptance Criterion | File | Function / Class |
|---|---|---|---|
| 1 | `POST /land-records/lookup` returns typed `LandRecordsResult` | `app/routers/land_records.py` | `lookup_land_records()` |
| 2 | Gated by `feature.land.records` → 403 when off | `app/routers/land_records.py` | `_require_flag()` |
| 3 | Bhoomi record returned as empty placeholder (no scraping) | `app/services/bhoomi_service.py` | `fetch_bhoomi_record()` |
| 4 | Court cases returned empty (eCourts has no public API) | `app/services/ecourts_service.py` | `search_court_cases()` |
| 5 | Deep links to Bhoomi / KAVERI / eCourts / CERSAI / MCA21 | `app/services/deep_links_service.py` | `get_deep_links()` |
| 6 | User input URL-encoded into deep links (no injection) | `app/services/deep_links_service.py` | `get_deep_links()` (`quote()`) |
| 7 | Completeness score + `none` severity + verify-directly notes | `app/services/land_records_service.py` | `analyze()` |
| 8 | Honest `data_source` (portal names + "direct access required") | `app/services/land_records_service.py` | `analyze()` |
| 9 | Typed request/response models | `app/models/land_records.py` | `LandRecordsRequest`, `LandRecordsResult`, `BhoomiRecord`, `CourtCase`, `DeepLink` |

---

## Security note

Portal-only: no outbound scraping, no credentials. Deep-link URLs are hardcoded
government domains; the only user-supplied value (`survey_number`) is `quote()`-encoded
before interpolation into the eCourts URL.

## Contract

`contracts/land-records.yaml` (v1.0.0) — CHANGELOG 2.4.0.

## Flag

`feature.land.records` — `FeatureFlag.LAND_RECORDS`, default off.

## Tests

`tests/land_records_smoke.py` — health, flag-off 403, flag-on 200 (real service; deep
links are deterministic, no network).
