# CLAUDE.md

Guidance for Claude Code working in the SAT monorepo.

## Repo Purpose

Canonical, deployable build of the Site Analysis Tool. Heavy features are migrated here one at a time from `/Volumes/LocalDrive/Site Analysis/` (review/cleanup workspace) after passing FVD validation. **No feature code lands without a contract, a flag, and a smoke test.**

## Repo State

- Public GitHub repo: `Site-Analysis/SAT`
- Main branch protected: 1 review + CI required, no direct push
- All changes via feature branch + PR
- `.claude/` is **partially** committed — team-shared agents/skills/commands/`settings.json` ARE in git; only `.claude/mcp.json` and `.claude/settings.local.json` are gitignored (they hold per-developer credentials). See § Claude Tooling for the full split.

---

## Layout

```
apps/web/              Next.js 16 + React 19 frontend (port 3000)
services/              FastAPI backends (one per analysis type)
  temperature/         port 8000 — thermal profile (IMD + Open-Meteo)
  sunpath/             port 8001 — solar / sun path (pvlib)
  flood/               port 8002 — flood risk (GEE + MERIT/ALOS)
  wind/                port 8003 — wind climatology
  geo/                 port 8004 — base geo / vegetation / admin boundaries
packages/flags/        Shared feature flag enum + helper
contracts/             OpenAPI YAML — one per service + CHANGELOG.md
migrations/            DB migrations + rollback notes
infra/                 Deployment assets
docs/                  Architecture + feature-validation/ FVDs
scripts/               Tooling automation
tests/                 Cross-service smoke tests
```

---

## Non-Negotiable Rules

1. **Contract-first.** Update `contracts/<service>.yaml` and `contracts/CHANGELOG.md` BEFORE writing service code. CI gate fails the PR otherwise.
2. **Flag-default-off.** Every new behavior gated by a `FeatureFlag` enum value in `packages/flags/src/flags.py`. Enable via `FLAGS=` env var only after validation.
3. **One feature per PR.** Tooling/refactor exceptions allowed but rare. PRs touching `contracts/` must update `contracts/CHANGELOG.md` (CI enforced).
4. **No direct push to main.** Branch + PR + 1 review + green CI.
5. **No secrets in committed files.** `.env`, `.claude/mcp.json`, and `.claude/settings.local.json` are gitignored. Never paste tokens, API keys, service-account JSON, or personal emails into any tracked file. Use `.env.example` for documentation and reference env vars in code/docs.
6. **FVD before code.** New feature requires `docs/feature-validation/SAT-XX_*.md` first. Acceptance criteria → code traceability is the contract for migration.

See `docs/integration-rules.md` for the canonical statement.

---

## Dev Workflow

### Frontend
```bash
cd apps/web
npm install              # first time
npm run dev              # http://localhost:3000
npm run build
```

Note: Next.js 16 has breaking changes. Read `apps/web/AGENTS.md` and `node_modules/next/dist/docs/` before writing component code.

### Services (per service)
Each service gets its own `.venv/`. **Use `python3.12`** — 3.14 is missing wheels for earthengine-api, pvlib, imdlib, netCDF4:
```bash
cd services/<service>
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port <port>
```

### Full stack via Docker
```bash
docker-compose up        # all services + web
```

### Lint + format
```bash
ruff check services/ packages/flags/src/flags.py
ruff format services/ packages/flags/src/flags.py
cd apps/web && npm run lint
```

Pre-commit hook (auto-runs ruff on staged Python files):
```bash
pip install pre-commit
pre-commit install       # once per clone
```

### Tests
```bash
# Smoke tests: ONE FILE PER PROCESS. Every service ships a package named `app`;
# running all *_smoke.py in one pytest process merges them into one namespace
# and they shadow each other. conftest deliberately does NOT add all service
# dirs to sys.path — each smoke file self-inserts its own + sys.modules.pop("app").
for f in tests/*_smoke.py; do pytest "$f"; done   # CI does this
pytest tests/sunpath_smoke.py    # or one at a time
```

---

## Feature Migration Workflow

Source: `/Volumes/LocalDrive/Site Analysis/` (review workspace, separate dir)
Target: `services/<service>/`

For each feature:
1. Confirm FVD exists at `docs/feature-validation/SAT-XX_*.md` with all ACs mapped to commits/functions
2. Review source code in Site Analysis workspace; fix issues there first
3. Update `contracts/<service>.yaml` + `contracts/CHANGELOG.md`
4. Add `FeatureFlag` enum entry, default off
5. Copy cleaned source: `Site-Analysis-Tool/src/Backend/<Service>/app/` → `services/<service>/app/`
6. Add `requirements.txt`, `pyproject.toml`, `Dockerfile`
7. Add service block to `docker-compose.yml`
8. Add smoke test: `tests/<service>_smoke.py`
9. Wire frontend in `apps/web/` behind same flag
10. Open PR `feat/<service>-service` → review → CI → merge
11. Enable flag in production `.env` only after manual validation

