# Phase 7 — Publish
# Steps 25–28 | Platform formatting, changelog entry, search optimization, archive

## Phase Goal
Get the copy into the right format for its destination and create a durable record of it. Publishing without archiving means the copy is untrackable and unreplaceable if the feature changes.

**Pre-condition:** Phase 7 is blocked if any SME gates from Phase 5 are still open. All gates must show `SME APPROVED` before proceeding.

---

## Step 25 — Platform Formatting

### Agent actions
Format the final copy for its specific destination. Different platforms have different requirements.

**In-app UI copy (tooltips, buttons, error messages, loading, empty states, onboarding):**
```
Deliver as a structured copy spec:

## [Component name] — Copy Spec

### Loading states
Stage 1 (0–Xs): "[copy]"
Stage 2 (X–Ys): "[copy]"
Stage 3 (Y+s): "[copy]"

### Empty states
Pre-action: "[copy]"
CTA: "[button label]"
No-data: "[copy]"
CTA: "[button label]"

### Error messages
[Error condition]: "[copy]"
[Error condition]: "[copy]"

### Tooltips
[Field/control name]: "[copy]"

### Buttons
[Action context]: "[button label]"
```

**Help center article:**
```
Format: Markdown
Heading levels: # H1 (title), ## H2 (sections), ### H3 (subsections)
Code blocks: triple backtick with language identifier
Internal links: relative URLs within help center
Metadata block at top:
  title: [title]
  description: [SEO meta, ≤155 chars]
  last_reviewed: [date]
  feature_status: [✅/🔄/📋]
```

**API documentation:**
```
Format: OpenAPI YAML or Markdown per project standard
Must include: method, path, description, parameters (with type/required/example), responses, error codes
GeoJSON note: mandatory on any endpoint with geographic data
Coordinate order note: mandatory inline in every parameter description
```

**Release notes / Changelog:**
```
Format: Keep a Changelog (Markdown)
Location: CHANGELOG.md in SAT monorepo root OR /docs/changelog/
Entry format:
## [Version] — YYYY-MM-DD
### Added
- [Feature] — [one-line description of what it does]
```

**Technical blog:**
```
Format: Markdown with frontmatter
Frontmatter:
  title: [title]
  date: YYYY-MM-DD
  author: [name]
  tags: [site-analysis, flood-analysis, solar-design, etc.]
  description: [≤155 chars]
```

---

## Step 26 — Keep a Changelog Entry

### Agent actions
For every content publish that corresponds to a feature change or new feature: write a changelog entry.

**Even if the task is only new copy** (not a feature code change), some copy types require a changelog entry:
- New onboarding modal added → "Added" entry
- Error message updated → "Changed" entry
- Help article added → "Added" entry (optional, but recommended)
- Feature deprecated with copy update → "Deprecated" entry

**Changelog entry format:**
```
## [Version] — YYYY-MM-DD

### Added
- [Feature name]: [one sentence — what users can now do or see]

### Changed
- [Feature name]: [old behavior] → [new behavior] (if error message rewrite: "Error messages now follow P+C+S format")

### Fixed
- [Feature name]: [what was wrong] → [what is now correct]
```

**Rules:**
- One entry per feature/change
- Present tense, active voice ("Users can now export...") or imperative ("Export flood analysis results as GeoJSON")
- No internal ticket numbers in user-facing changelog
- Reference the FVD or PR if linking to technical context

---

## Step 27 — Search Optimization (Web Content Only)

### Agent actions
For any content published to a publicly accessible URL (help center, technical blog, developer docs):

**Generate:**
1. **Page title** (≤60 characters, keyword-first)
2. **Meta description** (≤155 characters — expands title with proof point)
3. **URL slug** (lowercase, hyphens, descriptive, keyword-anchored)
4. **Primary keyword phrase** — the exact phrase this content should rank for
5. **Related terms** — 2–3 supporting phrases this content will naturally contain

**SAT target keyword patterns:**
```
Help articles: "how to [verb] [SAT feature]" / "[SAT feature] error fix" / "[analysis type] site analysis"
Explainers: "how [analysis type] works" / "[data source] explained architects"
API docs: "[endpoint name] API" / "SAT API [feature] integration"
Blog: "[analysis topic] architects India" / "[Indian city] [analysis type] architecture"
```

**Do not optimize for:**
- Generic SaaS terms ("site analysis software", "architecture analytics")
- Terms owned by competitors without differentiation
- Keywords with intent mismatch (research-stage keywords on a conversion page)

### Output format
```
## Search Metadata

Page title: [text — ≤60 chars]
Meta description: [text — ≤155 chars]
URL slug: /[slug]
Primary keyword: [phrase]
Related terms: [term 1], [term 2], [term 3]
```

---

## Step 28 — Archive and Audit Schedule

### Agent actions
Archive the complete content record and set a review date.

**Archive format:**
```markdown
---
content_type: [type]
feature: [feature name]
audience: [architect / developer / internal]
diataxis_quadrant: [Tutorial / How-To / Reference / Explanation]
status: [published / draft / pending_sme]
date_published: [YYYY-MM-DD]
last_reviewed: [YYYY-MM-DD]
next_review: [YYYY-MM-DD — set based on cadence below]
sme_gates: [all clear / pending: {list}]
fvd_reference: [path or "none"]
---

# [Content title]

[Full final copy]

---
## Tech Copy Rationale
[tech_copy_rationale block from P4]

## SME Gate Log
[Gate log from P5]

## Change History
- [YYYY-MM-DD]: Published
- [YYYY-MM-DD]: [change made] — reason: [brief note]
```

**Archive location:** Ask the human: "Where should I save this? Options: (a) `/Volumes/LocalDrive/SAT/docs/content-library/[type]/` (b) Confluence / Notion (c) inline in feature docs"

**Review schedule:**
| Content type | Review cadence |
|---|---|
| Onboarding modals | On feature change or every 2 months |
| Error messages | On feature change |
| Help articles | Every 2 months or on data source update |
| API docs | On every API change (mandatory) |
| Release notes | Permanent — no review required |
| Technical blog | Every 6 months |

Set the `next_review` date in the frontmatter at time of archiving.

### Gate (Phase Gate)
APPROVE PHASE 7
(Content published and archived. Workflow complete for this piece.)

---

## Phase 7 Completion Checklist

**Pre-conditions:**
- [ ] SME APPROVED received for all open gates from P5

**Steps:**
- [ ] Copy formatted for destination platform (Step 25)
- [ ] Changelog entry written and ready to commit (Step 26)
- [ ] Search metadata generated for web content (Step 27 — or marked N/A for UI copy)
- [ ] Full archive record written with frontmatter (Step 28)
- [ ] Archive location confirmed by human
- [ ] Review date set in archive record
- [ ] Change history started in archive record

**Final status:** Workflow closed. Content live.

---

## Content Library Index

Maintain this index in the content library root:

```
# SAT Content Library

| Title | Type | Feature | Audience | Diataxis | Date | Status | Next Review |
|---|---|---|---|---|---|---|---|
| [title] | [type] | [feature] | [audience] | [quadrant] | [date] | [published] | [date] |
```
