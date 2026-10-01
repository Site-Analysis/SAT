# builder-arch-integ — status log (2026-10-01)

Branch `builder-arch-integ`, cut from `origin/main` (3fc4686). Purpose: bring the Builder-Prod cadastral feature into SAT, add contour
analysis, and produce a parcel site report for survey 54/2 & 54/4, Tubarahalli. This file records what is **not done**, what **did not work**,
and **why**. No secrets are recorded here.

## Commits on the branch
- `34afb84` docs: parcel report design
- `a498bc4` feat(cadastral): service, map layer, Analyse-this-parcel button, Parcel & Title report page, dev auth bypass, OSM basemap
- `d4c00d8` Merge `feat/contour-analysis` (SAT-19)
- **Uncommitted:** `services/contour/{Dockerfile, requirements.txt, app/services/dem_service.py}` (build/runtime fixes, see Issues 3–5)

## Missing / not done
| # | Item | Why it is missing |
|---|------|-------------------|
| M1 | Contour, slope, buildability, transect data | GEE rejects the service account (Issue 1). The contour code is merged and builds, but cannot fetch a DEM. |
| M2 | Real flood-risk, hydrology, river-distance figures | Same GEE failure + Overpass failure; the flood service silently substitutes defaults (Issue 6). |
| M3 | Infrastructure connectivity (roads, transit, power) | Overpass returned 502/upstream-unavailable on every attempt (Issue 7). |
| M4 | Cadastral explorer on the **New Analysis** page (`/project/new`) | Never built. Planned in `~/.claude/plans/where-is-the-cadastral-dazzling-puffin.md` steps 3–6 (onParcelSelect prop on `CadastralLayer`, mount in `new/page.tsx`, add `contour` to `ANALYSIS_MODULES`, fix hard-coded "of 5 selected", export-page Polygon centroid). The report was produced offline instead. |
| M5 | Export page (`app/project/[id]/export/page.tsx`) falls back to Bangalore for Polygon boundaries | Not fixed (only reads Point boundaries). Parcel projects exported from the UI would use the wrong location. |
| M6 | Browser verification of the "Analyse this parcel" button, project creation and in-app PDF export | Never run in a browser (user asked not to use Chrome automation; login/auth path not exercised). Only `tsc`, `next build`, service curls and an offline-generated PDF were verified. |
| M7 | Land-use / land-type from the supplied database | `builder_data` has no such field: all 29,927 parquets hold only geometry, village_code, village_name, survey_no (2,324 hold only `status`). Land use in the report was supplied by the user (BDA RMP 2031 / 2015) and not independently verified. |
| M8 | 54/2 vs 54/4 plot assignment and sub-division geometry | Cadastral data holds parent surveys only (54, 40). KML overlay puts the west plot ~90% in survey 54 and the east plot in survey 40. Unresolved; flagged in the report. |
| M9 | Contour smoke test (`tests/contour_smoke.py`), `tests/cadastral_smoke.py` after auth removal, and one-file-per-process CI run | cadastral: run once (11 passed, 2 skipped) before auth was stripped, not rerun. contour: never run. |
| M10 | ESLint run | `apps/web` has no `eslint.config.*`; `npx eslint` tried to install v10 and failed. |
| M11 | FVD for cadastral (`docs/feature-validation/SAT-XX_*.md`) and `contracts/cadastral.yaml` review | Repo rule "FVD before code" not followed; the contract was copied from Builder-Prod and not checked with `contract-validator`. |
| M12 | PR | No PR opened; nothing pushed. Contour merge brought 103 files (incl. `tests/testUI.html`) — per "one feature per PR" it should be split. |
| M13 | `survey_index` rebuild time | Volumes `sat_survey_index_vol` (165 MB) and `sat_overpass-db` (532 MB) were **kept** on cleanup (other projects' volumes untouched). Delete them with `docker volume rm` if more space is needed; the survey index then rebuilds (~15 min) on next cadastral start. |

## Issues found (what did not work, and why)
1. **Contour — Google Earth Engine 403.** `Caller does not have required permission to use project <GEE_PROJECT_ID>`. The key in `gee-sa.json` authenticates
   (the account named in `GEE_SERVICE_ACCOUNT_EMAIL`) but lacks `roles/serviceusage.serviceUsageConsumer` on that project. Needs an owner to grant it, or a new key.
   Alternative key `services/service-account.json` (a second service account, different Google Cloud project) fails with `invalid_grant: account not found` (deleted account). Other
   `SAT-Fallback/services/*/gee-sa.json` copies are 0-byte files; `SAT-Fallback/gee-sa.json` is the same dead-permission key.
2. **Docker / host disk full.** `/System/Volumes/Data` hit 100% (175 MB free). Docker went `read-only file system` (build metadata DB, container logs), CLI calls hung, builds failed.
   Not fixable by moving Docker to LocalDrive: LocalDrive (`disk3s7`) is in the same APFS container (`disk3`) which had 0 B free.
3. **Contour image build — `rasterio==1.4.3` has no aarch64 wheel** on python:3.11; pip tried to compile and failed (`gdal-config` missing). Fixed by pinning `rasterio==1.4.4` (uncommitted).
4. **Contour runtime — `libexpat.so.1` missing** in `python:3.11-slim`; rasterio import failed. Fixed by adding `libexpat1` to the Dockerfile (uncommitted).
5. **Contour startup — two code bugs** in `dem_service.py` (uncommitted fixes): `os.environ["PROJ_DATA"]` KeyError on non-Windows (module was written for a Windows path; same fix as `stash@{1}`),
   and `Path(__file__).parents[4]` IndexError inside the container (`/app/app/services/…` has too few parents).
6. **Silent fallbacks that mislabel data (violates the repo rule "stubs must be honest").**
   - `rainfall` service: `Failed to initialize GEE: './gee-sa.json' not found` → `_generate_synthetic_series`, yet the response `data_source` still says "CHIRPS / Open-Meteo (CHIRPS Daily via Google Earth Engine)". Cause: `GEE_SERVICE_ACCOUNT_KEY_PATH=./gee-sa.json` is not mounted in that container.
   - `temperature` service: IMD `.grd` files for 2025 absent in `/app/data`; Open-Meteo call returned 400; fell back to an "estimated thermal profile" (score 27).
   - `flood` service: Overpass lookup failed → hard-coded 5000 m river distance; GEE terrain/MERIT metrics default to constants (e.g. flow accumulation 0.15, elevation min/mean/max 865/870/875).
   The site report therefore withholds flood/hydrology and replaces rainfall/temperature with directly fetched ERA5 data.
7. **Overpass (public mirror) unreliable.** `infrastructure` raised 502 (`OSM upstream unavailable`) on every attempt, including repeats; flood/water-bodies calls timed out. (Matches open issues #90/#91 in the repo.)
8. **`gust_risk` is always "High"** (issue #90): thresholds are applied to a 5-year maximum, not a percentile. The gust-risk chip was removed from the report.
9. **Frontend basemap broken**: `MapContainer.tsx` used CARTO Voyager raster tiles, now returning "API KEY REQUIRED". Switched to OSM tiles. `NEXT_PUBLIC_MAPTILER_KEY` (in both `SAT` and `SAT-SoA` `.env.local`) returns 403 on MapTiler — invalid/revoked; 3D view (`Scene3D.tsx`) and satellite toggle will fail until replaced.
10. **Frontend login path**: all pages gate on a Supabase session (`router.replace("/login")`). Added dev-only `NEXT_PUBLIC_DEV_BYPASS_AUTH=1` in `AuthHydrator.tsx` (default off). It is a build-time flag; must never be set in deployed envs.
11. **Builder-Prod could not be `git merge`d**: no common ancestor with `main` (trimmed rewrite, 410 files differ, ~47k fewer lines). Only additive files were copied; auth (Keycloak/next-auth), Supabase `builder_projects` routes and deployment scripts were dropped by decision.
12. **Cadastral flag parsing bug (fixed):** Builder-Prod split `FLAGS` on whitespace; SAT uses commas, so with multiple flags every cadastral endpoint returned 403.
13. **Survey search** needs `survey_index.db`, built in the background (~15 min) on first start; until done only dropdown + map click work.
14. **Cadastral names**: `echawadi_village_list.json` was missing from the original data folder; supplied later in `~/Downloads/builder_data`.
15. **Process mistakes (for the record):** an `xargs -d` failure on macOS detached HEAD onto the Builder-Prod ref (recovered, `CLAUDE.md` verified identical to main); one command printed a `NEXT_PUBLIC_` MapTiler key to the transcript (public client-side key, already invalid); a `site.py` helper shadowed Python's `site` module (renamed).
16. **Env/config touched:** `.env` — added `CADASTRAL_DATA_ROOT`, `feature.cadastral.land-records` and `feature.contour.analysis` to `FLAGS`. `apps/web/.env.local` — `NEXT_PUBLIC_DEV_BYPASS_AUTH=1`, `NEXT_PUBLIC_ENABLE_CADASTRAL_EXPLORER=1`. Both gitignored.
17. **Repo hygiene:** `docker-compose.yml` still has the obsolete `version:` key (warning only). Untracked clutter in the working tree: `.sat-frontend.log`, `deployment/`, `deployment-plan.md`, `scripts/sat-run.sh`, `services/cadastral-data/`, `ux-research/`.

## Deliverables outside the repo
- `~/Downloads/Tubarahalli_Survey_54-2_54-4_Site_Report.pdf` (client-facing, 11 pages)
- `~/Downloads/site_report_sources/` — `build_report.py`, `run.js`, `site.json` (rebuilding needs the services, a Python venv with matplotlib/Pillow/shapely, and compiled `analysis.js`; all were deleted in cleanup). Cleanup removed: root + `apps/web` `node_modules`, `apps/web/.next`, every `services/*/.venv`, all `sat-*` Docker images/containers/network, the overpass, `python:3.11-slim` and `alpine` images, and the Docker build cache. Kept: other projects' Docker images/volumes (caddy, jaeger, otel, postgis, keycloak), `builder_data`, the PDF and `site_report_sources/`.

## To resume
1. Get GEE permission (Issue 1), then `docker compose up -d --build contour` and test `/contour/analyze` with a ≥0.5 ha polygon.
2. Re-install deps: `npm install` (root), per-service venvs (`python3.12`), `docker compose build`.
3. Finish M4/M5/M6, run smoke tests one file per process, commit contour fixes, split PRs.
