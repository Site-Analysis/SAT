# Phase 2 — Synthesis & Insights
# Steps 7–10 | Affinity mapping, pattern identification, GitHub Issues

## Phase goal
Turn all approved transcripts into structured, human-reviewed insights and
GitHub Issues that become the factual foundation for all design decisions.
No design begins until this phase is fully approved.

---

## Step 7 — Extract Atomic Observations

### Agent actions
1. Read all approved transcripts.
2. Extract atomic observations — one idea per observation, no synthesis yet.

### Observation format (strict)
```
OBS-[N] | P[participant#] | [timestamp] | [topic-tag] | [observation text]
```

Topic tags: `workflow` `tools` `pain-point` `data` `collaboration` `ideal-tool`

Rules:
- Observations are NEUTRAL statements of fact, not interpretations.
  ✅ "P3 opened 3 browser tabs when looking up zoning rules [00:14:22]"
  ❌ "P3 finds zoning rules hard to find"
- One idea per observation. Split compound ideas.
- Minimum 8 observations per transcript. If fewer, re-read.
- Include verbatim quote in observations where the participant said something
  memorable. Mark with `[QUOTE]`.

3. Present the full observation list.
4. Ask: "Are there observations you believe I missed or that misrepresent
   what was said?"
5. Revise based on feedback. Re-present. Show the gate.

### Gate
APPROVE STEP 7

---

## Step 8 — Affinity Mapping

### Agent actions
1. Group observations from Step 7 by affinity.
2. Propose 8–12 clusters. Each cluster must:
   - Appear in observations from ≥3 participants
   - Have a label describing a BEHAVIOUR or PROBLEM (not a solution)
   - List all supporting observation IDs

### Cluster format
```
## CLUSTER [N]: [Label — behaviour/problem description]
Participants: [P1, P3, P5, ...]
Observations: [OBS-12, OBS-34, OBS-67, ...]
Summary: [1 sentence — what these observations have in common]
```

### SAT-specific clusters to watch for
Flag these if they emerge (they likely will based on domain knowledge):
- Manual data collection time
- Tool-switching friction
- Regulatory data lookup difficulty
- Site visit necessity (things only discoverable in person)
- Client presentation of analysis
- 'Intangibles' — light, neighbourhood vibe, views

3. Present clusters. Ask: "Do the observations in each cluster actually belong
   together? Do any labels describe a solution rather than a problem?"
4. Revise (split / merge / relabel) based on feedback. Re-present.

### Gate
APPROVE STEP 8

---

## Step 9 — Pain Point & Insight Report

### Agent actions
For each approved cluster, generate:

```
## Pain Point: [Cluster label]
Frequency: [N of N participants]
Severity: [BLOCKER | MAJOR FRICTION | MINOR ANNOYANCE]
Summary: [2–3 sentences — what the problem is and why it matters]

Supporting quotes:
> "[verbatim quote]" — P[N], [timestamp]
> "[verbatim quote]" — P[N], [timestamp]

SAT coverage:
- Currently addressed by: [module name, or "Not addressed"]
- Design opportunity: [direction — not a solution]
```

Then add a final section:
```
## SAT Opportunity Map

| Pain Point          | Addressed by SAT? | Beta scope? |
|---------------------|-------------------|-------------|
| [cluster label]     | Yes — [module]    | [Y/N]       |
...
```

Ask the human to confirm: "Which opportunity areas are in scope for Beta
vs. post-Beta roadmap?"

Present the report. Show the gate.

### Gate [SME GATE]
APPROVE STEP 9 + SME APPROVED
(SME confirms severity assessments are professionally accurate)

---

## Step 10 — Create GitHub Issues from Insights

### Agent actions
1. For each pain point with a design implication, draft a GitHub Issue:

```
Title: UX Insight: [pain point label]

Body:
## Summary
[pain point summary]

## Evidence
- Frequency: [N/N participants]
- Severity: [BLOCKER | MAJOR | MINOR]
- Supporting quotes: [2 quotes with participant IDs]

## Design direction
[one-sentence direction — not a solution]

## Source
- Cluster: [cluster label]
- Observations: [OBS-IDs]
- Transcripts: [participant IDs]

Labels: ux-research, insight, [severity-tag]
```

2. Also draft a summary issue:
   - Title: `UX Research Synthesis Complete — [date]`
   - Body: links to all insight issues + Phase 2 completion note
   - Labels: `ux-research`, `phase-2`, `do-not-close`

3. Present ALL draft issues to the human before creating any.
   Ask: "Any issues to add, remove, or modify?"

4. On approval: create issues in GitHub. Ask human to paste the URL of the
   summary issue to confirm.

### Gate (Phase Gate)
APPROVE PHASE 2
(requires: all issues created, summary issue URL confirmed, PO sign-off)

---

## Phase 2 completion checklist

- [ ] Observation list approved (Step 7)
- [ ] Affinity map approved — 8–12 clusters (Step 8)
- [ ] Pain point report approved by PO + SME (Step 9)
- [ ] Beta vs. post-Beta scope confirmed (Step 9)
- [ ] All GitHub Issues created and confirmed (Step 10)
- [ ] Summary issue URL logged
