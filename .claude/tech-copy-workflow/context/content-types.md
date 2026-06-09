# SAT Technical Copy — Content Types Reference

Nine content types. Each has a fixed Diataxis quadrant, audience, length limit, tone, and gate requirements.
This is the authoritative lookup for the technical copywriter. Load before P3 Architecture.

---

## Content Type Matrix

| # | Content Type | Diataxis | Audience | Max Length | Review Gate |
|---|---|---|---|---|---|
| 1 | Onboarding modal | Tutorial | Architect (first-time) | 3 screens, 30 words/screen | P5 SME (if feature claims) |
| 2 | Tooltip | Reference / Explanation | Architect (active user) | 2 sentences, ≤30 words | P5 SME (if data source claim) |
| 3 | Error message | How-To | Architect (error state) | 3 parts, ≤25 words total | None required (factual checks in P4) |
| 4 | Empty state | Tutorial | Architect (new feature) | 2 sentences + 1 CTA ≤10 words | None required |
| 5 | Loading copy | Reference | Architect (waiting) | 1 sentence per stage, cycling | None required |
| 6 | Help article | How-To / Explanation | Architect (self-serve) | 300–600 words | P5 SME (data + methodology) |
| 7 | API endpoint doc | Reference | Developer / Integrator | OpenAPI-standard | P5 SME (mandatory) |
| 8 | Release notes / Changelog | Reference | All users | Keep a Changelog format | None (FVD-traceable only) |
| 9 | Technical blog | Explanation | Architect (awareness) | 600–1200 words | P5 SME (for any claim cited) |

---

## Type 1 — Onboarding Modal

**Quadrant:** Tutorial
**Audience:** Architect using a feature for the first time
**Goal:** Deliver the minimum context to enable a successful first action. Not comprehensive documentation.

**Structure (3 screens maximum):**
```
Screen 1 — What + Why
  Headline: ≤7 words — what this feature produces
  Body: ≤25 words — the output value for their work (not the algorithm)

Screen 2 — How to Start
  Headline: ≤7 words — the main action
  Body: ≤20 words — steps to start, no jargon

Screen 3 — First Action
  CTA: specific verb + outcome (≤10 words)
  Skip button always visible
```

**Tone:** Warm, encouraging, brief. Not sales-y. No feature lists.
**SME gate:** Required if any screen references data source accuracy, coverage claims, or regulatory standards.
**Archive note:** Save onboarding copy to `docs/copy-library/onboarding/` with feature name and version.

---

## Type 2 — Tooltip

**Quadrant:** Reference (data field) or Explanation (UI control)
**Audience:** Architect in active use — querying what a metric means
**Goal:** Immediate comprehension. No scrolling required.

**Two sub-types — never mix in one tooltip:**

**Type 2a — Data field tooltip:**
```
Format: [What it measures] + [Scale/unit] + [What the number means for them]
Max: 2 sentences, ≤30 words
```

**Type 2b — UI control tooltip:**
```
Format: [What this control does] + [How to use it]
Max: 1 sentence, ≤20 words
```

**Tone:** Neutral, precise, no personality.
**SME gate:** Required if tooltip cites a specific accuracy figure or data source capability.
**Coordinate warning:** If tooltip includes coordinate examples, confirm [Lon, Lat] order.

---

## Type 3 — Error Message

**Quadrant:** How-To (recovery-oriented)
**Audience:** Architect in failure state — time-pressured, possibly frustrated
**Goal:** Immediate recovery path. No blame. No vague apologies.

**Structure (P+C+S — all 3 mandatory):**
```
[P] Problem: What happened (plain, specific)
[C] Cause: Why (honest, not technical jargon)
[S] Solution: What to do (actionable, specific)
```

**Total length:** ≤25 words across all 3 parts
**Tone:** Calm, professional, action-oriented. Never "Oops!" Never accusatory.
**SME gate:** Not required for standard error messages. Required if error message references a specific data source limit (e.g., "MERIT DEM unavailable for this region") — verify the condition is accurate.
**Coordinate warning:** If error mentions coordinates, confirm format in any example given.

---

## Type 4 — Empty State

**Quadrant:** Tutorial (pre-action) or How-To (no-data)
**Audience:** Architect who hasn't run the feature yet, or who ran it and got no results
**Goal:** Prevent confusion. Explain what the space is for and how to fill it.

**Two sub-types:**

**Type 4a — Pre-action (feature exists, not yet run):**
```
Sentence 1: What this panel shows when it's populated
Sentence 2: The value to them (why they should run it)
CTA: [Specific verb + outcome]
```

**Type 4b — No-data (analysis ran, location has no data):**
```
Sentence 1: What was tried and what failed
Sentence 2: Why (specific, not vague)
CTA: [What to try instead]
```

**Tone:** Helpful, neutral. Not apologetic.
**SME gate:** Required only if data coverage claim is in the empty state message.

---

## Type 5 — Loading Copy

**Quadrant:** Reference
**Audience:** Architect waiting for analysis
**Goal:** Reduce perceived wait time; build trust by naming what SAT is doing.

**Rules:**
- Must name the actual computation or data source being fetched
- Sequence: fastest → slowest step. Each line shows when it appears.
- Never: "Loading..." / "Please wait..." / "Processing..."
- Progressive messages preferred over a single static line

**Format:**
```
Stage 1 (0–2s): "[Specific action 1]..."
Stage 2 (2–5s): "[Specific action 2]..."
Stage 3 (5+s): "[Specific action 3 or reassurance]..."
```

