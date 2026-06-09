# Phase 1 — Research & Interviews
# Steps 1–6 | Remote interviews, transcription, repository

## ✅ PHASE 1 COMPLETE — 2026-06-10

All steps approved. Artifacts at `ux-research/phase-1/`. GitHub Issue: https://github.com/Site-Analysis/SAT/issues/13

| Artifact | Path | Status |
|----------|------|--------|
| Participant profiles | `ux-research/phase-1/step-1-participant-profiles.md` | ✅ Approved |
| Interview guide | `ux-research/phase-1/step-2-interview-guide.md` | ✅ Approved (retroactive) |
| Transcript P01 — Rubina | `ux-research/phase-1/transcripts/P01-rubina-junior-architect-2026-06-09.md` | ✅ Approved |
| Transcript P02 — Ranjita | `ux-research/phase-1/transcripts/P02-ranjita-junior-architect-2026-06-09.md` | ✅ Approved |
| Synthetic profiles P03–P05 | `ux-research/phase-1/synthetic/SME-derived-profiles-2026-06-09.md` | ✅ SME Approved (SA·Q3/SP·Q3 follow-up pending 2026-06-11) |
| Repository index | `ux-research/phase-1/step-6-repository-index.md` | ✅ APPROVE PHASE 1 |
| Findings summary | `.claude/ux-workflow/context/phase-1-findings.md` | ✅ Loaded in agent context |

**Read `context/phase-1-findings.md` before starting Phase 2. It contains confirmed tool landscape, pain points, verbatim quotes, and dashboard desires.**

**Outstanding:** SA·Q3 + SP·Q3 SME follow-up — due 2026-06-11. Update `synthetic/SME-derived-profiles-2026-06-09.md` when received.

---

## Phase goal (for future Phase 1 runs)
Collect raw evidence from Indian architects and urban planners about how they
conduct site analysis today. Minimum 5 participants. All recordings transcribed
and approved before Phase 2 begins.

---

## Step 1 — Define Participant Profiles

### Agent actions
1. Present the three starting profile types:
   - Junior architect (0–5 yrs experience)
   - Senior architect (5+ yrs experience)
   - Urban planner / architecture student
2. Ask the human:
   - Q1: How many participants per profile type? (minimum 5 total)
   - Q2: Any geographic constraints? (city, region)
   - Q3: Any firm-size preference? (solo practice, studio, large firm)
3. Generate a Participant Screening Criteria doc with: profile definitions,
   inclusion criteria, and disqualifying criteria.
4. Show the doc. Show the gate.

### Output format
```
## Participant Profiles

### Profile 1: [name]
- Experience: [range]
- Role: [definition]
- Inclusion criteria: [list]
- Disqualifying criteria: [list]

[repeat for each profile]

## Target count: [N total, breakdown by profile]
```

### Gate [SME GATE]
Product Owner: APPROVE STEP 1
SME: SME APPROVED (confirms profiles reflect real professional types)

---

## Step 2 — Prepare Interview Questions

### Agent actions
1. Load all questions from the SAT UX Workflow doc (Questionnaire section).
2. Structure into interview guide sections:
   - Warm-up (5 min): role, current project type
   - Workflow (10 min): daily process, tools used
   - Site analysis specifics (15 min): data collection, tool frustrations,
     workflow integration, sensory/subjective data, constraint management
   - Ideal tool (10 min): dream dashboard question, what would change routine
   - Close (5 min): anything else, willingness to test future prototype
3. Add timing estimate per section. Total target: 45–60 min.
4. Flag the 5 highest-priority SAT questions:
   - "Walk me through your typical site analysis process..."
   - "Which software tools do you use for site modelling?..."
   - "What is the biggest manual task your software doesn't handle?"
   - "If you could see one live-updated dashboard of site data..."
   - "Imagine the most ideal version of a site analysis tool..."
5. Show the guide. Show the gate.

### Output format
Markdown interview guide with: section headers, question text, timing,
SAT priority flags marked `[SAT-PRIORITY]`.

### Gate
APPROVE STEP 2

---

## Step 3 — Recruit Participants

### Agent actions
1. Ask the human:
   - Q1: Which outreach channels? (LinkedIn / architecture firm contacts /
     WhatsApp groups / college networks)
   - Q2: Who sends the messages? (agent drafts, human sends)
   - Q3: Has the human created Google Meet / Zoom links for each session?
     If not, remind: "You must create meeting links before outreach — the
     agent cannot create these."