Use the `feature-migrator` agent (in `.claude/agents/`) to drive this end-to-end.

---

## Feature Flags

```python
# packages/flags/src/flags.py
class FeatureFlag(StrEnum):
    TEMPERATURE_THERMAL_PROFILE = "feature.temperature.thermal-profile"
    FLOOD_RISK_ANALYSIS = "feature.flood.risk-analysis"
    SUNPATH_DIAGRAM = "feature.sunpath.diagram"
    WIND_ANALYSIS = "feature.wind.analysis"
    RAINFALL_ARCHIVE = "feature.rainfall.archive"
    RAINFALL_SUMMARY = "feature.rainfall.summary"
```

Enable via env var:
```bash
FLAGS=feature.temperature.thermal-profile,feature.sunpath.diagram
```

Add new flag to enum BEFORE first commit that depends on it.

---

## External Services

| Service | Used by | Setup |
|---|---|---|
| Google Earth Engine | flood, geo (vegetation, NDVI) | Service account JSON at `gee-sa.json` — copy from `/Volumes/LocalDrive/Site Analysis/Site-Analysis-Tool/gee-sa.json` |
| Open-Meteo | temperature, wind | Public, no key |
| IMD gridded data | temperature | Local files at `services/temperature/data/` |
| pvlib | sunpath | pip install only |
| Supabase | apps/web (auth, project persistence) | URL + anon key in `.env`, get from Supabase dashboard |

---

## Jira Access (MCP Broken)

**Atlassian plugin is installed and OAuth-authenticated** — use `mcp__plugin_atlassian_atlassian__*` MCP tools directly.
Cloud ID: `f53059b9-cd1d-4106-abf6-848d8e9069da`

API gotchas discovered in practice:
- **Sprint creation** requires board-level OAuth scope (not in current token) — create sprints via Jira UI board, then assign issues via API
- **`story_points` field** is not on the default create screen — do NOT pass in `additional_fields`; set via Jira UI after creation
- **Chirag's account ID**: `712020:99b3330a-a7a6-4ea9-ace5-e80e0e3e334e`

`jira-mcp` npm package (deprecated) returns HTTP 410 Gone. **Fallback** if plugin disconnects — call REST API v3 directly via Python urllib. Read credentials from env vars, never hardcode:
```bash
export ATLASSIAN_EMAIL="<your-atlassian-email>"
export ATLASSIAN_API_TOKEN="<your-token>"   # https://id.atlassian.com/manage-profile/security/api-tokens
export ATLASSIAN_BASE_URL="https://<your-workspace>.atlassian.net"
```
```python
import os, urllib.request, base64, json

email = os.environ["ATLASSIAN_EMAIL"]
token = os.environ["ATLASSIAN_API_TOKEN"]
base  = os.environ["ATLASSIAN_BASE_URL"]

creds = base64.b64encode(f"{email}:{token}".encode()).decode()
req = urllib.request.Request(
    f"{base}/rest/api/3/search/jql",
    data=json.dumps({"jql": "project=SAT AND status=Done", "maxResults": 100}).encode(),
    headers={"Authorization": f"Basic {creds}", "Content-Type": "application/json"},
)
data = json.loads(urllib.request.urlopen(req).read())
```

Do **not** paste a token into any tracked file. `.claude/mcp.json` (gitignored) is the only acceptable place to persist it for MCP use.

---

## Claude Tooling

This repo is fully wired for Claude Code. Most context lives in this file (`CLAUDE.md` at repo root). Agents, skills, and slash commands are in `.claude/`.

### Committed (team-shared)
- `.claude/agents/feature-migrator.md` — migrates one feature end-to-end from review workspace → SAT
- `.claude/agents/contract-validator.md` — validates OpenAPI YAML against FastAPI route signatures
- `.claude/commands/security-review.md` — Anthropic's `/security-review` (run before merging any PR)
- `.claude/skills/migrate-feature/` — `/migrate-feature <service>` skill, orchestrates the migration agents
- `.claude/settings.json` — team plugin marketplace config

### Local-only (gitignored — copy from Site Analysis workspace)
- `.claude/mcp.json` — GitHub + Jira MCP servers (contains tokens)
- `.claude/settings.local.json` — per-developer permission overrides

### Recommended plugins (install once per developer)
Run these in a Claude Code session to install to your user scope:

```
/plugin install atlassian@claude-plugins-official        # Jira/Confluence (replaces broken jira-mcp)
/plugin install supabase@claude-plugins-official         # apps/web auth + DB
/plugin install commit-commands@claude-plugins-official  # standardized git workflow
/plugin install pr-review-toolkit@claude-plugins-official # multi-agent PR review
/plugin install typescript-lsp@claude-plugins-official   # TS code intelligence (Next.js)
/plugin install pyright-lsp@claude-plugins-official      # Python type checking (services)
```

After install: `/reload-plugins`.

