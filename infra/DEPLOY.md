# SAT-Fallback — Deployment Checklist

Stack: 10 FastAPI services + Next.js 16 frontend + self-hosted Overpass (wiktorn/overpass-api).

---

## Required secrets (never commit these)

| Variable | Where set | Description |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | `apps/web/.env.local` + CI | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | `apps/web/.env.local` + CI | Supabase anon/publishable key |
| `FLAGS` | root `.env` | Comma-separated feature flags (all 18, see below) |
| `GEE_SA_KEY_PATH` | root `.env` | Path to GEE service-account JSON inside container |
| `GEE_SERVICE_ACCOUNT_KEY_PATH` | root `.env` | Same as above (`/app/gee-sa.json`) |
| `OVERPASS_URL` | root `.env` | `http://overpass:80/api/interpreter` (local) or public mirror |
| `IMD_DATA_DIR` | root `.env` | `/app/data` — IMD rainfall data dir |

Ship `gee-sa.json` out-of-band (scp / secrets manager). Do NOT commit.

### Full FLAGS value
```
FLAGS=feature.temperature.thermal-profile,feature.flood.risk-analysis,feature.sunpath.diagram,feature.sunpath.solar-day,feature.wind.analysis,feature.rainfall.archive,feature.rainfall.summary,feature.terrain.analysis,feature.simulation.3d,feature.zoning.land-use,feature.planning.site-capacity,feature.infrastructure.connectivity,feature.environment.soil,feature.environment.water-constraints,feature.context.growth-pipeline,feature.land.records,feature.geo.amenities,feature.geo.kgis-context
```

---

## Service image list

| Service | Port | Image source |
|---|---|---|
| temperature | 8000 | `./services/temperature` |
| sunpath | 8001 | `./services/sunpath` |
| flood | 8002 | `./services/flood` |
| wind | 8003 | `./services/wind` |
| rainfall | 8004 | `./services/rainfall` |
| geo | 8005 | `./services/geo` |
| planning | 8006 | `./services/planning` |
| infrastructure | 8007 | `./services/infrastructure` |
| future-infra | 8008 | `./services/future-infra` |
| land-records | 8009 | `./services/land-records` |
| overpass | 12345 | `wiktorn/overpass-api:latest` |
| frontend | 3000 | Next.js `next start` (built from `apps/web/`) |

---

## Build steps

### 1. Build all backend images
```bash
cd /path/to/SAT-Fallback
docker compose build
```

### 2. Build the frontend
```bash
npm install
npm run build --workspace apps/web
# Confirm .next/ exists in apps/web/
```

`NEXT_PUBLIC_*` vars are inlined at build time — rebuild whenever they change.

### 3. First-time Overpass init (one-time, 10-40 min)
```bash
docker compose up -d overpass
# Watch: docker compose logs -f overpass
# Ready when you see: "Dispatcher running" or healthcheck passes
# Validate: curl 'http://localhost:12345/api/interpreter?data=[out:json];node(around:200,12.9352,77.6733);out;'
```

After init, switch `OVERPASS_MODE` to `run` via the prod overlay (`docker-compose.prod.yml` already sets this).

### 4. Start all services (production)
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 5. Start the frontend
```bash
cd apps/web && npm run start   # port 3000
# Or via PM2: pm2 start "npm run start" --name sat-web --cwd apps/web
```

---

## Overpass notes

- **DB size (Southern Zone):** ~3-5 GB on the `overpass-db` volume (5-8× the 528 MB PBF).
- **EBS budget:** fits within 30 GB free-tier EBS if other storage is minimal.
- **After init:** change `OVERPASS_MODE=run` (already set in `docker-compose.prod.yml`). Re-running `init` re-downloads and re-indexes — avoid.
- **Updates:** run `docker compose restart overpass` after updating the PBF; or set up `OVERPASS_DIFF_URL` for incremental updates.

---

## Supabase / Google Auth

Required before first user login:
1. Supabase → Authentication → URL Configuration → Site URL `https://your-domain.com`; Redirect URL `https://your-domain.com/**`
2. Supabase → Authentication → Providers → Google → enable + paste Client ID/Secret from Google Cloud Console
3. Google Cloud Console → OAuth Client ID → Authorized redirect URI: `https://jaqlvsilsrdjeehqrump.supabase.co/auth/v1/callback`

Email/password login works without Google setup.

---

## Health check (all services)
```bash
for p in 8000 8001 8002 8003 8004 8005 8006 8007 8008 8009; do
  printf ":%s " "$p"; curl -fs "http://localhost:$p/health" && echo "OK" || echo "DOWN"
done
```

---

## Minimum instance sizing

| Config | RAM | Notes |
|---|---|---|
| AWS t2.micro (free tier) | 1 GiB | **Not sufficient** — 10 services idle = 1.3 GiB |
| AWS t3.small | 2 GiB | Minimum viable; sunpath (453 MiB) + temperature (215 MiB) tight |
| AWS t3.medium | 4 GiB | Recommended for single-tenant prod (~$30/mo) |
| AWS t3.large | 8 GiB | Comfortable for 5-10 concurrent users + Overpass |

See `testing/utilization-estimate.md` for the full free-tier analysis.
