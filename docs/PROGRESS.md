# Qnit — Progress Timeline

Two timelines: the **deployment phase log** (porting Fallback → SAT and shipping it) and the
**feature-build timeline** (what shipped in `apps/web` / the services, folded from the frontend
`apps/web/CHANGELOG.md` and the contract changelog). See `deployment-plan.md` for the phase
roadmap (local planning doc) and `docs/architecture/` for the resulting service/frontend maps.

---

## Deployment phase log

### 2026-06-20 — Phase 0 complete (Prep & Safety)
- **Security:** revoked leaked GitHub PAT (was in plaintext in SAT `.git/config`); switched
  remote to SSH `git@github.com:Site-Analysis/SAT.git`; `git fetch` verified; no token in tracked
  files.
- **Browser auth verified (all 4):** GoDaddy (qnit.in + qnit.site owned), Vercel (empty), AWS
  (account `chiragds`, region Sydney ap-southeast-2), Supabase (project "SAT", Tokyo).
- **Delta:** raw tree diff `sat/main..HEAD` = 300 files / +42626 — but misleading (Fallback &
  main diverged post-fork). **Port set = 20 Fallback-unique commits**, grouped per feature; NOT a
  tree-merge (would regress main-ahead rainfall).
- **Manifest** (`deployment/inventory.md`, local) corrected & locked: backend 4 new services
  (planning/infrastructure/future-infra/land-records) + geo buildout + sunpath mods + flood/wind
  rewrites as separate branches; Overpass self-host. Frontend via stacked PRs.

### 2026-06-21 — Phase 1 complete (Code Integration) — MERGED
All 16 PRs merged to `main`. CI fixes #60 (paths-filter perms) + #70 (`@sat/flags` tsconfig).
Backend (9): planning #59 · infrastructure #61 · future-infra #62 · land-records #63 · geo #64 ·
sunpath-3d #65 · flood #66 · wind #67 · overpass-selfhost #68 — each ships contract + CHANGELOG +
flag(s) default-off + compose block + smoke. Frontend (3, stacked): redesign base #69 →
public-landing #71 → rainfall-radar #72 (qnit-rebrand + map-measurements + 3d-fix folded into
base). Docs #73 (root CLAUDE.md FE gotchas). Agents → Site-Analysis/agents #1. `main` verified:
11 compose services + overpass-db volume, 20 flags (no dupes, ruff clean), `apps/web` builds
clean. FVDs SAT-10..18 + 04b/07b/09b. Deferred → Phase 6: landing CTA cross-domain
(qnit.site/login), per-service `OVERPASS_URL` mirror wiring.

### 2026-06-21 — Phase 2 complete (Documentation Consolidation)
- **Test inventory** → `docs/testing/TEST-INVENTORY.md`: every smoke + integration test, what it
  asserts, flag, run command. Re-ran smoke on SAT `main`: **55 passed, 0 failed** across 10
  `*_smoke.py` files (+ 2 xfailed in `temperature_imd_validation.py`, IMD data not mounted).
