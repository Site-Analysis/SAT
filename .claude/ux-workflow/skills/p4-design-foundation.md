# Phase 4 — Design Foundation
# Steps 15–18 | Brand tokens, Figma file, component library, MCP test

## Phase goal
Build the visual and structural foundation before any screen is drawn.
The design system created here is what the Figma MCP server reads to generate
code that uses SAT's actual tokens and components.

IMPORTANT: Phases 5–9 cannot begin until the MCP connection is confirmed
working in Step 18.

---

## Step 15 — Define Brand & Visual Tokens

### Agent actions
1. Ask the human ALL of the following before generating anything:

   **Q1:** Is there any existing brand colour, logo, or visual identity for SAT?
   (If yes, ask for the values. Do not proceed until provided.)

   **Q2:** What feeling should SAT convey?
   Options to consider: Professional/technical · Modern/minimal ·
   Data-scientific · Earthy/nature-connected · Other (describe)

   **Q3:** Any competitor tool whose visual language you want to reference
   (positively or as a contrast)?

2. Based ONLY on human answers, propose the following token set.
   Do not generate until Q1–Q3 are answered.

### Token proposal format
```
## Colour tokens

| Token name              | Value     | Usage                        |
|-------------------------|-----------|------------------------------|
| color/brand/primary     | #[hex]    | CTAs, active states          |
| color/brand/secondary   | #[hex]    | Secondary actions            |
| color/neutral/bg        | #[hex]    | Page background              |
| color/neutral/surface   | #[hex]    | Panels, cards                |
| color/neutral/border    | #[hex]    | Dividers                     |
| color/text/primary      | #[hex]    | Body text                    |
| color/text/secondary    | #[hex]    | Labels, metadata             |
| color/semantic/success  | #[hex]    | Confirmation states          |
| color/semantic/warning  | #[hex]    | Risk indicators              |
| color/semantic/error    | #[hex]    | Error states                 |
| color/semantic/info     | #[hex]    | Informational                |
| color/analysis/sunpath  | #[hex]    | Sun path module              |
| color/analysis/flood    | #[hex]    | Flood risk module            |
| color/analysis/temp     | #[hex]    | Temperature module           |
| color/analysis/wind     | #[hex]    | Wind module                  |
| color/analysis/rainfall | #[hex]    | Rainfall module              |

## Typography tokens
| Token name              | Value              |
|-------------------------|--------------------|
| font/family/base        | [font name]        |
| font/family/mono        | [font name]        |
| font/size/xs ... 4xl    | [scale values]     |
| font/weight/regular     | 400                |
| font/weight/medium      | 500                |
| font/weight/bold        | 700                |

## Spacing tokens
| Token name    | Value  |
|---------------|--------|
| space/1       | 4px    |
| space/2       | 8px    |
| space/3       | 12px   |
| space/4       | 16px   |
| space/6       | 24px   |
| space/8       | 32px   |
| space/12      | 48px   |
| space/16      | 64px   |

## Radius tokens
| Token      | Value |
|------------|-------|
| radius/sm  | 4px   |
| radius/md  | 8px   |
| radius/lg  | 12px  |
```

3. Present the token proposal.

Note: Analysis module colours MUST be reviewed by the SME — colours on a
map carry professional meaning. Red for flood, orange for sun are conventions
architects expect. Confirm these are correct before finalising.

### Gate [SME GATE]
APPROVE STEP 15 + SME APPROVED
(SME confirms analysis module colours match professional conventions)

---

## Step 16 — Create Figma File & Set Up Variables

### Agent actions
1. Ask: "Please confirm your Figma account has a project or team workspace
   where I should create the SAT file. What should the file be named?"

2. Create the Figma file with this exact page structure:
   ```
   Page 1: 🗂 Cover & Changelog
   Page 2: 🎨 Design Tokens / Variables
   Page 3: 🧩 Component Library
   Page 4: 📋 Screen Inventory
   Page 5: ✏️ Wireframes — Low-fi
   Page 6: 📐 Wireframes — Mid-fi
   Page 7: ✨ UI — High-fi
   Page 8: 🔗 Prototype Flows
   Page 9: 👨‍💻 Dev Handoff Reference
   ```

