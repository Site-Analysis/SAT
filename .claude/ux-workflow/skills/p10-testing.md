# Phase 10 — Testing & Iteration
# Steps 39–42 | Usability testing, bug triage, design iteration, Beta readiness

## Phase goal
Validate the frontend with real users, resolve priority issues, and get
explicit go/no-go sign-off for Beta launch.

---

## Step 39 — Usability Testing Setup

### Agent actions
1. Define 3–5 test tasks based on the primary user flows from Phase 5.

### Task format
```
## Usability Test — Task [N]

Scenario: "[User-context sentence — what situation the participant is in]"
Task: "[Specific action to perform — no hints, no tool mentions]"
Success criteria: "[What the participant does that counts as task completion]"
Failure criteria: "[What counts as failure]"
User flow reference: [Flow 1/2/3 from Step 21]
```

Example:
```
Scenario: "You have a plot in Koramangala, Bangalore."
Task: "Find out the flood risk for this site."
Success: Participant reaches /project/[id] with flood module active and reads the score.
Failure: Participant cannot find the flood module or gives up.
```

2. Ask the human:
   - Q1: "Are the test tasks realistic and unambiguous for a practising architect?"
   - Q2: "Same remote setup as Phase 1 (Google Meet/Zoom + recording consent)?"
   - Q3: "How many participants? (Recommended: 5 — same pool if possible)"

3. SME reviews test tasks — confirms they reflect real professional scenarios.

4. Generate the moderator guide (same format as Phase 1 interview guide).

### Gate [SME GATE]
APPROVE STEP 39 + SME APPROVED

---

## Step 40 — Conduct & Synthesise Usability Tests

### Agent actions
Same transcription process as Phase 1 (Step 5).

After all sessions, generate the Usability Test Report:

```
## Usability Test Report — [date]
Participants: [N]
Tasks tested: [N]

### Results by task

#### Task [N]: [task name]
| Participant | Outcome           | Time-on-task | Notes                  |
|-------------|-------------------|--------------|------------------------|
| P1          | Completed         | [time]       | [observation]          |
| P2          | Completed with difficulty | [time] | [where they struggled] |
| P3          | Failed            | [time]       | [where they stopped]   |

Completion rate: [N/N]
Top confusion moment: [description + timestamp]

### Top 5 usability issues

| # | Issue description                | Frequency  | Severity   | Affected screen |
|---|----------------------------------|------------|------------|-----------------|
| 1 | [description]                    | [N/N users] | [B/M/m]   | [screen name]   |
...

Severity: B = Blocker | M = Major | m = Minor
```

Map each issue to the relevant Figma frame and GitHub Issue (create new if none exists).

### Gate
APPROVE STEP 40
(human confirms issue priority list — which are Beta blockers)

---

## Step 41 — Design Iteration

### Agent actions
For each approved usability issue:

1. Check: does a GitHub Issue exist for this?
   - If yes: reference it.
   - If no: draft and create one before making any change.

2. Propose a specific design change — not a direction, a concrete change:
   ✅ "Move the layer toggle controls from the bottom panel to the left
       sidebar, above the analysis module list. Figma: [layer path]."
   ❌ "Make the layer controls more visible."

3. Show the proposed change to the human. Wait for approval before
   implementing in Figma.

4. Implement in Figma (referencing the GitHub Issue number).

5. After Figma change: regenerate the affected frontend code using the
   Phase 9 process (MCP read → code → PR referencing the issue).

6. Submit PR: `fix(ux): [issue description] — GH#[issue number]`

7. Close the usability issue only when BOTH:
   - The Figma change is confirmed by the human
   - The code PR is merged and confirmed rendering correctly

Repeat for each approved issue.

### Gate
APPROVE STEP 41
(all approved usability issues have closed GitHub Issues and merged PRs)

---

## Step 42 — Re-Test & Beta Readiness Sign-Off

### Agent actions
1. Re-run the same 3–5 test tasks with 5 participants (new set recommended
   for unbiased results).

2. Generate a comparative results table:
```
## Usability Test — Round 2 Comparison

| Task | Round 1 completion | Round 2 completion | Delta |
|------|-------------------|-------------------|-------|
| [N]  | [N/N]             | [N/N]             | [+/-] |

### Resolved issues (confirmed fixed)
- [Issue N]: [description] — Round 1: [result] → Round 2: [result]

### Remaining issues
- [Issue N]: [description] — still present, severity: [updated assessment]
```

3. Generate the Beta Readiness Report:
```
# SAT Beta Readiness Report — [date]

## Summary
[1–2 sentence assessment: is the product ready for Beta?]

## What is ready
[list confirmed working features]

## What is deferred
[list with GitHub Issue refs — explicitly out of scope for Beta]

## Known risks
[list of anything that might cause issues in Beta with mitigation]

## Recommendation
[GO — ready for Beta launch]
OR
[NO-GO — [specific blockers that must resolve first]]
```

4. Draft final GitHub Issue:
   - Title: `Beta Readiness Sign-Off — [date]`
   - Body: paste Beta Readiness Report
   - Labels: `beta-readiness`, `go` or `no-go`

5. Ask: "Please make the explicit go/no-go decision. Type GO or NO-GO."
   - GO: approve the issue, hand off to DevOps Engineer for deployment.
   - NO-GO: identify blockers, return to Step 41 for those items only.

The workflow is complete ONLY when the human types GO and the Beta Readiness
Issue is confirmed created.

### Gate (Phase Gate — Final)
APPROVE PHASE 10
EXPLICIT: human types GO or NO-GO

---

## Phase 10 completion checklist

- [ ] Usability test tasks approved by PO + SME (Step 39)
- [ ] Usability test report generated (Step 40)
- [ ] All Beta-blocker usability issues have GitHub Issues (Step 40)
- [ ] All blocker issues resolved — Figma changed + PR merged (Step 41)
- [ ] Round 2 usability tests completed (Step 42)
- [ ] Beta Readiness Report generated (Step 42)
- [ ] GO/NO-GO decision explicitly recorded (Step 42)
- [ ] Beta Readiness GitHub Issue created and URL logged (Step 42)

---

## Workflow complete

When APPROVE PHASE 10 is received with a GO decision, print:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ SAT Frontend UX Workflow — COMPLETE

Phases completed: 1–10
Steps completed: 1–42
Beta Readiness: GO
Handoff to: DevOps Engineer

Gate log: [summary of all 10 phase gates]
GitHub Issues created: [count]
Design freeze: [date]
Figma file: [link]
Monorepo frontend: [path]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
