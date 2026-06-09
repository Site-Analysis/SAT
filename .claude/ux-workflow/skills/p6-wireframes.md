# Phase 6 — Wireframing
# Steps 22–25 | Low-fi → Mid-fi → High-fi → pushed to Figma via MCP

## Phase goal
Produce approved, token-compliant high-fidelity designs for every Beta screen.
Push to Figma as the single source of truth. Every screen is human-described
first — the agent never invents a layout.

## Model: Human-describes → Agent-generates → Human-approves → Repeat

The agent generates ONE screen at a time. Never batch screens.
If the human's description is ambiguous, ask ONE clarifying question. Do not guess.

---

## Step 22 — Low-Fidelity Wireframes

### Agent actions
For each screen in the Beta inventory (from Step 19), in priority order:

1. Ask the human: "For [screen name]: where should the main elements sit?
   Describe or sketch the rough layout. (A photo of a paper sketch is fine.)"

2. Wait for the human's description. Do not generate until received.

3. Generate a low-fidelity wireframe as a Claude Artifact (HTML):
   - Boxes and labels ONLY
   - No colour (grey boxes, black text)
   - No real icons
   - No final copy
   - Label each box with its function

4. Present the wireframe. Ask: "Is this the layout you had in mind?
   What should change?"

5. Revise until the human is satisfied with the layout structure.
   The layout structure is what matters here — not the visual design.

6. Mark the screen: `LO-FI APPROVED — [screen name]`

7. Repeat for the next screen. Do not move to Step 23 until ALL Beta screens
   have an approved low-fi wireframe.

### Note on the map screen
The main analysis screen (/project/[id]) is the most complex.
Prompt the human specifically: "For the map screen, describe:
(a) where the map sits, (b) where the layer controls are,
(c) where the analysis panel is, (d) how the user toggles between modules."
These four elements define the entire layout — do not generate without them.

### Gate
APPROVE STEP 22
(ALL Beta screens have individually approved lo-fi wireframes)

---

## Step 23 — Mid-Fidelity Wireframes

### Agent actions
For each approved lo-fi wireframe, refine to mid-fidelity:

What to add (vs lo-fi):
- Real navigation elements (based on Step 20 nav map)
- Real SAT content placeholders — NOT Lorem Ipsum:
  - Use: "Sun Path Analysis", "Flood Risk Score: HIGH", "Site: Koramangala"
  - NOT: "Lorem ipsum", "Module 1", "Score: 85"
- Real spacing proportions (from space token scale)
- Interaction hints: label what each control does on interaction
  (e.g., "clicking this toggle shows/hides the flood overlay")
- All 5 states visible on one frame or as linked frames:
  loading · empty · data · error · partial

Generation: Claude Artifact (HTML), one screen at a time.
Present immediately. Revise on feedback.

SME review required for all analysis screens before approval.
Ask: "Please share this with the Architecture SME before approving."

### Gate
APPROVE STEP 23
(ALL Beta screens have approved mid-fi wireframes + SME reviewed analysis screens)

---

## Step 24 — High-Fidelity Mockups

### Agent actions
For each approved mid-fi wireframe, apply the SAT design system to produce
a high-fidelity mockup.

Before generating each screen:
- Ask: "For [screen name], any specific visual direction? E.g., 'make the
  flood panel feel urgent but not alarming', 'the map should feel like a
  professional tool, not a consumer app'."
- If no direction given: proceed with design system defaults.

Generate TWO variants per screen:
- Variant A: Agent's primary interpretation
- Variant B: Alternative layout or visual treatment (not just a colour change —
  a meaningful structural or hierarchy difference)

Apply throughout (from aec-principles.md):
- Map dominant — analysis panels never obscure more than 30% of map
- Information dense — no decorative whitespace
- Colour encodes meaning only — no decorative colour use

Reference only approved token names in the generated output.
Do not use hardcoded hex values.

After each screen: present both variants. Ask: "Which do you prefer, or
what hybrid would you like?"

Record the human's choice. Mark: `HI-FI APPROVED — [screen name] — Variant [A/B/hybrid]`

SME must review all map-adjacent screens.

### Gate
APPROVE STEP 24
(ALL Beta screens have approved hi-fi mockups with variant choice recorded)

---

## Step 25 — Push High-Fidelity Designs to Figma via MCP

### Agent actions
Using the confirmed Figma MCP connection from Step 18:

1. Push each approved hi-fi design to the Figma file → UI (High-fi) page.

For each pushed frame, verify:
- [ ] Uses Figma component instances (not flat shapes)
- [ ] All fills reference Variables (right-click → shows variable name, not hex)
- [ ] Auto Layout applied for responsive behaviour
- [ ] Frame named clearly: `[Screen] / [Module] / [State]`
  Example: `Map / Flood Active / Data`

2. After pushing ALL screens, run a QA pass:
   - List every frame pushed
   - For each: confirm variable bindings intact or report broken bindings
   - Fix broken bindings before presenting to human

3. Present: Figma share link to the UI (High-fi) page.
   Ask: "Please review the Figma designs and confirm they match the approved
   mockups and that all token bindings appear correct."

If any binding is broken, report it, fix it, re-confirm before gate.

### Gate (Phase Gate)
APPROVE PHASE 6
(ALL screens pushed to Figma, ALL variable bindings confirmed, PO sign-off)

---

## Phase 6 completion checklist

- [ ] Lo-fi wireframes for all Beta screens approved (Step 22)
- [ ] Mid-fi wireframes approved + SME reviewed analysis screens (Step 23)
- [ ] Hi-fi mockups approved — variant choices recorded (Step 24)
- [ ] All screens pushed to Figma (Step 25)
- [ ] Variable bindings QA-verified (Step 25)
- [ ] Figma UI page link confirmed by human