**Tone:** Informative, matter-of-fact. No personality injection.
**SME gate:** Not required. Accuracy verified in P4 against known service architecture.

---

## Type 6 — Help Article

**Quadrant:** How-To or Explanation (never Tutorial — those are onboarding modals)
**Audience:** Architect troubleshooting or seeking deeper understanding
**Goal:** Enable a specific task (How-To) or build a mental model (Explanation).

**How-To structure:**
```
Heading: "How to [verb] [specific outcome]"
Intro: ≤2 sentences — who this is for and when to use it
Steps: numbered, each ≤20 words
Outcome: what success looks like
Next steps: optional link to related doc
```

**Explanation structure:**
```
Heading: "Understanding [topic]" or "How [feature] works"
Intro: ≤3 sentences — the key mental model
Section 1: The concept
Section 2: How SAT applies it
Section 3: What it means for the user's work
Related: links to How-To and Reference docs on the same topic
```

**Length:** 300–600 words. No padding.
**EPPO check mandatory:** Article must be self-contained. No "as explained earlier."
**Flesch-Kincaid target:** 50–65
**SME gate:** Required. All methodology claims, data source descriptions, and accuracy figures reviewed by engineer before publishing.

---

## Type 7 — API Endpoint Documentation

**Quadrant:** Reference
**Audience:** Developer integrating SAT APIs or building on top of the platform
**Goal:** Enable correct API usage without any external resource. 100% complete.

**Structure (OpenAPI-aligned):**
```
## [METHOD] /path/to/endpoint

### Description
[One sentence: what this endpoint does]

### Request
**Method:** [GET / POST]
**Content-Type:** application/json

#### Parameters / Request Body
| Field | Type | Required | Description |
|---|---|---|---|
| [name] | [type] | [Yes/No] | [plain English description] |

#### GeoJSON Coordinate Note
⚠️ coordinates: [Longitude, Latitude] — not [Latitude, Longitude]

#### Example Request
\`\`\`json
[full example — no placeholders]
\`\`\`

### Response
#### Success (200)
| Field | Type | Description |
|---|---|---|

#### Example Response
\`\`\`json
[full example]
\`\`\`

### Error Codes
| Code | Meaning | How to fix |
|---|---|---|
```

**Length:** No limit — completeness is mandatory.
**Tone:** Neutral, austere. No storytelling. Tables and examples preferred over prose.
**Coordinate warning:** Required in every endpoint doc that accepts or returns geographic data.
**SME gate:** Mandatory. Engineer must verify every field, type, and example before publishing.

---

## Type 8 — Release Notes / Changelog

**Quadrant:** Reference
**Audience:** All SAT users (architects + developers)
**Goal:** Clear record of what changed, why it matters, and whether action is needed.

**Format:** Keep a Changelog (keepachangelog.com)
```
## [Version] — YYYY-MM-DD

### Added
- [New feature or capability — one line each]

### Changed
- [Behavior change — old behavior → new behavior]

### Deprecated
- [Feature entering end-of-life — what replaces it, when it ends]

### Removed
- [Feature removed — migration path if applicable]

### Fixed
- [Bug fix — what was broken, what the fix affects]

### Security
- [Security fix — REQUIRED to list even without detail]
```

**Rules:**
- Every item: active voice, one line, references affected feature
- No internal ticket numbers in user-facing changelog (use GitHub PR or FVD reference)
- "Added" items must reference only ✅ Done features — never 📋 Planned
- Fixed items: describe user-visible impact, not code change

**Tone:** Factual, concise. No marketing language in changelogs.
**SME gate:** Not required. All entries FVD-traceable or human-confirmed before writing.

---

## Type 9 — Technical Blog

**Quadrant:** Explanation
**Audience:** Architect (awareness / consideration) — typically arriving via search or LinkedIn
**Goal:** Build SAT's authority as a domain expert. Architect walks away having learned something useful, with SAT as the source.

**Structure:**
```
Headline: [Specific, data-anchored, ≤10 words]
Hook (100 words): A specific problem architects face — not a product pitch
Insight (200 words): The key knowledge, explained clearly
SAT Connection (150 words): How SAT applies or solves this — data-backed
Conclusion (100 words): The takeaway, without the hard sell
CTA (1 line): Soft — "Explore [feature] →" not "Sign up now"
```

**Length:** 600–1200 words. Quality > length.
**Flesch-Kincaid target:** 45–60
**Tone:** Authoritative peer. Not a vendor. No "At SAT, we believe..."
**No unfounded claims:** Every metric, data source reference, and comparison must be source-traceable.
**SME gate:** Required for any technical claim that goes beyond FVD documentation.
**India market alignment check:** All examples use Indian firms, Indian cities, Indian regulations.

---

## Gate Escalation Summary

| Content Type | Auto-approved | SME gate triggers |
|---|---|---|
| Onboarding modal | If no accuracy/coverage claims | Data source accuracy, regulatory standard reference |
| Tooltip | If visual description only | Specific accuracy figures, data source capability |
| Error message | Always (verify in P4) | Data source limit claims |
| Empty state | Always | Data coverage claims |
| Loading copy | Always | Never |
| Help article | Never | All methodology, accuracy, data source claims |
| API docs | Never | All fields, types, examples |
| Release notes | If FVD-traceable | Any uncited feature claim |
| Technical blog | Never | All technical claims beyond FVD |
