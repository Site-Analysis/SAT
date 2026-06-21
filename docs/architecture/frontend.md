# Frontend Map — `apps/web`

Next.js 16 (App Router) + React 19 + Tailwind v4 + react-leaflet 5 + zustand 5 + recharts 3.
Rebranded **Qnit by GeoKnit**. Dev server on `:3000` (`npm run dev`). Design tokens live in
`app/globals.css` (warm architectural palette; forest-green accent `--color-brand-primary:
#306223` — the older sage `#657166` and any Deep-Navy/Teal references are stale).

## Routes

| Route | File | Purpose |
|---|---|---|
| `/` | `app/page.tsx` | **Landing** (`components/landing/LandingPage.tsx`) for logged-out visitors. Logged-in users are redirected to `/dashboard` client-side (`useEffect`). |
| `/login` | `app/(auth)/login/page.tsx` | Supabase auth (email/password + Google OAuth). |
| `/dashboard` | `app/dashboard/page.tsx` | Project list / entry to analyses. |
| `/project/new` | `app/project/new/page.tsx` | Map + draw site + module selector → start analysis. |
| `/project/[id]` | `app/project/[id]/page.tsx` | Interactive analysis map (+ `/loading`, `/export` sub-routes). |
| `/settings` | `app/settings/page.tsx` | Profile / settings. |

Root layout `app/layout.tsx` loads fonts (Inter + Space Grotesk + Space Mono) and mounts
`components/AuthHydrator.tsx`.

## Landing vs tool — domain routing (⚠ NOT YET IMPLEMENTED)

The **target** topology (`deployment-plan.md`): one Vercel deployment serving two domains —

- `qnit.in` → marketing landing only; "Login" CTA is a plain link to `https://qnit.site/login`.
- `qnit.site` → the authed tool; Supabase auth lives here. Middleware: unauthenticated `/` →
  `302 /login`; authenticated `/` → `302 /dashboard`. The app would branch on
  `request.headers.host` (`.in` vs `.site`).

**Current reality:** there is **no `middleware.ts`** and **no `request.headers.host` branch** in
the codebase. Today both the landing and the tool are served from the same app at `/`, and the
logged-out/logged-in split is done **client-side** in `app/page.tsx` (`useEffect` redirect to
`/dashboard`). The landing CTA target and the host-based split are **deferred to Phase 5/6**
(env-driven CTA → `qnit.site/login`; middleware redirect). Document this gap before relying on it.

> Cross-domain note: `.in` and `.site` are separate registrable domains, so a Supabase cookie
> set on one is not readable on the other. That is *why* all auth must live on `qnit.site` and
> `qnit.in` stays marketing-only — there is no cookie handoff to build.

## Supabase auth flow

- Browser client: `lib/supabase/client.ts` — `createClient(NEXT_PUBLIC_SUPABASE_URL,
  NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY)`. (Env var is `PUBLISHABLE_KEY`, **not** `ANON_KEY` —
  documented gotcha in root `CLAUDE.md`.)
- `lib/env.ts` requires `NEXT_PUBLIC_SUPABASE_URL` at runtime (`requireEnv`).
- `components/AuthHydrator.tsx` hydrates the auth/session state into the zustand store on mount;
  pages read session from the store. Sign-in (`signInWithOAuth` Google + email/password) on
  `/login`; sign-out from the TopNav profile dropdown (`supabase.auth.signOut()` + store clear).
- Auth is **client-side** (no server middleware guard yet — see the gap above). Project
  persistence is in Supabase (not FastAPI).

## Backend base URL configuration

Two layers in `lib/api/`:

1. `lib/api/client.ts` — generic helper: `API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? ""`,
   `fetch(\`${API_BASE}${path}\`)`.
2. `lib/api/analysis.ts` — **per-service** base URLs, each its own env var with a `localhost`
   dev default:

| Module | Env var | Dev default |
|---|---|---|
| flood | `NEXT_PUBLIC_FLOOD_API_URL` | `http://localhost:8002` |
| sunpath | `NEXT_PUBLIC_SUNPATH_API_URL` | `http://localhost:8001` |
| wind | `NEXT_PUBLIC_WIND_API_URL` | `http://localhost:8003` |
| temperature | `NEXT_PUBLIC_TEMPERATURE_API_URL` | `http://localhost:8000` |
| rainfall | `NEXT_PUBLIC_RAINFALL_API_URL` | `http://localhost:8004` |
| zone / amenities | `NEXT_PUBLIC_GEO_API_URL` | `http://localhost:8005` |
| planning | `NEXT_PUBLIC_PLANNING_API_URL` | `http://localhost:8006` |
| infrastructure | `NEXT_PUBLIC_INFRA_API_URL` | `http://localhost:8007` |
| growth (future-infra) | `NEXT_PUBLIC_FUTURE_INFRA_API_URL` | `http://localhost:8008` |
| land | `NEXT_PUBLIC_LAND_RECORDS_API_URL` | `http://localhost:8009` |

In production all of these point at the Caddy reverse proxy on `api.qnit.site` (per-service
routes `/temperature/*`, `/sunpath/*`, … — see `docs/architecture/services.md`).
`NEXT_PUBLIC_*` vars are **inlined at build time** — rebuild on Vercel whenever they change.

## Map / draw internals

Leaflet map; Three.js 3D on a shared MapLibre canvas (`components/three/Scene3D.tsx` — the
double-`setPixelRatio` blank-canvas bug is fixed). Polygon measurement overlay mutates DOM
outside the React render cycle. `RainfallRadar` (recharts/SVG spider chart) lives in the rainfall
right panel; `RainfallOverlay` (not `RainfallRose` — removed) on the map. Five FE gotchas
(Supabase key name, `AuthHydrator` render block, dynamic-import double-removal, Rose-vs-Overlay
naming, `TopNav centerContent`) are in root `CLAUDE.md`; CSS-module + monthly-rainfall data-path
notes in `apps/web/CLAUDE.md`.
