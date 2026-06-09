# Phase 3 — Messaging Architecture
# Steps 9–12 | Value prop hierarchy, objection map, specificity audit, positioning lock

## Phase Goal
Build the structural skeleton of the copy before writing prose. Messaging architecture
defines what SAT says, in what order, with what proof. The copy developed in Phase 4
hangs on this skeleton.

This phase is required for: landing pages, email sequences, case studies, conference pitches.
It can be skipped for single-asset quick tasks (LinkedIn post, one email).

---

## Step 9 — Value Proposition Hierarchy

### Agent actions
Build a layered value prop stack for this specific asset: persona + buying stage + feature(s).

The stack has 4 levels — draft each from top to bottom:

**Level 1 — The Elevator Pitch (1 sentence)**
The single most important thing SAT does for this persona.
Format: `[Verb] [outcome] [for whom] [in what context]`
Example: "Give Indian architects solar and flood analysis data in 5 minutes, at the site selection stage."

**Level 2 — The Three Supporting Props (1 sentence each)**
Three proof-backed reasons the elevator pitch is true.
Each must: (a) be specific, (b) have a data point or source, (c) address a pain from the audience intelligence.

**Level 3 — The Objection Neutralizer (1 sentence)**
The one preemptive statement that addresses the primary objection identified in Step 7.
Example for Head of Design: "SAT presents options — every decision stays yours."
Example for BIM Head: "Every output is GeoJSON, every source is cited."

**Level 4 — The Call to Action (1 phrase)**
The single action the copy wants the reader to take.
Must be action verb + specific outcome. No generic CTAs.

### Output format
```
## Value Prop Stack — [Persona] — [Asset type]

L1 Elevator Pitch:
"[one sentence]"

L2 Supporting Props:
1. [prop] — Proof: [source or metric]
2. [prop] — Proof: [source or metric]
3. [prop] — Proof: [source or metric]

L3 Objection Neutralizer:
"[one sentence addressing primary objection]"

L4 CTA:
"[action verb + specific outcome]"
```

### Gate
APPROVE STEP 9

---

## Step 10 — Objection Map

### Agent actions
For the locked persona and buying stage, map the 3 most likely objections and their counter-messages.

Sources:
- Phase 2 audience intelligence
- buyer-personas.md — "What disqualifies copy instantly"
- competitive-landscape.md — where SAT's positioning can be attacked

For each objection:
1. State the objection as the persona would say it (their words, not marketing language)
2. Identify the root fear behind it
3. Draft the counter-message (one sentence, specific, no defensive tone)
4. Tag where in the copy this counter-message appears (headline / body / FAQ / CTA)

### Output format
```
## Objection Map — [Persona]

### Objection 1
Their words: "[how they'd say it]"
Root fear: [what they're really afraid of]
Counter-message: "[one sentence]"
Placement: [where in the copy]

### Objection 2
[same format]

### Objection 3
[same format]
```

### Gate
APPROVE STEP 10

---

## Step 11 — Specificity Audit

### Agent actions
Apply the specificity rule to every claim in the messaging stack from Steps 9–10.

For each claim, run the test:
> "Could a skeptical architect read this claim and say 'prove it'?"
If yes → it needs a specific number, source, or comparison.

**Audit table — review every claim:**

| Claim | Specific? | Fix |
|---|---|---|
| "[claim text]" | ✅ yes / ❌ no | [rewritten version with number/source] |

**Vastu bridge check:**
If the features referenced include solar (sun path) or wind analysis, AND the persona is
Principal or Head of Design, flag: "Vastu bridge opportunity — connect east/north
orientation output to Vastu spatial validation. Relevant for Indian residential developer context."
Ask human: "Deploy Vastu bridge for this asset? Y/N"

**Indian regulatory vocabulary check:**
Does the copy reference any of: NBC 2016, ECBC 2017, BBMP, BDA, FSI, FAR, Auto-DCR?
If yes → verify the specific clause or metric in competitive-landscape.md or ask for confirmation.
If a regulatory claim is unverified → flag with `[SME REVIEW REQUIRED]`.

### Output format
```
## Specificity Audit Report

| Original claim | Verdict | Revised claim (if changed) | Source |
|---|---|---|---|
| "[claim]" | ✅ | [unchanged] | [source] |
| "[claim]" | ❌ | "[specific rewrite]" | [METRIC NEEDED] |

Vastu bridge: [deploy / skip]
Regulatory flags: [list any [SME REVIEW REQUIRED] items]
```

### Gate
APPROVE STEP 11

---

## Step 12 — Positioning Statement Lock

### Agent actions
Synthesize Steps 9–11 into one locked positioning statement for this asset.

This is the creative brief a copywriter would pin above their screen before drafting.
It answers five questions in one paragraph:

1. **Who** is reading? (persona, one sentence)
2. **What problem** does this copy address? (one pain from audience intelligence)
3. **What does SAT do** about it? (L1 + L2 value props, compressed)
4. **Why SAT specifically?** (the differentiator vs Forma/TestFit/QGIS)
5. **What does the reader do next?** (the CTA)

### Output format
```
## Positioning Statement — [Asset type] — [Persona] — [Date]

This copy speaks to [persona] who [current frustration]. They are at the
[awareness / consideration / decision] stage. The copy must make them feel/believe
[desired belief state] by demonstrating [SAT capability with specific proof]. The
differentiator is [what no competitor offers]. The reader should [CTA].

Framework to apply in Phase 4: [framework name]
Key proof to use: [list top 3 proof points from Step 8]
Objection to preempt: [primary objection from Step 10]
Vastu bridge: [deploy / skip]
```

### Gate (Phase Gate)
APPROVE PHASE 3
(Positioning locked. Phase 4 copy development must not contradict the positioning statement
without reopening Phase 3.)

---

## Phase 3 Completion Checklist

- [ ] Value prop stack built and approved (Step 9)
- [ ] Objection map complete — all 3 objections addressed (Step 10)
- [ ] Specificity audit passed — no vague claims without numbers (Step 11)
- [ ] All [METRIC NEEDED] items: human decision made (source provided or placeholder accepted)
- [ ] [SME REVIEW REQUIRED] items: flagged for Architecture SME before publish
- [ ] Vastu bridge decision confirmed (Step 11)
- [ ] Positioning statement locked (Step 12)