2. Generate outreach message templates for each channel. Keep them short:
   - Who you are, what SAT is (one sentence), what you need (45 min interview),
     what they get (early access + input into the product).
3. Generate a Participant Tracking Table:

```
| # | Name | Role | Firm | Channel | Status | Meeting link | Scheduled time |
|---|------|------|------|---------|--------|--------------|----------------|
```

4. Instruct the human: fill in the table as confirmations arrive.
   When minimum 5 are confirmed, report back to the agent.
5. Show templates and table. Show the gate.

### Gate
APPROVE STEP 3
(gate remains open until human confirms ≥5 participants with meeting links)

---

## Step 4 — Conduct Interviews

### Agent actions
1. Generate a Pre-Interview Briefing Checklist for the human interviewer:
   - Recording consent script (exact wording)
   - Warm-up framing ("We're not testing you, we're learning from you")
   - 'Show me' prompts: "Can you share your screen and show me a recent
     site analysis report or the tools you use?"
   - Note-taking format: behaviour > opinion, quote verbatim when strong
   - Post-interview checklist: save recording, export notes, confirm upload

2. After EACH interview: prompt the human to confirm completion and upload.
   Do not wait until all interviews are done to ask.

3. Track completions in the Participant Tracking Table from Step 3.

4. The agent does NOT attend or conduct interviews.

### Output format
Pre-interview briefing checklist (markdown).
Updated tracking table after each confirmed interview.

### Gate
APPROVE STEP 4
(gate requires ALL scheduled interviews complete AND all recordings uploaded)

---

## Step 5 — Transcribe Interviews

### Agent actions
For each recording, in order:
1. Ask the human to provide the recording file or shareable link.
2. Transcribe with:
   - Speaker labels: `[INTERVIEWER]` and `[PARTICIPANT]`
   - Timestamps every 2 minutes: `[00:02:00]`
   - Verbatim — do not paraphrase or clean up speech
   - Flag these moments inline with `[FLAG: screen-share]`,
     `[FLAG: strong-emotion]`, `[FLAG: show-me-probe]`
3. Present the transcript to the human for accuracy review.
4. Human corrects technical terms (NBC, FSI, BBMP, BIM, AutoCAD, pvlib, etc.)
   and any mis-transcribed Indian-English phrases.
5. Mark transcript as APPROVED only after human signs off.
6. Repeat for each participant.

### Output format
One markdown file per participant:
```
# Transcript — P[N]: [Role] — [Date]
Status: PENDING APPROVAL / APPROVED

[00:00:00]
[INTERVIEWER] [question text]
[PARTICIPANT] [response text]
[FLAG: screen-share] [observation]

[00:02:00]
...
```

### Gate
APPROVE STEP 5
(gate requires ALL transcripts individually approved — not just submitted)

---

## Step 6 — Organise Research Repository

### Agent actions
1. Generate a Research Repository Index:
```
# SAT UX Research Repository — Phase 1

| # | Participant | Role        | Date       | Transcript | Status   |
|---|-------------|-------------|------------|------------|----------|
| 1 | [name]      | [role]      | [date]     | [link]     | Approved |
...

Total participants: [N]
Interview guide version: [date]
Phase 1 completed: [date]
```

2. Draft a GitHub Issue:
   - Title: `UX Research — Phase 1 Complete — Participant Repository`
   - Body: paste the repository index
   - Labels: `ux-research`, `phase-1`, `do-not-close`

3. Ask: "Please create this GitHub Issue in the SAT monorepo and paste the
   issue URL here to confirm."

4. Log the issue URL once provided.

### Gate (Phase Gate)
APPROVE PHASE 1
(requires: issue URL confirmed, all transcripts approved, PO sign-off)

---

## Phase 1 completion checklist

Before APPROVE PHASE 1 is accepted, verify all of:
- [ ] ≥5 participant profiles approved (Step 1)
- [ ] Interview guide approved (Step 2)
- [ ] ≥5 participants recruited and confirmed (Step 3)
- [ ] All interviews conducted and recordings uploaded (Step 4)
- [ ] All transcripts individually approved (Step 5)
- [ ] GitHub Issue created and URL confirmed (Step 6)
