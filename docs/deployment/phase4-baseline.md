# Phase 4 — Backend Deploy Baseline

Single AWS t3.medium (4 GB, Mumbai ap-south-1), multi-container docker-compose + Caddy.
Bring-up: `docker compose -f docker-compose.yml -f docker-compose.aws.yml up -d`.
Live at **https://api.qnit.site** (Let's Encrypt TLS, auto-renew).

## Overpass — OFF-BOX (public mirror)

Self-hosted Overpass does **not** fit 4 GB alongside the 10 services, so the `overpass`
service is disabled in `docker-compose.aws.yml` (assigned to an inactive `selfhost`
compose profile). OSM-backed services use a public mirror:

| Setting | Value |
|---|---|
| Primary mirror (`OVERPASS_URL`) | `https://overpass-api.de/api/interpreter` |
| Fallback mirrors | `overpass.kumi.systems/api/interpreter`, `overpass.openstreetmap.fr/api/interpreter` |
| Rate limit (primary) | fair-use ~10k req/day, no key; may throttle under concurrent load |
| Consumers via env | geo, infrastructure, planning |
| Consumers w/ public default internally | flood (`flood_service.py`), sunpath (`OVERPASS_API_URL`) |

To self-host later: move to a larger instance (≥8 GB), run a one-time
`OVERPASS_MODE=init`, then enable the `selfhost` profile.

## Feature flags

All **20** flags enabled, sourced from `packages/flags/src/flags.py` (authoritative).
`infra/DEPLOY.md`'s older string was stale (2 phantom flags `terrain.analysis` /
`simulation.3d`, missing 4 rainfall flags) — fixed in this PR. Set via `FLAGS=` in `.env`
(gitignored). Gating verified: flag present → 200, flag absent → 403, ungated `/health` → 200.

## Right-sizing (4 GB)

- `--workers 1` on every service (bump the hottest only if measured need).
- `mem_limit` per service (hard OOM ceiling so one service can't take the box).
- `restart: unless-stopped` + Docker healthchecks (`/health`) on all.

### RAM baseline (steady-state idle, all 10 healthy + Caddy)

| Service | Mem | Limit |
|---|---|---|
| sunpath | 252 MiB | 600m |
| temperature | 74 MiB | 350m |
| rainfall | 56 MiB | 350m |
| geo | 38 MiB | 400m |
| flood | 38 MiB | 500m |
| wind | 38 MiB | 450m |
| planning | 41 MiB | 300m |
| infrastructure | 37 MiB | 300m |
| future-infra | 36 MiB | 300m |
| land-records | 37 MiB | 300m |
| caddy | 15 MiB | 96m |
| **Host total** | **~1.37 GB used / 3.83 GB (2.46 GB free)** | |

Comfortable headroom — room to bump workers later if traffic warrants.

## Caddy routing

TLS terminator for `api.qnit.site`; reverse-proxies by path prefix to the compose
network (service names). Prefixes are **not** stripped — each service serves its own
prefix natively.

| Path | → Service:port | Note |
|---|---|---|
| `/weather/*` | temperature:8000 | FE calls this directly (climate-archive, thermal-grid, thermal-profile) |
| `/temperature/*` | temperature:8000 | alias, prefix stripped (port-map label) |
| `/sunpath/*` `/buildings/*` `/shadow/*` | sunpath:8001 | annual, orientation, solar-day |
| `/flood/*` | flood:8002 | |
| `/wind/*` | wind:8003 | |
| `/rainfall/*` | rainfall:8004 | archive, summary |
| `/geo/*` | geo:8005 | amenities, soil, water-constraints, zone |
| `/planning/*` | planning:8006 | |
| `/infrastructure/*` | infrastructure:8007 | |
| `/future-infra/*` | future-infra:8008 | pipeline |
| `/land-records/*` | land-records:8009 | lookup |
| `/status/<svc>` | each `/health` | external health alias (avoids root `/health` collision) |

All 18 `apps/web` API paths verified to map to a route (no missing aliases).

### CORS

Handled per-service (FastAPI `CORSMiddleware`), **not** in Caddy (avoids duplicate
`Access-Control-Allow-Origin`). Origin locked to `https://qnit.site` via
`CORS_ORIGINS=["https://qnit.site"]` in the override. JSON-array form is required —
sunpath's `Settings.CORS_ORIGINS` is a pydantic `list[str]` that crashes on a bare
string; the other 9 services' `_parse_cors_origins` accept the JSON form too.
Verified: preflight returns exact origin (not `*`).

## Latency baseline (HTTPS, from outside ap-south-1)

| Probe | Result |
|---|---|
| `/status/temperature` ×30 sequential | min 211ms · p50 219ms · p90 228ms · max 240ms |
| 20 concurrent | all complete in 325ms (no contention) |
| `/sunpath/annual` functional | 314ms, 200 |

The ~210ms floor is geographic RTT to Mumbai; server compute is tens of ms.

## Verification summary

- 10/10 services healthy (Docker healthchecks + external `/status/<svc>` = 200).
- TLS valid (Let's Encrypt, tls-alpn-01).
- Flag gating: 200 with flag / 403 without (live-tested on sunpath).
- CORS: exact-origin echo for `https://qnit.site`.
- All `apps/web` API paths route correctly.
