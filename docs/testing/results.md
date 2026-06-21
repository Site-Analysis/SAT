# Stage B — Test Results

Run completed: 2026-06-18/19

---

## B3 — Integration test suite

**Initial run (2026-06-18, Overpass rate-limited):**
```
62 collected · 54 passed · 0 failed · 8 skipped
42 s wall-clock
```

**Re-run (2026-06-19, Overpass restored):**
```
62 collected · 62 passed · 0 failed · 0 skipped
113 s wall-clock
```

All 10 services healthy. Zero failures. All 8 previously-skipped Overpass tests now pass.
See `matrix.md` for per-service breakdown and mirror configuration notes.

**Key correctness findings discovered during test authoring:**

| Service | Bug / schema mismatch found |
|---|---|
| flood | Response field is `overall_score` (0–100) + `risk_category` string, not `risk_score` (0–1) |
| rainfall | `start_date` / `end_date` query params required — not documented |
| geo | Params are `lat`/`lon`, not `latitude`/`longitude` |
| geo | Amenity response is flat dict (categories as top-level keys), not `{categories: [...]}` |
| planning | `plot_area_sqm` required POST field — missing from OpenAPI description |
| infrastructure | All analysis routes 502 on public Overpass (confirmed upstream, not service bug) |
| future-infra | Params are `lat`/`lon`, not `latitude`/`longitude` |
| land-records | Endpoint is POST (not GET); uses Karnataka admin hierarchy, not lat/lon |

---

## B4 — Baseline instrumentation (single full analysis, Bellandur)

See `utilization-estimate.md` for full table. Summary:

- **Fastest:** future-infra 7 ms, land-records 23 ms, rainfall 26 ms
- **Slowest:** geo 23.5 s, planning 24.3 s (both Overpass-bound)
- **Total sequential:** ~57 s (collapses to ~10 s with Overpass mirror)
- **Peak RAM:** sunpath 436 MiB, temperature 214 MiB; total stack ~1.23 GiB

---

## B5 — Concurrency probe

| Service | Safe ceiling | Failure mode at ceiling |
|---|---|---|
| temperature | ≥20 concurrent | No failures observed |
| sunpath | ~10–15 (CPU-bound, p95 grows ~26 ms/req) | Latency degradation, no errors |
| flood | **≤5 concurrent** | HTTP 500 at N=10 (5/10 fail), N=14/20 fail at N=20 |

Flood service has a hard concurrency wall. Needs a semaphore or queue before scaling.

---

## Stage B summary

| Criterion | Result |
|---|---|
| All services healthy | ✓ |
| Test suite green (0 hard failures, 0 skips) | ✓ — 62/62 after Overpass mirror fix |
| Latency baseline captured | ✓ |
| Concurrency ceiling identified | ✓ — flood fails at N=10 |
| External dependency risks mapped | ✓ — Overpass mirror stability is critical path |
| Cost extrapolation written | ✓ — see utilization-estimate.md |

### Recommendations before beta launch

1. **Self-host Overpass** — eliminates the 25 s geo/planning latency and removes public rate-limit risk.
2. **Queue flood requests** — add semaphore (max 5 concurrent) before scaling.
3. **Cache Open-Meteo** — temperature + rainfall already fast; caching buys nothing extra at low volume.
4. **Supabase env vars** — `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` must be set in Vercel/prod before frontend launch.
5. **Google Auth** — enable provider in Supabase dashboard (Chirag's access required).
