# Phase 7 — UI Finalisation
# Steps 26–29 | Consistency audit, fixes, prototype, design freeze

## Phase goal
Polish the Figma file to production quality, build a testable prototype,
and declare design freeze. After Step 29, no Figma change is made without
a GitHub Issue reference.

---

## Step 26 — Design Consistency Audit

### Agent actions
Read the full Figma file via MCP. Check for:

| Check                    | Pass criteria                                      |
|--------------------------|----------------------------------------------------|
| Spacing                  | All spacing is on the token scale (space/1–16)     |
| Colour bindings          | Zero raw hex values — all reference Variables      |
| Component instances      | No detached instances — all link to library        |
| State coverage           | All 5 states present per screen                    |
| Frame naming             | Follows `Screen / Module / State` convention       |
| Typography               | All text references typography token Variables     |
| Analysis colours         | All use `color/analysis/[module]` tokens           |

### Audit report format
```
## Figma Consistency Audit — [date]

### Issues found: [N]

| # | Figma layer path                 | Issue type       | Fix needed              |
|---|----------------------------------|------------------|-------------------------|
| 1 | Map/Flood Active/Data → Panel BG | Raw hex #1A7F7A  | Bind to color/brand/... |
| 2 | Dashboard/Empty → Heading        | Detached text    | Re-link typography token|
...

### No issues:
[List of pages/frames that passed all checks]
```

Present the audit report. Ask: "Which issues are Beta blockers?
Which are acceptable debt?"

### Gate
APPROVE STEP 26
(human has categorised all issues as blocker or acceptable debt)

---

## Step 27 — Apply Audit Fixes

### Agent actions
1. Fix ALL blocker issues via Figma MCP write operations.
2. For each fix, report: layer path, what was changed, what it is now.

After all fixes, run a delta audit:
- Re-read the affected frames via MCP
- Confirm ONLY the targeted bindings changed
- Report: "N fixes applied. Delta audit: no unintended changes detected."
  OR: "Delta audit found [N] unintended changes: [list]. Reverting..."

If a fix cannot be applied via MCP, report it to the human with the exact
Figma layer path and required manual fix. Do not skip it.

Present post-fix state.

### Gate
APPROVE STEP 27
(human confirms all blockers resolved; unintended changes confirmed absent)

---

## Step 28 — Build Prototype Flows

### Agent actions
Wire the three approved user flows (from Step 21) as interactive Figma prototypes.

For each flow:
- Connect frames with transitions (standard: dissolve 200ms unless human specifies)
- Set interaction triggers (tap/click)
- Add overlay interactions for:
  - Map tooltips (hover/tap on map element)
  - Analysis score card expansion (tap sub-score to expand)
  - Layer toggle feedback (tap toggle → immediate visual state change)

Prototype quality check:
- Walk through each flow yourself via MCP read
- Verify every CTA has a connection
- Verify every error path is reachable
- Verify no dead-end frames (frames with no forward or back navigation)

Share the prototype link. Ask: "Please walk through each flow as if you
are a first-time user. Note any broken links, confusing transitions, or
missing interactions."

Architecture SME must also walk through the primary analysis flow.

### Gate [SME GATE]
APPROVE STEP 28 + SME APPROVED

---

## Step 29 — Design Freeze Declaration

### Agent actions
1. Generate the Design Freeze document:

```
# SAT Design Freeze — [date]

## Scope
Beta frontend — [N] screens in scope.

## Figma file
File name: [name]
File URL: [url]
UI page: [direct link]
MCP link: [mcp frame link]

## Version
Token version: [date of last token change]
Component library version: [date of last component change]
Frozen by: [Product Owner name]

## Screens in scope
| Screen name | Figma frame path | Route |
|-------------|-----------------|-------|
[list all]

## Known deferred items
[List anything explicitly not in scope for Beta with reason]

## Change protocol (post-freeze)
ALL changes to this Figma file after this date require:
1. A GitHub Issue opened FIRST
2. Issue approved by Product Owner
3. Agent references the issue number when making the change
No exceptions.
```

2. Draft GitHub Issue:
   - Title: `Design Freeze — [date] — Beta Frontend`
   - Body: paste the freeze document
   - Labels: `design-freeze`, `beta`, `do-not-modify-without-pm-approval`

3. Ask human to create the issue and paste the URL.

4. After the URL is confirmed, brief the team: "Design is frozen. Phase 8
   (handoff) and Phase 9 (code generation) can now begin."

### Gate (Phase Gate)
APPROVE PHASE 7
(freeze document confirmed, GitHub Issue URL provided, PO explicit sign-off)

---

## Phase 7 completion checklist

- [ ] Consistency audit complete — all blockers categorised (Step 26)
- [ ] All blocker fixes applied and delta-audited (Step 27)
- [ ] Prototype flows built — all three flows, no dead ends (Step 28)
- [ ] SME approved primary analysis flow (Step 28)
- [ ] Design Freeze GitHub Issue created and URL logged (Step 29)
- [ ] Post-freeze change protocol acknowledged by team
