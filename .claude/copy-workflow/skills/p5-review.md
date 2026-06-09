# Phase 5 — Review & Refinement
# Steps 18–21 | Brand check, technical accuracy, regulatory review, final revision

## Phase Goal
Harden the approved draft before it leaves the team. Copy that ships with false claims,
regulatory errors, or brand voice violations costs more to fix after publishing than it
does to catch here.

---

## Step 18 — Brand Voice Check

### Agent actions
Run a systematic brand voice audit against `/Volumes/LocalDrive/SAT/.claude/copy-workflow/context/brand-voice.md`.

**Check 1 — Banned word scan**
Search the full draft for every word on the banned list.
Flag each instance with: original phrase → suggested replacement.

**Check 2 — Tone calibration**
Read the full draft and assess against the five tone dimensions:
- Authority: confident + specific? Or boastful?
- Technical depth: AEC-fluent? Or archibabble?
- Relationship: peer-to-peer? Or vendor-to-buyer?
- Specificity: concrete numbers throughout? Or vague claims?
- Urgency: contextual and earned? Or manufactured?

**Check 3 — Voice consistency**
If SAT has existing published copy (from Phase 2 Step 6 inventory):
Does this new copy sound like it was written by the same author?
Flag any sections that feel tonally inconsistent.

**Check 4 — Proof hierarchy**
Verify the proof hierarchy from brand-voice.md is applied:
1. Named firm + specific outcome (strongest)
2. Quantified process comparison
3. Data source authority
4. Standard compliance
5. Algorithm authority
6. Feature description (weakest — should not be the primary proof)

Is the copy leading with the strongest proof available? If not, reorder.

### Output format
```
## Brand Voice Audit

Banned words: [PASS / list instances with fixes]
Tone: [✅ each dimension or ❌ with fix]
Voice consistency: [PASS / inconsistent sections]
Proof hierarchy: [leading with [proof type] — appropriate? Y/N / reorder suggestion]

Updated draft (if changes made):
[revised copy]
```

### Gate
APPROVE STEP 18

---

## Step 19 — Technical Accuracy Check

### Agent actions
Every claim in the copy that references a SAT feature, data source, or analytical capability
must be traceable.

**Traceability protocol:**
1. List every technical claim in the draft
2. For each claim, identify the source:
   - FVD spec in `/Volumes/LocalDrive/SAT/docs/feature-validation/`
   - Human-confirmed metric (from Phase 1 or Phase 2)
   - Research citation (from competitive audit)
3. Flag any claim without a traceable source as `[UNVERIFIED — source required]`

**High-risk claims to audit with extra care:**
- Accuracy claims (e.g., "±0.0003° solar position accuracy") → verify against SAT-04 FVD
- Data freshness claims ("daily weather updates") → verify against architecture
- Coverage claims ("any site in India") → verify against service documentation
- Integration claims ("Revit-compatible GeoJSON export") → verify is live, not planned
- Compliance claims ("NBC 2016 setback computation") → verify is live, flag if 📋 Planned

**Data source accuracy:**
Any named data source (IMD, MERIT DEM, JRC GSW, Open-Meteo, NREL SPA, pvlib, GEE) must be:
- Spelled and abbreviated correctly
- Applied to the correct feature (e.g., MERIT DEM is for flood/elevation — not for solar)
- Not overstated (e.g., IMD is India-only; Open-Meteo is global fallback)

### Output format
```
## Technical Accuracy Audit

| Claim | Source | Status |
|---|---|---|
| "[claim]" | [FVD / human / research] | ✅ verified |
| "[claim]" | — | ❌ [UNVERIFIED] |

Data source accuracy: [PASS / issues listed]

Updated draft (if claims removed or corrected):
[revised copy]
```

### Gate
APPROVE STEP 19

---

## Step 20 — Regulatory Accuracy Check

### Agent actions
Copy that references Indian regulatory standards must pass an additional check.

**Standard-by-standard:**

**NBC 2016 (National Building Code):**
- Is the claim specific to a chapter/section? (e.g., "Part 6 setback requirements" not just "NBC-compliant")
- Does the claim apply to the correct building type and location?
- Flag with `[SME REVIEW REQUIRED]` if specific clause is referenced but unconfirmed

**ECBC 2017 (Energy Conservation Building Code):**
- Is the specific metric named (energy performance index, glazing ratio, etc.)?
- Does SAT actually compute this, or is it guidance copy? (Verify feature status)
- Flag with `[SME REVIEW REQUIRED]` for specific efficiency benchmarks

**BBMP / BDA (Bengaluru local bodies):**
- Is this copy specifically for Bengaluru-focused use cases?
- Is the regulation current (BBMP has amended regulations — confirm year)
- Flag with `[SME REVIEW REQUIRED]` for any specific bylaw reference

**Auto-DCR:**
- Any claim about Auto-DCR integration requires SME confirmation
- SAT does not currently have a certified Auto-DCR integration — do not imply it does

**Vastu Shastra:**
- If Vastu bridge is deployed, verify framing is scientific (light + ventilation data) not supernatural
- Do not claim SAT is "Vastu-certified" or "Vastu-validated" — it analyzes orientation factors that align with Vastu principles, but is not a Vastu authority

### Output format
```
## Regulatory Accuracy Check

NBC 2016 references: [PASS / [SME REVIEW REQUIRED] — list]
ECBC 2017 references: [PASS / [SME REVIEW REQUIRED] — list]
BBMP/BDA references: [PASS / [SME REVIEW REQUIRED] / N/A]
Auto-DCR references: [none / [SME REVIEW REQUIRED] if present]
Vastu framing: [scientifically framed / ❌ overclaims Vastu authority]

SME gates opened (if any): [list steps requiring SME APPROVED before publishing]
```

### Gate [SME GATE if any regulatory flags raised]
APPROVE STEP 20
(If SME gates are open: copy cannot publish until SME APPROVED received.)

---

## Step 21 — Final Revision & Delivery Draft

### Agent actions
Incorporate all changes from Steps 18–20. Produce the final clean draft.

**Final checklist before delivery:**
- [ ] No banned words
- [ ] All proof claims traceable
- [ ] No 📋 features without disclaimer
- [ ] All SME gates either passed or flagged as pending
- [ ] Headlines comply with length limits (≤8 words for hero)
- [ ] CTAs are action verb + specific outcome (not generic)
- [ ] Length complies with channel guidelines from brand-voice.md
- [ ] `<copy_rationale>` block is present and accurate

**Pre-publish note to human:**
State which SME gates (if any) are still open and cannot be waived before the copy ships.

### Output format
```
## Final Draft — [Asset type] — [Persona] — [Date]
Status: READY FOR HANDOFF (pending [N] SME gates / all clear)

[clean final copy — no annotations, no brackets]

---
<copy_rationale>
Persona: [name]
Framework: [name]
Primary lever: [lever]
Proof used: [list]
SME gates: [open / all clear]
</copy_rationale>
```

### Gate (Phase Gate)
APPROVE PHASE 5
(Final draft locked. Proceed to handoff in Phase 6.)

---

## Phase 5 Completion Checklist

- [ ] Brand voice audit: no banned words, all tone dimensions pass (Step 18)
- [ ] Technical accuracy: all claims traceable (Step 19)
- [ ] Regulatory accuracy: all NBC/ECBC/BBMP/Vastu references verified or flagged (Step 20)
- [ ] SME gates: opened for any unverified regulatory claims (Step 20)
- [ ] Final draft clean and complete (Step 21)
- [ ] copy_rationale block accurate and present (Step 21)
