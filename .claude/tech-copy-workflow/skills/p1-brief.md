# Phase 1 — Brief
# Steps 1–4 | Content type intake, feature verification, audience definition, Diataxis classification

## Phase Goal
Lock the brief before writing begins. Every ambiguity resolved here saves a full revision cycle later.
A brief that takes 10 minutes to lock saves 60 minutes of rework.

---

## Step 1 — Content Type Intake

### Agent actions
Identify what is being requested. Ask the human to confirm if unclear.

**Required intake information:**
1. **Content type** — which of the 9 types from `content-types.md`? (onboarding, tooltip, error, empty state, loading, help article, API doc, release notes, technical blog)
2. **Feature or topic** — which SAT feature or analysis is this content about?
3. **Trigger context** — what user action or state triggers this content? (e.g., "user clicks 'Run Flood Analysis' for the first time", "API user sends malformed GeoJSON", "engineer building integration")
4. **Destination** — where does this copy appear? (in-app UI, help center, developer docs, blog, changelog)

**If request is ambiguous:**
Ask 1–2 clarifying questions before proceeding. Do not infer the content type from vague language like "write something about the flood analysis."

### Output format
```
## P1 Brief — Content Type Intake

Content type: [name]
Feature / topic: [name]
Trigger context: [description]
Destination: [location]
```

---

## Step 2 — Feature Status Verification

### Agent actions
Before writing anything, verify the feature's current build status.

1. Read `PROJECT_OVERVIEW.md` → find the feature → check ✅/🔄/📋 status
2. If a Feature Validation Document (FVD) exists for this feature, identify its path in `/Volumes/LocalDrive/SAT/docs/feature-validation/`
3. Confirm the feature is in the correct status for the intended copy

**Copy permission by status:**

| Status | Allowed copy | Restriction |
|---|---|---|
| ✅ Done | Full feature copy — all content types | None |
| 🔄 Migrating | "Available in legacy interface; migrating to new UI" | Flag as transitional |
| 📋 Planned | Strategy/planning docs only | Never write as if live |

**If status is 📋 Planned:**
Flag immediately:
```
⚠️ Feature Status: [Feature] is 📋 Planned — not yet built.
Content will include the disclaimer: "[Feature] is currently in development and not yet available in SAT."
Confirm you want to proceed with forward-looking copy.
```

### Output format
```
## Feature Status

Feature: [name]
Current status: [✅/🔄/📋]
FVD path: [path or "none found"]
Copy permission: [full / transitional / forward-looking with disclaimer]
```

### Gate
APPROVE STEP 2

---

## Step 3 — Audience Definition

### Agent actions
Define the specific audience for this content piece.

SAT has 3 distinct audiences with different vocabulary, goals, and cognitive contexts:

**Audience A — Architect (in-app user)**
- Profile: practicing architect at a Tier-1 Indian firm
- Vocabulary: architectural, spatial, visual — not GIS or API
- Goal: make a design decision or produce a deliverable
- State when reading this content: [first-time / active use / error / waiting]
- Key principle: intelligent but GIS-vocabulary-free

**Audience B — Developer / Integrator**
- Profile: engineer building on top of SAT or integrating SAT outputs into their system
- Vocabulary: API-fluent, JSON-comfortable, GIS-aware
- Goal: implement a correct integration without ambiguity
- Key principle: precision > brevity; completeness mandatory

**Audience C — Internal / Cross-functional**
- Profile: product manager, designer, or stakeholder reading technical docs for context
- Vocabulary: product-aware, not deeply technical
- Goal: understand what a feature does and how it works conceptually

**For the content in this brief:**
Identify the primary audience. State their cognitive state at the moment they encounter this content (e.g., "Architect who just saw an error for the first time — frustrated, time-pressured, wants to recover quickly").

### Output format
```
## Audience

Primary audience: [Architect / Developer / Internal]
Cognitive state: [description]
Vocabulary constraint: [key terms to avoid or translate]
Secondary audience (if any): [description]
```

---

## Step 4 — Diataxis Classification

### Agent actions
Classify the content into one of the 4 Diataxis quadrants. This determines the structure, tone, and length.

**Classification decision tree:**

```
Is the user trying to complete a specific task?
  YES → Is this their first time doing it?
    YES → Tutorial
    NO  → How-To Guide
  NO  → Are they looking for information to use elsewhere?
    YES → Reference
    NO  → They want to understand — Explanation
```

**Confirm the classification is valid for the chosen content type:**
- Onboarding modals → Tutorial ✓
- Tooltips → Reference or Explanation ✓ (never Tutorial)
- Error messages → How-To ✓ (recovery is a task)
- Help articles → How-To or Explanation ✓ (never Tutorial — that's onboarding)
- API docs → Reference ✓
- Release notes → Reference ✓
- Technical blog → Explanation ✓ (with Insight arc)

**If the content spans quadrants:** flag it. Confirm with human whether to:
a) Split into separate pieces (preferred)
b) Prioritize one quadrant and note the secondary elements

### Output format
```
## Diataxis Classification

Quadrant: [Tutorial / How-To / Reference / Explanation]
Justification: [one sentence — why this classification fits]
Structure implication: [what this means for how the content is organized]
```

### Gate (Phase Gate)
APPROVE PHASE 1
(Brief locked. Quadrant, content type, feature status, and audience confirmed. Proceed to P2 Discovery.)

---

## Phase 1 Completion Checklist

- [ ] Content type confirmed from the 9 types in content-types.md
- [ ] Feature name identified
- [ ] Feature status verified (✅/🔄/📋)
- [ ] FVD path noted (or flagged as absent)
- [ ] Primary audience defined with cognitive state
- [ ] Diataxis quadrant locked
- [ ] No ambiguities remaining before writing begins
