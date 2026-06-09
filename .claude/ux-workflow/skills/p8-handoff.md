# Phase 8 — Design-to-Code Handoff
# Steps 30–33 | Token map, component specs, screen notes, Dev Handoff page

## Phase goal
Extract everything a developer needs from the frozen Figma file — without
interpretation. The Frontend Engineer should be able to implement Phase 9
using only the outputs of this phase.

## How the Figma MCP handoff works
```
Frozen Figma file
  → Figma MCP server reads: Variables, components, Auto Layout, layer hierarchy
  → Claude Code receives structured design representation
  → Agent generates code referencing SAT token names (not hardcoded values)
  → Code uses actual Figma component structure as source of truth
```

---

## Step 30 — Extract Token Map & Component Registry

### Agent actions
Via Figma MCP, read the frozen file and produce:

**Token Map:**
```
## SAT Token Map — [date]

| Figma Variable name      | CSS custom property       | Tailwind config key         |
|--------------------------|---------------------------|-----------------------------|
| color/brand/primary      | --color-brand-primary     | colors.brand.primary        |
| color/brand/secondary    | --color-brand-secondary   | colors.brand.secondary      |
| color/analysis/flood     | --color-analysis-flood    | colors.analysis.flood       |
| [... all tokens]         |                           |                             |
```

**Component Registry:**
```
## SAT Component Registry — [date]

### [Component name]
Figma path: [Component Library / Group / Component]
Variants: [list all variant properties and values]
Props (inferred): [prop name: type — based on variants]
Usage notes: [when to use this component]
MCP frame link: [direct link]
```

Present both to the human and Frontend Engineer.
Ask: "Do the CSS variable names and Tailwind keys match the config you plan
to use? Any naming adjustments needed before code generation begins?"

Update the Token Map based on Frontend Engineer input.

### Gate
APPROVE STEP 30
(Frontend Engineer explicitly approves the Token Map naming)

---

## Step 31 — Generate Component Specifications

### Agent actions
For each component in the approved Component Registry, read it via Figma MCP
and generate a component specification:

```
## Component: [Name]

### TypeScript props interface
```typescript
interface [ComponentName]Props {
  variant: '[variant1]' | '[variant2]' | ...;
  size?: '[size1]' | '[size2]' | ...;
  state?: 'default' | 'hover' | 'focus' | 'disabled' | 'loading' | 'error';
  // [additional props from Figma variants]
  children?: React.ReactNode;
  onClick?: () => void;
  className?: string;
}
```

### Visual states
| State    | Description                              | Figma variant        |
|----------|------------------------------------------|----------------------|
| default  | [description]                            | [Figma variant name] |
| hover    | [description]                            | [Figma variant name] |
| focus    | [description + focus ring spec]          | [Figma variant name] |
| disabled | [description]                            | [Figma variant name] |
| loading  | [description + loading indicator spec]   | [Figma variant name] |
| error    | [description]                            | [Figma variant name] |

### Responsive behaviour
[Description from Auto Layout properties read via MCP]

### Accessibility
- ARIA role: [role]
- ARIA label: [label pattern]
- Keyboard: [keyboard interactions required]
- Focus visible: [yes — uses focus ring from token]

### Token references
- Background: [token name]
- Text: [token name]
- Border: [token name]
- [any other token references]

### Figma MCP link
[direct link to component in Figma]
```

Flag: any component that requires animation. Specify:
- Property being animated
- Duration: [value from token if defined, or ask human]
- Easing: [value or ask human]

Present all component specs. Ask Frontend Engineer: "Flag any spec that is
technically ambiguous or requires a library not in the current stack."

### Gate
APPROVE STEP 31
(Frontend Engineer approves all component specs)

---

## Step 32 — Generate Screen Implementation Notes

### Agent actions
For each Beta screen, generate implementation notes:

```
## Screen: [Name] — [Route]

### Components used
- [Component name] — [usage context]
- [Component name] — [usage context]

### Data dependencies
| Data | Source API endpoint | Method | Response shape (key fields) |
|------|---------------------|--------|----------------------------|
| [data name] | /api/[endpoint] | GET | { field: type, ... } |

Note: API endpoint references must be confirmed with the Backend Engineer.
Mark unconfirmed endpoints as `[UNCONFIRMED — pending BE confirmation]`.

### State management
- Global state (Zustand): [what is stored globally and why]
- Local state (useState): [what is local and why]

### Screen states
| State   | Trigger                        | UI behaviour                |
|---------|--------------------------------|------------------------------|
| loading | [trigger condition]            | [skeleton / spinner spec]    |
| empty   | [trigger condition]            | [empty state content]        |
| data    | [trigger condition]            | [normal populated state]     |
| error   | [trigger condition]            | [error message + action]     |
| partial | [trigger condition]            | [partial load behaviour]     |

### Responsive notes
- 1440px: [layout description]
- 1280px: [any layout changes]
- 768px: [any layout changes]

### Geospatial-specific notes (map screen only)
- Leaflet layer order: [base → overlays in order]
- Analysis overlay rendering: [how each module's data is visualised on map]
- Layer toggle behaviour: [toggle on/off cycle, loading state per layer]
```

Before finalising API endpoint references:
Ask the Backend Engineer: "Please confirm these endpoints exist and the
response shapes are correct: [list]."

Mark confirmed endpoints: `[CONFIRMED — [BE name]]`
Mark unconfirmed: `[UNCONFIRMED — open question]`

Do NOT generate page code for a screen with unconfirmed API endpoints
unless the human explicitly says to proceed with mock data.

### Gate
APPROVE STEP 32
(Frontend Engineer and Backend Engineer both approve — all [UNCONFIRMED]
items either resolved or explicitly deferred with mock data decision)

---

## Step 33 — Create Dev Handoff Page in Figma

### Agent actions
On the Dev Handoff Reference page (Page 9) in Figma, build:

**Section 1 — Token Reference**
Table: Figma Variable name | CSS var | Tailwind key | Example usage

**Section 2 — Component Registry**
Table: Component name | Figma path | Props summary | MCP link

**Section 3 — Screen Directory**
Table: Screen name | Route | Figma frame link | Key components | API endpoints

**Section 4 — Implementation Notes**
Link to approved implementation notes doc (or embed key sections)

**Section 5 — Open Questions**
List any items marked [UNCONFIRMED] or [PLACEHOLDER] from earlier phases

Enable Figma Dev Mode on the file.
Ask human: "Please confirm Dev Mode is enabled and accessible to the
Frontend Engineer."

### Gate (Phase Gate)
APPROVE PHASE 8
(Frontend Engineer confirms Dev Handoff page is complete and Dev Mode accessible)

---

## Phase 8 completion checklist

- [ ] Token Map approved by Frontend Engineer (Step 30)
- [ ] Component Registry complete (Step 30)
- [ ] All component specs approved by Frontend Engineer (Step 31)
- [ ] API endpoints confirmed by Backend Engineer (Step 32)
- [ ] Screen implementation notes approved (Step 32)
- [ ] Dev Handoff page built in Figma (Step 33)
- [ ] Dev Mode enabled and confirmed (Step 33)
- [ ] All [UNCONFIRMED] and [PLACEHOLDER] items logged and tracked
