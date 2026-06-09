# Phase 5 — UX Flow & Information Architecture
# Steps 19–21 | Screen inventory, navigation map, user flow diagrams

## Phase goal
Define every screen SAT needs for Beta, how they connect, and the three
primary user flows. Wireframing (Phase 6) begins on a defined IA, not a
blank canvas.

---

## Step 19 — Define Screen Inventory

### Agent actions
1. Read approved requirements list (Phase 3) and user journeys (Phase 3).
2. List every screen SAT needs. Derive from requirements — do not add screens
   not in the requirements.

### Screen format
```
## Screen [N]: [Screen name]

Route: /[path]
Primary persona: [persona name]
Key actions: [list — what can the user do here]
Data displayed: [what information is shown]
Analysis module: [sunpath | flood | temperature | wind | rainfall | core | N/A]
Beta scope: [IN SCOPE | DEFERRED]
Requirement source: [REQ-IDs]
```

3. Ask: "Are there any screens you know the product needs that did not emerge
   from the requirements? If yes, which requirement would they satisfy?"

4. Add any human-provided screens with their requirement source. If the human
   cannot cite a requirement, note: `[Source: Product Owner direction — not in
   research]` — this is acceptable but must be explicit.

5. Present the screen inventory. Ask human to confirm Beta vs. Deferred scope.

### Gate
APPROVE STEP 19
(Beta scope confirmed and locked)

---

## Step 20 — Map Navigation & Information Architecture

### Agent actions
1. Create a text-based navigation map from the approved screen inventory.

### Navigation map format
```
Entry points
├── / (root → redirect to /dashboard if authed, /login if not)
├── /login
└── /signup (if applicable — ask human)

Authenticated routes
├── /dashboard (project list)
├── /project/new
├── /project/[id] (main analysis interface — map + panels)
│   ├── /project/[id]/sunpath
│   ├── /project/[id]/flood
│   ├── /project/[id]/temperature
│   ├── /project/[id]/wind
│   └── /project/[id]/rainfall
├── /settings
└── [any additional screens from Step 19]
```

Rules enforced from aec-principles.md:
- The map interface (/project/[id]) must be reachable in ONE click from
  /dashboard. Verify this is true in the map.
- No analysis result is more than two clicks from the home screen.

2. Identify for each screen:
   - Auth required: YES / NO
   - Persistent state: YES (survives navigation) / NO
   - Screen states needed: list from [loading, empty, data, error, partial]

3. Ask: "Does this navigation structure match how you expect users to move
   through the product? Any missing routes?"

4. Present the navigation map.

### Gate
APPROVE STEP 20

---

## Step 21 — Build User Flow Diagrams in Figma

### Agent actions
Build three user flow diagrams on the Screen Inventory page in Figma.

**Flow 1 — New site analysis:**
```
/dashboard (empty state)
  → "New analysis" CTA
  → /project/new
  → Drop pin on map / enter address
  → Select analysis modules to run
  → Analysis loading state (per module)
  → /project/[id] — results loaded
  → ERROR PATH: API timeout → error state with retry
  → ERROR PATH: No data for location → partial state with explanation
```

**Flow 2 — Return to saved analysis:**
```
/login (if session expired)
  → /dashboard (project list)
  → Select existing project
  → /project/[id] — last state restored
  → ERROR PATH: Project deleted → 404 with recovery action
```

**Flow 3 — Export / share analysis:**
```
/project/[id] — results loaded
  → Export / share action (ask human: where is this in the UI?)
  → Export format selection (ask human: what formats are supported in Beta?)
  → Confirmation / download trigger
  → ERROR PATH: Export fails → error state
```

For Flow 3: If the human cannot answer the export format question,
mark the flow as `[PLACEHOLDER — pending product decision]` and note the
open question. Do not invent a format.

Each flow shows: happy path (solid lines) + error paths (dashed lines).

Present flows via Figma share link (Screen Inventory page).

### Gate [SME GATE] (Phase Gate)
APPROVE PHASE 5 + SME APPROVED
(SME confirms the primary analysis flow matches architect mental model)

---

## Phase 5 completion checklist

- [ ] Screen inventory complete — Beta scope locked (Step 19)
- [ ] Navigation map approved — map is one click from dashboard (Step 20)
- [ ] Auth boundaries confirmed (Step 20)
- [ ] Three user flows in Figma — happy paths + error paths (Step 21)
- [ ] SME confirmed primary analysis flow (Step 21)
- [ ] Any open product decisions noted (export format, etc.)
