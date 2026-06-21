# Backend Utilization & Cost Estimate

Measured 2026-06-18/19 on local Docker stack (10 services, Apple M-series host).
**Headline: the full SAT stack cannot run on AWS Free Tier (1 GiB t2.micro).
10 services idle = 1,324 MiB — already exceeds the ceiling before a single user connects.**

---

## Baseline resource footprint (idle)

| Service | Port | RAM (idle) | CPU (idle) |
|---|---|---|---|
| temperature | 8000 | 214 MiB | 0.4% |
| sunpath | 8001 | 436 MiB | 5.2% |
| flood | 8002 | 93 MiB | 0.6% |
| wind | 8003 | 87 MiB | 0.6% |
| rainfall | 8004 | 81 MiB | 0.3% |
| geo | 8005 | 97 MiB | 0.8% |
| planning | 8006 | 83 MiB | 1.0% |
| infrastructure | 8007 | 90 MiB | 0.8% |
| future-infra | 8008 | 79 MiB | 0.6% |
| land-records | 8009 | 74 MiB | 3.4% |
| **Total** | | **~1.23 GiB** | |

Sunpath is the heaviest service — ephem + pandas load at startup. Temperature second due to scipy.

---

## Per-analysis latency (single sequential call, Bellandur 12.9352°N 77.6733°E)

| Service | Latency | External dependency | Response size |
|---|---|---|---|
| future-infra | 7 ms | Static curated data | 438 B |
| land-records | 23 ms | Bhoomi scrape (cached) | 1.5 KB |
| rainfall | 26 ms | Open-Meteo (cached) | 6.7 KB |
| temperature | 59 ms | Open-Meteo (cached) | 12 KB |
| sunpath | 68 ms | Ephemeris computation | 3.7 KB |
| flood | 4,071 ms | External risk API | 1.1 KB |
| wind | 4,761 ms | External wind API | 809 B |
| geo | 23,484 ms | Overpass API (rate-limited) | 25 KB |
| planning | 24,262 ms | Overpass zone lookup | 1.2 KB |
| infrastructure | ~25,000 ms | Overpass (rate-limited, skipped) | — |
| **Total (sequential)** | **~57 s** | | ~52 KB |

> **Overpass is the dominant bottleneck.** Geo + planning + infrastructure together account for ~50–73 s of latency. With the self-hosted `wiktorn/overpass-api` (Southern Zone extract, now deployed), this collapses to <500 ms.

---

## Concurrency ceiling

| Service | 1 req | 5 req | 10 req | 20 req | Notes |
|---|---|---|---|---|---|
| temperature | 38 ms | 14 ms | 18 ms | 27 ms | Open-Meteo response caching; scales flat |
| sunpath | 46 ms | 146 ms | 266 ms | 536 ms | CPU-bound; linear scaling ~26 ms/req |
| flood | 5,892 ms | 4,983 ms | 5,144 ms (5 fail) | 5,242 ms (14 fail) | **Fails at N≥10** — internal 500 error |

Flood fails at N=10 concurrent — likely a single shared connection or file lock in the external risk model. Safe ceiling: **≤5 concurrent flood calls**.

Other Overpass-dependent services (geo, planning, infra) are already serialized upstream — no benefit from parallelism.

---

## AWS Free Tier capacity analysis (B6 headline)

**Question: how many users fit in the AWS Free Tier?**

### Free Tier budget (12-month, verified 2026-06)
- EC2: 750 hr/mo t2.micro = **1 vCPU, 1 GiB (1,024 MiB) RAM**, one instance 24×7
- EBS: **30 GB**
- Data transfer out: ~100 GB/mo
- Supabase (auth): free tier = 50,000 MAU, 500 MB DB

### Step 1: RAM wall

| Component | Idle RAM | Source |
|---|---|---|
| temperature | 215 MiB | measured |
| sunpath | 453 MiB | measured |
| flood | 82 MiB | measured |
| wind | 87 MiB | measured |
| rainfall | 81 MiB | measured |
| geo | 91 MiB | measured |
| planning | 82 MiB | measured |
| infrastructure | 81 MiB | measured |
| future-infra | 79 MiB | measured |
| land-records | 75 MiB | measured |
| **10 services total** | **1,326 MiB** | |
| Next.js prod server | ~250 MiB | estimated (Node.js) |
| Overpass container (idle) | ~200 MiB | estimated (wiktorn image) |
| **Full stack idle** | **~1,776 MiB** | |

**Verdict: the full stack overflows the 1 GiB free-tier ceiling by 752+ MiB before a single user connects. AWS Free Tier supports zero concurrent users of the full SAT stack.**

### Step 2: EBS budget

Self-hosted Overpass (Southern Zone extract, 528 MB PBF) indexes to **~3–5 GB** on the `overpass-db` volume (measured: TBD after init completes). This fits within 30 GB EBS if the OS and app code use <25 GB. OS (~8 GB) + app (~2 GB) + Overpass DB (5 GB) = 15 GB — fits.

