# Phase 3 — Personas & Requirements
# Steps 11–14 | Research-grounded personas, journeys, requirements, GitHub Issues

## Phase goal
Convert approved insights into personas, journey maps, and a fully traceable
requirements list. Nothing in this phase is invented — every claim cites a
source from Phase 2.

---

## Step 11 — Create Personas

### Agent actions
1. Read approved affinity map and insight report.
2. Propose 2–3 personas based ONLY on research patterns — not assumptions.

### Persona format (strict)
```
## Persona [N]: [Name] — [Role]

Research basis: [list of cluster IDs that define this persona type]

| Attribute        | Value                                      | Source            |
|------------------|--------------------------------------------|-------------------|
| Experience level | [range]                                    | [cluster/obs IDs] |
| Primary goal     | [what they want to achieve]                | [cluster/obs IDs] |
| Current tools    | [tools mentioned in transcripts]           | [participant IDs] |
| Key frustration  | [top pain point]                           | [cluster ID]      |

Behaviours (research-backed):
- [behaviour 1] — Source: [OBS-IDs]
- [behaviour 2] — Source: [OBS-IDs]
- [behaviour 3] — Source: [OBS-IDs]

Pain points (research-backed):
- [pain point 1] — Source: [cluster ID]
- [pain point 2] — Source: [cluster ID]
- [pain point 3] — Source: [cluster ID]

"I want SAT to..." — [verbatim quote or closest composite from transcripts]

Fabrication flag: [list any attribute that is INFERRED, not directly observed]
```

3. Clearly mark inferred attributes. Do not hide them.
4. Present all personas. Show the gate.

### Gate [SME GATE]
APPROVE STEP 11 + SME APPROVED
(SME confirms personas reflect real professional types in Indian AEC)

---

## Step 12 — Map User Journeys

### Agent actions
For each approved persona, create two journey maps:

**Current state (pre-SAT):**
```
Trigger → [what starts the site analysis need]
  ↓
Step 1: [action] | Tool: [tool] | Pain: [pain point, cite cluster]
  ↓
Step 2: [action] | Tool: [tool] | Pain: [pain point, cite cluster]
  ↓
[continue until output]
  ↓
Output: [what the architect produces]
Time estimate: [from transcripts, cite participant]
```

**SAT-assisted state:**
```
Trigger → [same trigger]
  ↓
Step 1: [action in SAT] | SAT feature: [module]
  ↓
[continue]
  ↓
Output: [what they produce]
Time saved: [estimate based on current-state comparison]
```

Rules:
- Only include steps mentioned in transcripts or confirmed by SME.
- If a step is assumed, mark it `[ASSUMED — not in transcripts]`.
- The SME validates the current-state journey — it must reflect real practice.

### Gate [SME GATE]
APPROVE STEP 12 + SME APPROVED

---

## Step 13 — Define Functional Requirements

### Agent actions
1. Derive requirements from approved journey maps and pain points ONLY.
2. For each requirement, cite the source.

### Requirement format
```
REQ-[N] | [Type] | [Priority: TBD] | Source: [cluster/journey step]

Requirement: [what the system must do / user must be able to do]
Acceptance criteria: [how we know it is met — specific and testable]
AEC note: [any Indian standard or professional convention that applies]
```

Types: `FUNCTIONAL` `USER` `AEC-SPECIFIC`

AEC-specific requirements must be confirmed by SME before listing.

3. Present the full list. Ask: "Is any requirement here not traceable to
   the approved research? If so, which one and what is its source?"

### Gate [SME GATE]
APPROVE STEP 13 + SME APPROVED
(AEC-specific requirements confirmed by SME)

---

## Step 14 — Prioritise Requirements & Create GitHub Issues

### Agent actions
1. Apply MoSCoW prioritisation to each requirement:
   - Must-have: Beta is broken without this
   - Should-have: Important but Beta can ship without it
   - Could-have: Nice to have, low effort
   - Won't-have (Beta): Explicitly deferred

2. Ask the human:
   - "Are there requirements that are technically blocked for Beta?"
   - "Any MoSCoW assignments you want to override?"

3. Update priorities based on human input.

4. Draft GitHub Issues — one per requirement:
```
Title: UX Requirement: [requirement label]

Body:
## Requirement
[requirement text]

## Acceptance criteria
[testable criteria]

## Priority
[Must / Should / Could / Won't — Beta]

## Source
- Research cluster: [ID]
- Journey step: [persona + step]

## AEC note
[applicable standard, if any]

Labels: ux-requirement, [must-have|should-have|could-have|deferred],
        [sunpath|flood|temperature|wind|rainfall|core] (whichever applies)
```

5. Present ALL drafts before creating. Ask for final changes.
6. Create on approval. Ask human to confirm issues visible in GitHub.

### Gate (Phase Gate)
APPROVE PHASE 3
(all issues created, human confirms visible in GitHub, PO sign-off)

---

## Phase 3 completion checklist

- [ ] 2–3 personas approved by PO + SME (Step 11)
- [ ] Current-state and SAT-assisted journey maps approved (Step 12)
- [ ] Requirements list approved and traceable (Step 13)
- [ ] MoSCoW priorities confirmed with human input (Step 14)
- [ ] All requirement GitHub Issues created (Step 14)
- [ ] Beta scope locked: Must-have list finalised
