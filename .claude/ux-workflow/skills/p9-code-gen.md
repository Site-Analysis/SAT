# Phase 9 — Frontend Code Generation
# Steps 34–38 | Scaffold → components → pages → QA → monorepo PR

## Phase goal
Generate production-ready Next.js 14 frontend code — token-compliant,
component-accurate, API-integrated — and commit it to the SAT monorepo.

## Code generation rules (ABSOLUTE)

1. Token compliance: ALL styling uses token-keyed Tailwind classes only.
   ✅ `bg-brand-primary` ❌ `bg-[#1A7F7A]` ❌ `bg-teal-700`

2. Figma-first: Before writing any component or page, read the relevant
   Figma frame via MCP. Code matches the design — design is the source of truth.

3. One PR per unit: Components → one PR each. Pages → one PR each.
   Do not batch multiple unrelated components or pages.

4. Verify against design: After generating a component or page, take a
   visual comparison (screenshot or description) against the Figma frame.
   Report any differences. Fix before submitting the PR.

5. No speculative additions: Do not add features, props, or states not in
   the approved specs. If something seems missing, ask.

---

## Step 34 — Scaffold the Next.js Frontend

### Agent actions
1. Ask the human:
   - Q1: What is the monorepo directory path for the frontend?
     (e.g., `/apps/web`, `/frontend`, `/packages/app`)
   - Q2: What is the branch naming convention?
     (e.g., `feat/[description]`, `feature/[description]`)
   - Q3: Any existing monorepo tooling to be aware of?
     (Turborepo, Nx, pnpm workspaces — if so, what's the workspace name?)

   Do NOT scaffold until Q1–Q3 are answered.

2. Scaffold the Next.js 14 App Router project at the confirmed path:

Directory structure:
```
[frontend-path]/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Root redirect
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── signup/page.tsx (if in scope)
│   ├── dashboard/page.tsx
│   └── project/
│       ├── new/page.tsx
│       └── [id]/page.tsx
├── components/
│   ├── ui/                 # Shadcn/ui base + custom atoms
│   ├── map/                # Map-specific components
│   └── layout/             # Layout shells
├── lib/
│   ├── api/                # API client functions
│   └── utils.ts
├── styles/
│   └── globals.css         # CSS custom properties from token map
├── tailwind.config.ts      # Token-keyed Tailwind config
├── tsconfig.json
└── package.json
```

3. `tailwind.config.ts` must include ALL tokens from the approved Token Map:
```typescript
// Generated from SAT Token Map — [date]
// DO NOT edit manually — update Figma Variables and regenerate
const config = {
  theme: {
    extend: {
      colors: {
        brand: {
          primary: 'var(--color-brand-primary)',
          secondary: 'var(--color-brand-secondary)',
        },
        analysis: {
          sunpath: 'var(--color-analysis-sunpath)',
          flood: 'var(--color-analysis-flood)',
          temperature: 'var(--color-analysis-temp)',
          wind: 'var(--color-analysis-wind)',
          rainfall: 'var(--color-analysis-rainfall)',
        },
        // [all other tokens]
      },
      // [spacing, radius, typography tokens]
    }
  }
}
```

4. `globals.css` must define CSS custom properties for every token:
```css
/* SAT Design Tokens — generated from Figma Variables [date] */
:root {
  --color-brand-primary: [hex from approved token];
  /* [all tokens] */
}
```

5. Submit PR:
   - Title: `feat: frontend scaffold — Next.js 14 + Tailwind + design tokens`
   - Body: list of what was scaffolded, token count, Tailwind config mapping
   - Ask human to review, approve, and merge before any component work begins.

### Gate
APPROVE STEP 34
(scaffold PR merged, human confirms project runs without errors)

---

## Step 35 — Generate Shared Components

### Agent actions
For each component in the approved Component Registry, in dependency order
(atoms first, then composed components):

1. Read the Figma component via MCP. Describe what you read before generating.
2. Generate the component at `components/[category]/[ComponentName].tsx`.

### Component file structure
```typescript
// [ComponentName].tsx
// Generated from Figma: [MCP frame link]
// Spec: [link to component spec from Phase 8]

import { type VariantProps, cva } from 'class-variance-authority';
// [other imports]

const [componentName]Variants = cva(
  // base classes using ONLY token keys
  'base-classes',
  {
    variants: {
      variant: {
        primary: 'bg-brand-primary text-white',
        // [all variants from spec]
      },
      // [other variant dimensions]
    },
    defaultVariants: { variant: 'primary' }
  }
);

interface [ComponentName]Props
  extends React.HTMLAttributes<HTMLElement>,
    VariantProps<typeof [componentName]Variants> {
  // [props from approved spec]
}

export function [ComponentName]({ variant, ...props }: [ComponentName]Props) {
  return (
    <element
      className={[componentName]Variants({ variant })}
      {...props}
    />
  );
}
```

3. After generating: compare against the Figma frame.
   Report: "Visual comparison: [what matches / what differs]."
   Fix differences before submitting PR.

4. Submit one PR per component:
   - Title: `feat(components): [ComponentName]`
   - Body: Figma MCP link, spec reference, variant list, state coverage

5. Wait for PR approval and merge before starting the next component.

Ask human: "Should I also generate Storybook stories for each component?"
If yes: generate a `[ComponentName].stories.tsx` alongside each component.

### Gate
APPROVE STEP 35
(ALL components merged; human confirms rendering correctly in dev environment)

---

## Step 36 — Generate Page-Level Screens

### Agent actions
For each Beta screen, in route order:

1. Read the Figma frame via MCP before writing any code.
2. Compose the page from approved shared components only.
   Do not create new inline components inside page files.

### Page file structure
```typescript
// [page-name]/page.tsx
// Generated from Figma: [MCP frame link]
// Implementation notes: [ref from Phase 8 Step 32]

import { [components used] } from '@/components/...';
// [other imports]

// Types for API response
interface [DataType] {
  // [from approved implementation notes]
}

export default async function [PageName]() {
  // Server component where possible
  // Client component ('use client') only if interactivity requires it
  return (
    // Layout using approved components + token-keyed Tailwind only
  );
}
```

3. Handle all 5 states: loading (Suspense/skeleton), empty, data, error, partial.
4. Wire API integration using the confirmed endpoints from Step 32.
   For [UNCONFIRMED] endpoints: use mock data and comment: `// TODO: replace mock — see GH Issue #[N]`

5. The map screen (`/project/[id]`) gets a dedicated PR and requires review
   from both Frontend Engineer AND Architecture SME.

6. Submit PR per page:
   - Title: `feat(pages): [screen name] — [route]`
   - Body: Figma MCP link, components used, API endpoints wired, states covered,
     any TODO items

### Gate
APPROVE STEP 36
(ALL page PRs merged; visual QA against Figma done; API integration confirmed)

---

## Step 37 — Responsive & Cross-Browser QA

### Agent actions
For each merged page, verify rendering at:

| Breakpoint | Target device              | Priority |
|------------|---------------------------|----------|
| 1440px     | Architect workstation      | PRIMARY  |
| 1280px     | Laptop                     | HIGH     |
| 768px      | Tablet                     | MEDIUM   |

Browsers: Chrome (primary), Firefox, Safari.

For each issue found, draft a GitHub Issue:
```
Title: Bug: [screen] — [issue description] — [breakpoint/browser]
Body:
- Screen: [name + route]
- Breakpoint: [px]
- Browser: [name + version]
- Expected: [what the Figma design shows]
- Actual: [what is rendering]
- Figma frame link: [link]
Labels: bug, frontend, priority-[blocker|major|minor]
```

Present ALL bug issues to human before creating. Ask: "Which are Beta blockers?"
Create on approval.

### Gate
APPROVE STEP 37
(all Beta-blocker bugs confirmed resolved; non-blocker issues logged as GitHub Issues)

---

## Step 38 — Frontend Complete — Monorepo Summary

### Agent actions
Draft a GitHub Issue:
```
Title: Frontend Beta Complete — [date]

## Summary
All Beta frontend screens implemented and QA'd.

## Merged PRs
| PR # | Title                | Screen(s) covered |
|------|----------------------|-------------------|
[list all]

## Screens delivered
[list with routes]

## Known deferred items
[list with GH Issue refs]

## QA status
- Responsive: [PASS / issues logged]
- Cross-browser: [PASS / issues logged]
- Token compliance: [PASS]
- Figma match: [PASS / delta notes]

## Figma file
[frozen file link]

## MCP link
[mcp link]

Labels: frontend, beta-complete
```

Ask: "Please confirm the frontend runs without errors in the dev environment
before I close Phase 9."

### Gate (Phase Gate)
APPROVE PHASE 9
(frontend confirmed running, summary issue created, QA sign-off, handoff to QA team)

---

## Phase 9 completion checklist

- [ ] Scaffold PR merged — tokens in Tailwind config (Step 34)
- [ ] All component PRs merged (Step 35)
- [ ] All page PRs merged (Step 36)
- [ ] Responsive QA complete — blockers resolved (Step 37)
- [ ] Summary GitHub Issue created (Step 38)
- [ ] Frontend confirmed running in dev environment (Step 38)