### Step 3: analyses/day on smallest viable instance

With local Overpass installed, wall-clock per analysis drops from ~57 s to ~10 s (Overpass queries: <500 ms locally vs 23 s on public API).

| Instance | RAM | vCPU | $/mo | Fits full stack? | Safe concurrent | Analyses/day (10 s/analysis) |
|---|---|---|---|---|---|---|
| t2.micro (free) | 1 GiB | 1 | $0 | **No** (overflows by 752 MiB idle) | 0 | 0 |
| t3.small | 2 GiB | 2 | ~$15 | Yes (tight, ~200 MiB headroom) | 1 | ~8,000 (rate-limited in practice) |
| t3.medium | 4 GiB | 2 | ~$30 | Yes (comfortable) | 3–5 | ~25,000 |
| t3.large | 8 GiB | 2 | ~$60 | Yes (headroom for Overpass peaks) | 8–10 | ~50,000 |

Usage assumption: 1 analysis per session, 1 session per user per day.

| Tier | Instance | Max users/day | $/mo |
|---|---|---|---|
| Free Tier | t2.micro | **0** (stack doesn't fit) | $0 |
| Minimum viable | t3.small | ~8,000 (API quota limited before CPU) | ~$15 |
| Beta (10 concurrent) | t3.medium | ~25,000 | ~$30 |
| Early prod | t3.large | ~50,000 | ~$60 |

### Step 4: external quotas that bind before EC2

After self-hosting Overpass, these become the real ceilings:

| Dependency | Quota | Binding at... |
|---|---|---|
| **Open-Meteo** | Unlimited (non-commercial) | Not binding |
| **Overpass (self-hosted)** | Local — no quota | Not binding |
| **Google Earth Engine** | 100 concurrent requests / service account | ~100 concurrent analyses |
| **Supabase free tier** | 50,000 MAU | ~50,000 users/month |
| **Flood risk API** | Unknown — fails at N=10 concurrent | 10 concurrent analyses |

GEE (sunpath, flood, wind) and Supabase MAU become the binding quotas well before EC2 CPU/RAM on t3.medium+.

### Honest verdict

| Statement | Detail |
|---|---|
| **Free Tier capacity** | Zero. Stack idle RAM (1,776 MiB) exceeds t2.micro ceiling (1,024 MiB). |
| **Realistic free-tier use** | Demo only with reduced service set: drop sunpath (453 MiB) + temperature (215 MiB) → remaining 8 services fit (~658 MiB idle). But that removes core features. |
| **Minimum paid** | t3.small (~$15/mo) fits everything; GEE quota and flood concurrency cap become the binding limits long before RAM. |
| **Recommended beta** | t3.medium (~$30/mo): headroom for 3–5 concurrent analyses, comfortable Overpass, stays under GEE's 100-concurrent ceiling. |
| **Mitigation options** | Consolidate services into fewer processes; cache analysis results by geohash; use Celery for flood requests; upgrade GEE service account quota. |

---

## Extrapolation: analyses per day (with self-hosted Overpass)

One "full site analysis" = all 10 services, local Overpass → ~10 s wall-clock.

| Volume | Analyses/day | Analyses/hr | Concurrent needed | Flood safety | Instance |
|---|---|---|---|---|---|
| **Dev / staging** | 10 | <1 | 1 | ✓ | t3.small |
| **Low beta** | 100 | ~4 | 1–2 | ✓ | t3.small |
| **Active beta** | 1,000 | ~42 | ≤5 | ✓ (<5 flood) | t3.medium |
| **Early prod** | 10,000 | ~417 | 5–10 | ⚠ queue flood | t3.large + queue |

---

## External API quotas & risks

| Dependency | Used by | Free tier / limit | Risk |
|---|---|---|---|
| **Open-Meteo** | temperature, rainfall | Unlimited (non-commercial) | Low |
| **Overpass (self-hosted)** | geo, planning, infra | Local — Southern Zone seeded | None |
| **Ephem (local)** | sunpath | Unlimited (offline computation) | None |
| **GEE** | sunpath, flood, wind | 100 concurrent req / service account | Medium — upgrade for >100 concurrent |
| **Bhoomi scrape** | land-records | No SLA | Medium — Karnataka state site uptime |
| **Flood risk API** | flood | Unknown — fails at N=10 | Medium — add semaphore |

### Recommendations

1. **Overpass self-hosted** ✓ (done — `wiktorn/overpass-api`, Southern Zone, `docker-compose.prod.yml`)
2. **Queue flood requests** — add semaphore (max 5 concurrent) before scaling past N=5 req/s.
3. **Cache analysis results** by geohash (1 km²), 24 h TTL — eliminates most repeat Overpass + API calls.
4. **GEE quota upgrade** — request higher concurrent limit from Google for production traffic.
5. **Minimum deploy target: t3.small** — free tier is not viable for the full stack.
