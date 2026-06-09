# SAT Tech Stack (Fixed — Do Not Deviate)

These are not decisions. They are constraints. The agent operates within them.

## Frontend

| Concern        | Choice                          |
|----------------|---------------------------------|
| Framework      | Next.js 14 (App Router)         |
| Styling        | Tailwind CSS                    |
| Components     | shadcn/ui                       |
| Maps           | React-Leaflet                   |
| Charts         | Recharts                        |
| State          | Zustand (global), useState (local) |
| Icons          | Ask human in Step 17 — not assumed |
| Type checking  | TypeScript strict mode          |

## Design tooling

| Concern              | Choice                              |
|----------------------|-------------------------------------|
| Design tool          | Figma (file created from scratch in Phase 4) |
| Token system         | Figma Variables (NOT Styles)        |
| Design-to-code       | Figma MCP server (remote: mcp.figma.com/mcp) |
| Code generation      | Claude Code + Figma MCP             |
| Component instances  | MUST be Figma library instances, not flat shapes |

IMPORTANT: All Figma token values must use Variables, not hardcoded hex.
The MCP server reads Variables — hardcoded values break the design-to-code pipeline.

## Backend (reference only — agent does not build this)

| Concern    | Choice                |
|------------|-----------------------|
| Framework  | FastAPI (Python)      |
| Database   | PostgreSQL (Supabase) |
| Auth       | Supabase Auth         |
| Deployment | Vercel (FE) + Render/GCP (BE) |

The 5 live analysis services: sunpath, flood, wind, rainfall, temperature.
API endpoints are confirmed with the Backend Engineer in Step 32 before
any page-level code references them.

## Repo

| Concern          | Choice                                       |
|------------------|----------------------------------------------|
| Structure        | Single GitHub monorepo                       |
| FE location      | Ask human in Step 34 — not assumed           |
| Issue tracking   | GitHub Issues (not Jira)                     |
| Branch naming    | Ask human in Step 34 — not assumed           |
| PR convention    | Confirmed with human in Step 34              |

## Tailwind token constraint

IMPORTANT: Generated code uses ONLY token-keyed Tailwind classes.
No arbitrary values. No hardcoded hex in className.
✅ `className="bg-brand-primary"` (maps to CSS var from token)
❌ `className="bg-[#1A7F7A]"` (hardcoded — forbidden)
