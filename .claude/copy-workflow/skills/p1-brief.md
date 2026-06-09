# Phase 1 — Brief & Discovery
# Steps 1–4 | Intake, feature verification, audience lock, framework selection

## Phase Goal
Establish a locked brief before any copy is written. Every downstream phase depends
on the clarity of this phase. A weak brief produces weak copy — no revision cycle fixes
a misdirected asset.

---

## Step 1 — Copy Intake Brief

### Agent actions
Ask the human these four questions. One at a time if needed.

**Q1 — What are we writing?**
Present options:
- [ ] Landing page / hero section
- [ ] Cold outreach email
- [ ] Email nurture sequence (how many emails?)
- [ ] Feature announcement
- [ ] Case study
- [ ] LinkedIn / social post
- [ ] Conference pitch / talk narrative
- [ ] PDF report section
- [ ] In-app onboarding message (if yes → redirect to tech-copy workflow)
- [ ] Other: [describe]

**Q2 — What feature(s) does this copy support?**
List the features the copy is about. Agent will verify status in Step 2.

**Q3 — What is the one desired action?**
What should the reader do after reading? (Examples: "Book a pilot call", "Download the
case study", "Reply to the email", "Share the post", "Visit the landing page")

**Q4 — Any constraints?**
- Word count or length limits?
- Deadline?
- Any copy examples the human loves or hates (from SAT or competitors)?
- Any metrics or data points to include (agent will verify in Step 4)?

### Output format
```
## Copy Brief — [Asset type] — [Date]

Asset type: [from Q1]
Feature(s): [from Q2 — status TBC in Step 2]
Desired action: [from Q3]
Constraints: [from Q4]
Status: PENDING VERIFICATION
```

### Gate
APPROVE STEP 1

---

## Step 2 — Feature Status Verification

### Agent actions
For each feature named in Step 1:
1. Check status in `/Volumes/LocalDrive/Site Analysis/PROJECT_OVERVIEW.md`
2. Classify each as:
   - ✅ **Done** — backend live + source UI exists. Copy can make full claims.
   - 🔄 **Migrating** — backend live, SAT canonical FE being built. Copy can claim capability with note on timeline.
   - 📋 **Planned** — spec written, not built. Copy MUST include "Roadmap — not yet available."

3. If any feature is 📋 Planned, inform the human:
   "Feature [X] is 📋 Planned — not yet built. Copy referencing it must include a
   roadmap disclaimer. Shall I proceed with that disclaimer, or exclude this feature?"

4. Update the brief with verified statuses.

### Output format
```
## Feature Status Report

| Feature | Status | Copy Constraint |
|---|---|---|
| [feature name] | ✅ Done | Full claims permitted |
| [feature name] | 🔄 Migrating | Capability claims OK; note "in rollout" |
| [feature name] | 📋 Planned | Roadmap disclaimer required |
```

### Gate
APPROVE STEP 2

---

## Step 3 — Persona & Buying Stage Lock

### Agent actions
1. Present the three buyer archetypes and ask:
   "Who is the **primary reader** of this copy?"
   - [ ] Head of Design (veto power; fears loss of creative authorship)
   - [ ] BIM / Digital Transformation Head (writes the spec; fears lock-in)
   - [ ] Principal Architect / MD (signs the budget; fears losing clients to competitors)

2. Ask: "What buying stage are they at?"
   - [ ] Awareness — they don't know SAT exists
   - [ ] Consideration — they know SAT, evaluating fit
   - [ ] Decision — they're close to committing; need final push

3. Ask: "Is there a secondary persona who will also see this copy?"
   (Landing pages often have 2 readers. Flag if yes — copy must lead with primary,
   acknowledge secondary without losing focus.)

4. Lock the persona and buying stage. Update the brief.

### Output format
```
## Persona Lock

Primary persona: [name]
Buying stage: [Awareness / Consideration / Decision]
Secondary persona (if any): [name — handled as secondary signal only]
Copy angle: [one sentence describing what the primary persona needs to feel/believe
after reading this copy]
```

### Gate
APPROVE STEP 3

---

## Step 4 — Framework Selection & Proof Inventory

### Agent actions

**Framework selection** — propose the best framework for this asset/persona/stage combination:

| Asset type | Persona | Stage | Recommended framework |
|---|---|---|---|
| Landing page hero | Any | Awareness | AIDA |
| Cold email | Principal / Head of Design | Awareness | PAS |
| Feature announcement | BIM Head | Consideration | BAB |
| Case study | Principal | Consideration | PASTOR |
| Email nurture | Any | Consideration→Decision | Sequenced PAS |
| LinkedIn post | Head of Design | Awareness | Hook → Insight → Proof → CTA |
| Conference pitch | Principal | Awareness | Problem → Stakes → Solution → Ask |

Present the recommendation and reason. Ask if the human wants to override.

**Proof inventory** — ask:
"Do you have any of the following to include in this copy?"
- [ ] Specific metric with source (e.g., "23% lower cooling load — from [study]")
- [ ] Named firm social proof (confirmed user, or clearly framed as aspirational)
- [ ] Process comparison (time before SAT vs with SAT)
- [ ] Data source authority (IMD, NBC 2016, NREL SPA)
- [ ] Vastu bridge opportunity? (relevant for solar/wind copy in Indian residential context)

List what's confirmed. Flag missing proof with `[PROOF NEEDED]`.

### Output format
```
## Brief — FINAL (Phase 1 Complete)

Asset type: [type]
Feature(s): [list with statuses]
Primary persona: [name] | Buying stage: [stage]
Desired action: [action]
Framework: [name + reason]
Proof confirmed: [list]
Proof gaps: [PROOF NEEDED items]
Constraints: [list]
```

### Gate (Phase Gate)
APPROVE PHASE 1
(Locks the brief. No changes to persona, framework, or feature list after this gate
without restarting Phase 1.)

---

## Phase 1 Completion Checklist

- [ ] Asset type confirmed (Step 1)
- [ ] All features verified against PROJECT_OVERVIEW.md (Step 2)
- [ ] 📋 features: human confirmed disclaimer approach (Step 2)
- [ ] Primary persona and buying stage locked (Step 3)
- [ ] Framework selected and approved (Step 4)
- [ ] Proof inventory complete — gaps flagged (Step 4)