- **Stage B suite imported** (was absent in Phase 1) → `tests/integration/` (10 live-HTTP tests,
  PR `chore/testing-import` #74) + reports `docs/testing/{matrix,results,scenarios}.md`. Last full
  run 62/62 (Fallback) — re-run against live SAT stack in Phase 4.
- **Architecture docs** → `docs/architecture/services.md` (ports/routes/contracts/flags/deps) +
  `frontend.md` (routing, Supabase auth, backend base URLs). Recorded the **`request.headers.host`
  / middleware redirect is NOT yet implemented** — landing/tool split is client-side; deferred to
  Phase 5/6.
- **Deploy staging** → `docs/deployment/`: `utilization-estimate.md` (B6 sizing) + `README.md`.
  Ports reconcile with the plan (rainfall 8004, geo 8005 ✓). **Found:** `infra/DEPLOY.md` prod
  `FLAGS` string is stale — 2 phantom flags (`terrain.analysis`, `simulation.3d`) + 4 missing
  rainfall flags vs the 20-flag registry. Fix in Phase 4.
- `contracts/CHANGELOG.md` verified complete through v2.8.0 (every service version) — no change.
- Docs-only PR `docs/consolidation`.

### 2026-06-21 — Phase 3 complete (Pre-Deployment Setup)
- **Path:** Chrome-extension MCP unavailable this session → ran via CLIs (`aws`, `vercel`,
  `supabase`) instead of autonomous browser. Secrets → `.env.production` (gitignored; added the
  pattern to `.gitignore`), index → `deployment/secrets-manifest.md`.
- **AWS EC2 (Mumbai `ap-south-1`)** — `i-0e709db0b743075ee` t3.medium, Ubuntu 24.04
  (`ami-006f82a1d5a27da54`), 30 GB gp3. SG `sg-00c0f45009ce9cc37` (22←admin IP /32, 80, 443).
  **Elastic IP `65.1.245.213`** associated. Key `~/.ssh/qnit-ec2.pem`. No stack installed (Phase 4).
- **Vercel** — project `qnit-web`. 14 Production env vars staged: 11 API URLs all =
  `https://api.qnit.site` (Caddy multiplexes by path prefix), `NEXT_PUBLIC_SUPABASE_URL`,
  `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`, `NEXT_PUBLIC_MAPTILER_KEY`. Domains `qnit.site` +
  `qnit.in` reserved (verify in Phase 5). Git→repo connect deferred (needs GitHub Login Connection).
- **Supabase** — reused existing **SAT** project (Tokyo `ap-northeast-1`). URL + publishable key
  collected. `public` schema empty (0 tables, 0 migrations; no repo `.sql` — nothing to apply).
  Service-role key not used by the frontend, not retrieved. Auth URL config = dashboard step.
- **GoDaddy DNS (live + verified)** — `qnit.site` A @→`76.76.21.21`, `api`→`65.1.245.213`;
  `qnit.in` A @→`76.76.21.21` (overwrote parked / WebsiteBuilder apex with user approval).
- **Phase 4/5 carry-forward:** (1) Vercel→GitHub Login Connection + repo link (Phase 5);
  (2) Supabase Auth URL config (Site URL `https://qnit.site` + redirect allow-list) — dashboard;
  (3) Caddy must route **both** `/temperature/*` and `/weather/*` → temp svc (FE calls `/weather/*`);
  (4) SG port 22 pinned to a dynamic admin IP — re-add before SSH; (5) Supabase advisors:
  leaked-password protection off, `public.rls_auto_enable()` SECURITY DEFINER exposed to anon.

---

## Feature build timeline

Folded from `apps/web/CHANGELOG.md` (frontend) and `contracts/CHANGELOG.md` (services). Newest
first.

### 2026-06-20 — Rainfall radar + nav cleanup + landing copy
- **`RainfallRadar`** — SVG spider/radar chart in the rainfall right panel (12 month spokes, scale
  rings, monsoon months highlighted). Replaces the confusing `RainfallRose` petal map overlay;
  `RainfallOverlay` (annual badge + legend) restored on the map. Monthly chart → horizontal bars.
- **Nav search removed** — `SearchBar` (TopNav `centerContent`) dropped; `MapSearch` (Nominatim) is
  the sole address lookup. "Use current location" → floating map button; "Start Analysis" → bottom
  of `ModuleSelector`.
- **Landing copy** — "Ranjita" → "Ranjitha"; headline reworked; "Architecture Dialogue" firm
  citations removed (→ "Bengaluru practice"); PLG section trimmed.

### 2026-06-20 — Qnit rebrand + public landing page
- **Rebrand: Qnit by GeoKnit** — product rename across all user-facing strings (TopNav, login,
  dashboard, settings, export, land-records panel). Code identifiers/layer names unchanged.
- **Public landing** (`/`) — full marketing page (`LandingPage.tsx` + `landing.module.css`) for
  logged-out visitors; logged-in → `/dashboard` (client-side `useEffect`). `qnit-logo.svg` replaces
  the SAT diamond. Fonts → Inter + Space Grotesk + Space Mono (Geist aliases kept for back-compat).

### 2026-06-20 — Map measurements + flood-zone rework + forest-green accent
- **`SiteConfigCard`** — editable site name + lat/long, perimeter, area, vertex-angle chips, and a
  Dimensions toggle wired to the draw store.
- **Polygon measurement overlay (live)** — DOM-mutation overlay outside React render: segment
  length labels, interior-angle chips, cursor tooltip (distance/angle/area/perimeter). Static
  labels persist on commit; congestion/zoom-stability handled.
- **Flood risk zones** — now scale the drawn site polygon outward per intensity (cosLat-corrected),
  rendering one zone colored by the dominant flood driver (was 4 concentric circles).
- **Accent → forest green** `#306223` (was sage `#657166`), 57 instances / 14 files.

### 2026-06-19 — 3D fix + compass + infra hardening
- **3D blank-canvas fix** — removed `renderer.setPixelRatio` on the shared MapLibre canvas
  (`Scene3D.tsx`); the double-dpr buffer was rendering tiles into a quarter of the canvas.
- **MapCompass redesign** (diamond needle) + toggles repositioned below it; **profile dropdown**
  in TopNav (name/email/Settings/Sign out); Settings tab pill removed.
- **Overpass mirror** — `overpass-api.de` → `overpass.openstreetmap.fr` (geo/planning/flood) +
  `maps.mail.ru` (infrastructure burst); telecom query colon-key fix. CORS 5173→3000;
  `reactStrictMode: false` (Leaflet double-mount). DrawTools delete-button + zoning-timeout +
  amenities graceful-fallback + land-records healthcheck (curl) fixes.

### Service contracts (backend) — see `contracts/CHANGELOG.md`
- Live-data rewrites: flood v1.7.0 (Open-Meteo SRTM/ERA5 + OSM water), wind v1.2.0 (Open-Meteo
  ERA5 10 m). sunpath v1.6.0 (`/sunpath/solar-day` for 3D study). New services: planning, infra,
  future-infra, land-records, geo buildout (each v1.0.0). rainfall v2.0.0 (climate intelligence).
  temperature v1.1.0 (live climate-archive + thermal-grid). Aggregate contract version 2.8.0.

---

_Phase log appended by the executor as each phase completes._

### Phase 4 complete — 2026-06-21 — backend live at https://api.qnit.site
Backend stack deployed to the single AWS t3.medium (Mumbai), multi-container
docker-compose + Caddy reverse proxy (TLS auto via Let's Encrypt). New committed
artifacts: `docker-compose.aws.yml` (4 GB right-size: workers=1, per-service
`mem_limit`, `restart: unless-stopped`, Caddy service), `infra/Caddyfile` (path-prefix
routing incl. `/weather/*` for the FE + `/status/<svc>` health aliases),
`docs/deployment/phase4-baseline.md`. Fixed stale `infra/DEPLOY.md` FLAGS string
(20-flag authoritative set; dropped 2 phantom flags, added 4 rainfall flags).
**Overpass off-box** — public mirror (`overpass-api.de` + 2 fallbacks); self-host
disabled (inactive `selfhost` profile) as it doesn't fit 4 GB. CORS per-service
(`["https://qnit.site"]` JSON-array form — required by sunpath's pydantic `list[str]`).
Verified: 10/10 healthy, valid TLS, flag gating 200/403, exact-origin CORS, all 18
`apps/web` paths route, RAM ~1.37 GB used / 3.83 GB (2.46 GB free), health p50 219ms.

### Phase 5 complete — 2026-06-21 — frontend live at https://qnit.site (+ https://qnit.in)
One Vercel deployment, two domains, host-routing in `apps/web/proxy.ts` (Next 16 renamed
the `middleware` convention to `proxy`). `qnit.in` serves the marketing landing only;
`qnit.site` serves the tool and owns all auth (`.in` and `.site` are different registrable
domains, so no shared session cookie). Routing: `qnit.in/` → landing, `qnit.in/<deep>` →
`308` to `qnit.site`; `qnit.site/` → `307 /login` (the login page client-redirects to
`/dashboard` when a session already exists). Auth stays client-side (Supabase
localStorage/PKCE) — no SSR cookie refactor. Landing CTAs point at absolute
`NEXT_PUBLIC_LOGIN_URL` (default `https://qnit.site/login`) so `qnit.in` visitors
authenticate on the correct domain. Shipped in **PR #79** (`feat/host-routing`). Vercel
project `qnit-web`: Root Directory `apps/web`, Next.js, 15 Production env vars (Supabase +
MapTiler + all API URLs → `https://api.qnit.site`, Caddy path-multiplexes). Both domains
attached with verified A-record DNS (GoDaddy apex → `76.76.21.21`). Live-verified:
production deploy READY, host-routing 307/308/200 correct on both domains, TLS HTTP/2 with
no warnings, proxy deployed as `/_middleware`. Email + Google login confirmed working →
`/dashboard`.
