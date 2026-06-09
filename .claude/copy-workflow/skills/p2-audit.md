# Phase 2 — Research & Competitive Audit
# Steps 5–8 | Competitor copy, existing SAT copy, audience intelligence, proof points

## Phase Goal
Build an evidence base before writing. Good copy is downstream of good research.
This phase is optional for quick-turn single assets but required for landing pages,
email sequences, and any copy that will run at scale (piloting, conference).

---

## Step 5 — Competitive Copy Audit

### Agent actions
1. For each relevant competitor in `/Volumes/LocalDrive/SAT/.claude/copy-workflow/context/competitive-landscape.md`,
   use WebSearch to pull their current live positioning copy.
   Focus: homepage headline, hero subhead, primary CTA, one feature page.

2. For each competitor, extract:
   - **Headline**: exact text
   - **Primary claim**: what they say they do
   - **Proof type**: (data / social proof / authority / vague)
   - **Persona targeted**: (developer / architect / BIM / general)
   - **Tone**: (technical / aspirational / ROI-focused / generic)
   - **Weaknesses**: where their copy is vague, generic, or misses Indian market reality

3. Identify **vocabulary gaps**: terms SAT can own that competitors avoid
   (NBC 2016, IMD, BBMP, Vastu, NREL SPA — these are SAT-differentiating and absent from competitor copy).

4. Identify **claim inflation**: where competitors make vague claims SAT can beat with specifics.

### Output format
```
## Competitive Copy Audit

### [Competitor Name]
Homepage headline: "[exact text]"
Primary claim: [what they say]
Proof type: [data / social proof / authority / vague]
Persona targeted: [who]
Tone: [descriptor]
Weakness for SAT to exploit: [specific gap]

[repeat for each competitor]

## Vocabulary SAT can own (not used by competitors):
- [term 1]
- [term 2]

## Claim inflation opportunities (SAT can beat with specifics):
- Competitor says "[vague]" → SAT can say "[specific]"
```

### Gate
APPROVE STEP 5

---

## Step 6 — SAT Copy Inventory

### Agent actions
1. Search existing SAT copy across:
   - `/Volumes/LocalDrive/SAT/apps/web/` — any existing landing page or onboarding copy
   - `/Volumes/LocalDrive/Site Analysis/` — any existing marketing docs, README copy, Jira ticket descriptions
   - Ask the human: "Is there any existing email copy, slide deck copy, or published content I should review?"

2. For each piece found, evaluate:
   - Does it comply with brand voice? (flag banned words)
   - Is it persona-specific or generic?
   - Does it make any claims that reference 📋 Planned features without a disclaimer?
   - Does it use specificity or vague claims?

3. Flag inconsistencies. These become constraints for new copy (must maintain consistency
   or explicitly supersede the old copy).

### Output format
```
## SAT Copy Inventory

### [Asset name / location]
Current copy: "[excerpt]"
Brand voice compliance: [pass / fail — flag issues]
Persona: [specific / generic]
Feature claims: [verified / unverified 📋 features]
Specificity: [strong / weak]
Action: [keep / update / retire]

## Copy conflicts to resolve before publishing new copy:
- [conflict 1]
```

### Gate
APPROVE STEP 6

---

## Step 7 — Audience Intelligence

### Agent actions
Based on the locked persona (from Phase 1 Step 3), build a specific intelligence brief.
Do not invent data — pull from approved sources or ask the human.

Sources:
- `/Volumes/LocalDrive/SAT/.claude/copy-workflow/context/buyer-personas.md`
- `/Volumes/LocalDrive/Site Analysis/PROJECT_OVERVIEW.md` §2
- Any user interview transcripts the human provides
- WebSearch for recent AEC market news in India (e.g., "Indian architecture firm technology adoption 2026")

Compile:
1. **Their current frustration** (what the target persona complains about re: site analysis today)
2. **Their language** (exact phrases architects use — pull from Reddit r/Indian_architects, architecture forum discussions, any provided transcripts)
3. **Their buying trigger** (what event causes them to evaluate a new tool: new project, lost pitch, new regulation, competitor adoption)
4. **Their objection** (the one thing that will stop them from buying even if they like SAT)

### Output format
```
## Audience Intelligence — [Persona name]

Current frustration: [specific, quoted where possible]
Their language: [phrases they use — not marketing language]
Buying trigger: [what event starts the evaluation]
Primary objection: [the one blocker]
Counter-message for objection: [how SAT's copy addresses it]
```

### Gate
APPROVE STEP 7

---

## Step 8 — Proof Point Collection

### Agent actions
Compile all verified proof points available for this copy asset.

**Tier 1 — Hard proof (cite source)**
- SAT-specific metrics from FVD specs (e.g., NREL SPA ±0.0003° from SAT-04 FVD)
- Process comparisons confirmed by the human ("5 min vs 2 weeks" — source: human input)
- Data source authority (IMD = official India government meteorological data)

**Tier 2 — Industry proof (cite source)**
- AEC industry benchmarks (from competitive audit, research report)
- Regulatory specifics (NBC 2016 clauses, ECBC energy intensity benchmarks)

**Tier 3 — Social proof (confirm before using)**
- Named firm examples — human must confirm if real or aspirational
- Testimonials — human must provide verbatim text with attribution

**Flag gaps:**
- Any required proof point without a verified source → `[METRIC NEEDED — source required]`
- Do not proceed to copy development with unfilled proof gaps unless human explicitly
  authorizes a placeholder.

### Output format
```
## Proof Inventory — Verified

### Tier 1 (Hard Proof)
- [claim] — Source: [FVD / human input / spec]

### Tier 2 (Industry Proof)
- [claim] — Source: [research report / regulatory document]

### Tier 3 (Social Proof)
- [claim] — Confirmed: [yes / aspirational only]

### Gaps (Flagged)
- [METRIC NEEDED]: [description of what's missing]
```

### Gate (Phase Gate)
APPROVE PHASE 2
(Research phase complete. Brief + proof inventory locked. Proceed to messaging.)

---

## Phase 2 Completion Checklist

- [ ] Competitor copy audited, weaknesses identified (Step 5)
- [ ] Existing SAT copy inventoried, conflicts flagged (Step 6)
- [ ] Audience intelligence compiled for locked persona (Step 7)
- [ ] Proof inventory complete — all gaps flagged with [METRIC NEEDED] (Step 8)
- [ ] Human confirmed any aspirational social proof claims (Step 8)
