# Phase 5 — SME Review
# Steps 17–20 | Pre-SME checklist, question delivery, correction incorporation, gate log

## Phase Goal
Validate every technical claim before it publishes. SME review is not a rubber stamp — it is the accuracy gate that prevents user-visible errors. An architect who catches a wrong claim in SAT copy will question everything else SAT says.

---

## Step 17 — Pre-SME Checklist

### Agent actions
Before escalating to the SME, self-verify everything that can be verified without human expertise.

**Self-verification checklist:**

**FVD cross-reference:**
- [ ] Every data source named in the copy matches the FVD's data source list
- [ ] Every accuracy figure in the copy exists in the FVD (not inferred)
- [ ] Every feature capability described is in the FVD's "Done" acceptance criteria
- [ ] No 📋 Planned features described as if live

**Coordinate order:**
- [ ] Every GeoJSON example in the copy is [Lon, Lat]
- [ ] Every bounding box is [minLon, minLat, maxLon, maxLat]
- [ ] API parameter descriptions say "Longitude, Latitude" not "latitude, longitude"

**Regulatory terminology:**
- [ ] Every regulatory standard reference includes a specific version year (NBC 2016, not "NBC")
- [ ] Every ECBC reference names a specific metric
- [ ] No Auto-DCR claims without human confirmation

**Feature status:**
- [ ] No live-copy language for 📋 Planned features
- [ ] 🔄 Migrating features marked as transitional where shown in copy

**Report format:**
```
## Pre-SME Self-Verification

FVD cross-reference: [PASS / issues]
Coordinate order: [PASS / issues]
Regulatory terminology: [PASS / issues]
Feature status: [PASS / issues]

Self-verified — no SME gate needed for: [list claims]
SME gates required for: [list claims]
```

### Gate
APPROVE STEP 17

---

## Step 18 — SME Question Delivery

### Agent actions
Send the prepared SME questions from Step 7 (P2 Discovery) to the human for escalation.

**Pre-send format (review before delivering to SME):**
Each question must be binary or specific — no open-ended questions.

**Delivery package:**
```
## SME Questions for [Feature] — [Date]

Context for SME: "We're writing [content type] for [feature]. Reviewing for technical accuracy before publishing."

Q1 (blocking): [binary question]
Expected answer: [A or B or specific value]
Why it matters: [what claim this verifies, what the fallback is if answer is different]

Q2 (high priority): [binary question]
Expected answer: [A or B or specific value]
Fallback if different: [safe alternative phrase that works if Q2 answer changes the claim]

Q3 (medium): [binary question]
Expected answer: [A or B or specific value]
Fallback: [safe phrase]
```

**Batch limit: max 3 per interrupt.** If there are more questions, hold the lower-priority ones and ask the human: "Shall I queue the next set after these are answered?"

**After receiving SME responses:**
- Log the response (who answered, date, exact claim verified) in the SME Gate Log
- Update the draft with the confirmed information
- If the SME corrects a claim: update the draft; do not retain the incorrect version anywhere

---

## Step 19 — SME Correction Incorporation

### Agent actions
Apply every SME correction to the draft.

**Correction principles:**
- Incorporate corrections precisely — do not paraphrase the SME's correction
- If the SME's answer creates a longer/more technical explanation than the original copy allowed: apply the correction and then re-apply the plain language rules. The correction must be both accurate and readable.
- If the SME's correction fundamentally changes what the copy says (not just a number adjustment): re-run the Diataxis quadrant check. Does the corrected claim still fit the intended content type?

**Conflict resolution:**
If a SME correction conflicts with the FVD: flag it. The FVD may be stale. Present both to the human and request clarification before updating either.

**SME Gate Log entry format:**
```
| Date | Feature | Claim in copy | SME question | SME answer | Updated in draft | Verified by |
|---|---|---|---|---|---|---|
| 2026-06-09 | Flood | "90m resolution" | "MERIT DEM India resolution?" | "Confirmed 90m nationwide" | ✅ | [name] |
```

### Output format
Present the revised draft section with corrections applied. Mark corrections clearly:
```
[REVISED - SME confirmed]: "SAT uses MERIT DEM elevation data at 90m resolution for India."
```

---

## Step 20 — Gate Log and Status Update

### Agent actions
Document the final SME review state and set the content status.

**Content status options:**
- `APPROVED — all clear`: all SME gates resolved, no open items
- `APPROVED — SME PENDING [N] items`: human approved the phase, SME gates still open. Cannot publish.
- `HOLD — SME PENDING`: phase not approved until SME gates close

**Final SME Gate Log:**
```
## SME Review Summary — [Content type] — [Feature] — [Date]

Total SME gates opened: [N]
Gates resolved: [N]
Gates pending: [N]

Pending gates (cannot publish until resolved):
1. [specific claim] — waiting for: [SME name / question]

Content status: [APPROVED - all clear / APPROVED - SME PENDING / HOLD - SME PENDING]
```

**If any gates are open:** do not proceed to P7 Publish. Proceed to P6 Editorial for copy quality review, but mark P7 as blocked.

### Gate (Phase Gate)
APPROVE PHASE 5
(All SME gates either resolved or documented as pending. Proceed to P6 Editorial.)

---

## Phase 5 Completion Checklist

- [ ] Pre-SME self-verification complete — all self-checkable items verified
- [ ] SME questions batched (max 3) and delivered via human
- [ ] All SME responses incorporated into draft
- [ ] SME Gate Log completed with dates, claims, responses, and verifiers
- [ ] Content status set (APPROVED / PENDING)
- [ ] If any gates open: flagged clearly, P7 marked as blocked
- [ ] Revised draft is clean — no correction markup remaining in final version
