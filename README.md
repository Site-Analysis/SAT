# Qnit — cited, India-specific site intelligence

**Proprietary — All Rights Reserved.** Source-available for transparency only; no license to use, copy, modify, or deploy is granted. See [LICENSE](LICENSE).

Live: [qnit.in](https://qnit.in) (landing) · [qnit.site](https://qnit.site) (app) · `api.qnit.site` (backend).

---

## What it is

Qnit is a site-analysis tool for builders, architects, and due-diligence teams. Draw or search a site and it aggregates environmental and regulatory context — flood risk, sun path, wind, rainfall, temperature, zoning, planning capacity, and infrastructure — into one view. Every output is **cited with its source name, dataset version, and last-updated date**, and the full report is exportable to a RERA / bank-grade landscape PDF.

The product replaces the exploratory layer of site assessment (aggregation, consolidation, initial interpretation) that today costs ₹20,000–₹50,000 per site in consultant fees, before statutory reports are commissioned.

## Features

**Visual analysis modules** (interactive map + charts):
- **Sun path** — annual solar geometry and shading
- **Flood** — risk zones scaled by severity
- **Temperature** — annual thermal profile (Open-Meteo / IMD)
- **Wind** — directional analysis and rose
- **Rainfall** — archive, seasonality, anomaly, climate profile

**Data-context modules** (cited tabular/overlay output):
- Zoning & land use · Planning site capacity · Infrastructure connectivity
- Soil & water constraints · Amenities · Growth pipeline · Land records · KGIS context

Every module is **feature-flag gated** (`packages/flags`) and ships disabled by default until validated.

## Architecture

| Layer | Stack |
|---|---|
| **Frontend** | Next.js 16 + React 19 + Tailwind v4 + react-leaflet, in `apps/web` |
| **Backend** | 10 FastAPI services (`services/*`), one process per domain |
| **Auth & persistence** | Supabase (Google OAuth + project storage) |
| **Deploy** | EC2 (Mumbai) behind Caddy at `api.qnit.site`; Vercel dual-domain frontend |

### Services & ports

| Service | Port | Domain |
|---|---|---|
| `temperature` | 8000 | Annual temperature (Open-Meteo) |
| `sunpath` | 8001 | Solar geometry (pvlib) |
| `flood` | 8002 | Flood risk (GEE / MERIT-ALOS) |
| `wind` | 8003 | Wind analysis (Open-Meteo) |
| `rainfall` | 8004 | Rainfall (CHIRPS / IMD) |
| `geo` | 8005 | Amenities & KGIS context (OSM / Overpass) |
| `planning` | 8006 | Site capacity |
| `infrastructure` | 8007 | Connectivity |
| `future-infra` | 8008 | Growth pipeline |
| `land-records` | 8009 | Land records |

Self-hosted **Overpass** + **Caddy** reverse proxy complete the production stack (`docker-compose.aws.yml`).

**Data sources:** Open-Meteo, IMD, pvlib, Google Earth Engine (MERIT-ALOS DEM, CHIRPS), OpenStreetMap / Overpass.

## Monorepo layout

```
apps/web/      Next.js 16 frontend (the Qnit app + landing page)
services/      10 FastAPI services (one dir per domain, app/main.py each)
packages/      Shared libraries — flags, clients, schemas
contracts/     OpenAPI specs (contract-first, written before service code)
migrations/    Database migrations and schema notes
infra/         Caddyfile and deployment assets
docs/          Architecture, integration rules, feature-validation docs
scripts/       Tooling and automation
tests/         Cross-service smoke tests
```

## Dev quickstart

**Frontend:**
```bash
cd apps/web
npm install
npm run dev          # http://localhost:3000
```

**A backend service** (per service, Python 3.12):
```bash
cd services/temperature
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
FLAGS=feature.temperature.thermal-profile uvicorn app.main:app --reload --port 8000
```
Set `FLAGS=` (comma-separated) to the flags a module needs — see `packages/flags/src/flags.py`.

**All services at once:**
```bash
docker-compose up
```

**Tests** (one smoke file per process):
```bash
for f in tests/*_smoke.py; do pytest "$f"; done
```

## Engineering rules

- **Contract-first** — API changes land in `contracts/` before any service code.
- **Flag-default-off** — new functionality ships behind a flag, enabled only after validation.
- **One feature per PR** — branch → PR → green CI → merge; never push to `main`.

See [`docs/integration-rules.md`](docs/integration-rules.md) and [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

© 2026 Qnit. All rights reserved. Proprietary & source-available — public for transparency only; no license to use, copy, modify, or deploy is granted. See [LICENSE](LICENSE). Enquiries: chiragds0117@gmail.com