3. Enter ALL approved tokens as Figma **Variables** (NOT Styles).
   Organise into variable collections:
   - Collection: Colours → groups: brand, neutral, text, semantic, analysis
   - Collection: Typography → groups: family, size, weight, line-height
   - Collection: Spacing → group: space
   - Collection: Radius → group: radius

   Naming convention: `group/subgroup/name`
   Example: `color/analysis/flood` NOT `flood-color`

4. Verify naming maps to Tailwind CSS config keys:
   `color/brand/primary` → `--color-brand-primary` → `colors.brand.primary`

5. Share the Figma file with: Product Owner, Frontend Engineer, SME.
   Ask human to confirm sharing is complete.

### Gate
APPROVE STEP 16
(human confirms file created, Variables populated, file shared)

---

## Step 17 — Build Core Component Library

### Agent actions
1. Ask the human: "Which icon library will SAT use?"
   Options: Lucide (recommended — already in shadcn/ui) · Heroicons · Custom
   Do NOT proceed until answered.

2. Build the following components in Figma, using ONLY Variables — no hardcoded
   values anywhere:

**Atoms:**
- Button: primary, secondary, ghost, danger — states: default, hover, focus,
  disabled, loading
- Input: default, focus, error, disabled
- Badge/Tag: default, success, warning, error
- Toggle: on, off, disabled
- Tooltip: default
- Icon: document the icon library choice and scale

**Map-specific (critical — SME must review):**
- Layer toggle control: on/off states + loading state
- Analysis score card: title, score value, severity colour, sub-scores (collapsible)
- Risk indicator: colour-coded band (maps to analysis token colours)
- Map pin/marker: default, selected, loading

**Layout shells:**
- Top navigation bar: logo zone, nav items, user zone
- Side panel: expanded, collapsed states
- Map canvas wrapper: with layer control overlay position
- Analysis dashboard panel: header, content, empty, loading states

Rules:
- Every fill, stroke, and text colour references a Variable.
- Every component uses Auto Layout.
- All states are separate variants in a single component.
- No detached instances.

3. Present the component library (share Figma page link).

### Gate [SME GATE]
APPROVE STEP 17 + SME APPROVED
(SME reviews map-specific and analysis components for professional accuracy)

---

## Step 18 — Connect Figma MCP — Test Read

### Agent actions
1. Ask the human: "Has Claude Code been installed and configured with the
   Figma MCP server? The remote server URL is: https://mcp.figma.com/mcp
   Please confirm this is set up before I attempt a test read."

2. Once confirmed, run a test read:
   - Read the Figma file variables (token list)
   - Read one component from the library (e.g., the Button component)
   - Report back: what the agent read, including component structure,
     variant names, and variable bindings

3. If the test read fails:
   - Report the exact error
   - Diagnostic checklist:
     - [ ] Is Claude Code running?
     - [ ] Is the Figma MCP server listed in `/mcp`?
     - [ ] Does the Figma file have the correct share permissions?
     - [ ] Is the user authenticated in Figma?
   - Do NOT proceed past Step 18 until the test read succeeds.

4. If the test read succeeds:
   - Document the Figma file MCP link
   - Confirm: "MCP connection working. Can read [N] variables and [N]
     components. Proceeding to Phase 5 is unblocked."

### Gate (Phase Gate)
APPROVE PHASE 4
(requires: token set approved, Figma file created, component library approved,
MCP test read successful, human confirms all of the above)

---

## Phase 4 completion checklist

- [ ] Token set approved by PO + SME (Step 15)
- [ ] Figma file created with correct page structure (Step 16)
- [ ] Variables populated and named correctly (Step 16)
- [ ] File shared with team (Step 16)
- [ ] Component library built — all atoms + map + layout shells (Step 17)
- [ ] All components token-bound (no hardcoded values) (Step 17)
- [ ] MCP test read successful — result documented (Step 18)