### Global skills
- `graphify` (`~/.claude/skills/graphify/`) — `/graphify <path>` builds knowledge graphs

### First-time setup checklist (new clone)
1. `cp -r /Volumes/LocalDrive/Site\ Analysis/.claude/mcp.json /Volumes/LocalDrive/SAT/.claude/mcp.json`
2. `cp /Volumes/LocalDrive/Site\ Analysis/.claude/settings.local.json /Volumes/LocalDrive/SAT/.claude/settings.local.json`
3. `cp /Volumes/LocalDrive/Site\ Analysis/Site-Analysis-Tool/gee-sa.json /Volumes/LocalDrive/SAT/gee-sa.json`
4. `cp .env.example .env` then fill Supabase keys
5. `npm install` (root) — installs workspaces
6. `pip install pre-commit && pre-commit install` (root)
7. Open Claude Code in this dir, run the `/plugin install` commands above

---

## Gotchas (learned)

- **`app` name collision.** Every service's package is literally `app`. Never run cross-service tests in one process (see § Tests). New smoke file must self-insert its service dir + `sys.modules.pop("app")` + set FLAGS via `monkeypatch` per-test.
- **CHANGELOG is one aggregate, monotonic version.** `contracts/CHANGELOG.md` rises across ALL services (1.1.0 temp → 1.2.0 rainfall → … → 1.6.0 flood). Parallel PRs collide on version numbers — pick the next free one when rebasing. The CI contract gate requires `contracts/CHANGELOG.md` to appear in the PR's diff vs `main`, so if a sibling PR already merged your entry, add a fresh dated entry.
- **Service PRs carry siblings' files.** A branch forked before a sibling merged ships a stale copy of that sibling (e.g. flood/wind PRs each re-added `rainfall`). Merge `main` into the branch and verify the sibling's files are byte-identical to `main` before merging — else you silently revert it.
- **Flags enforced in-process, per service.** Each service reads `os.getenv("FLAGS")` directly and raises `HTTPException(403)` — it does NOT import `packages/flags` (that's outside the Docker build context). Gated endpoints return 403 unless `FLAGS=` lists the flag.
- **Stubs must be honest.** Synthetic/deterministic services set `data_source`/`source` to `"synthetic"` or `"deterministic-fallback"`, never a real provider name like `"open-meteo"`. Mislabeling fake data is a review blocker.
- **Local run without Docker:** per-service `.venv` uvicorn; `rainfall` has no venv (reuse `flood`'s — same deps). Must export `FLAGS` or every gated endpoint 403s. GEE absent → services log `GEEServiceError` but degrade gracefully.

### Frontend (`apps/web`) — map / draw (from SAT-Fallback `1d0c0d0`)

- **zsh glob with bracket paths in git.** `git add apps/web/app/project/[id]/page.tsx` fails — zsh treats `[id]` as a glob. Single-quote: `git add 'apps/web/app/project/[id]/page.tsx'`.
- **Leaflet labels outside `.leaflet-map-pane` — zoom animation.** Labels appended to `map.getContainer()` (siblings of `.leaflet-map-pane`) freeze at stale pixel positions during Leaflet's CSS scale-zoom and appear to jump/teleport. Hide on `zoomstart`, redraw on `zoomend`; use `move` only for pan (see `DrawTools.tsx`).
- **Leaflet event timing.** `move` fires continuously during pan; `zoom` fires once at the end of an animated zoom (not per-frame); `zoomstart`/`zoomend` bracket the animation. Split listeners when pan vs zoom need different handling — don't pass `"move zoom"`.
- **DOM-mutation overlays for mousemove-rate updates.** Tooltips updating every `mousemove` (drawing measurements) must write to a `div` ref via `el.innerHTML`/`appendChild`, never React state — state re-renders at mousemove rate lag visibly (`DrawTools.tsx → renderMeasure()`).
- **Geographic polygon scaling needs cosLat.** Scaling a polygon from its centroid in raw lat/lng distorts E–W (lng degrees are shorter). Apply `dLng*cos(cLat·π/180)`, scale, divide back. Matters at Indian latitudes (~12°N, cosLat≈0.978) — `FloodZoneRings.tsx → scalePoly()`.
- **Three.js + MapLibre shared canvas — never `setPixelRatio()`.** MapLibre already sets `canvas.width = cssWidth × devicePixelRatio`; calling `renderer.setPixelRatio(dpr)` on the shared canvas doubles the buffer (tiles render only in the bottom-left quarter). `Scene3D.tsx` relies on `render()`'s `setViewport(gl.drawingBufferWidth, …)` instead.

---

## Related Docs

- `docs/integration-rules.md` — short canonical rule statement
- `docs/feature-flags.md` — flag conventions
- `docs/feature-validation/` — FVDs (one per Jira ticket)
- `docs/PROGRESS.md` — master timeline + sprint log
- `contracts/CHANGELOG.md` — contract version history
- `apps/web/AGENTS.md` — Next.js 16 specific rules
