# Phase 6 — Handoff
# Steps 22–25 | Channel format, design annotations, SEO metadata, copy library archive

## Phase Goal
Get the copy into the right format, to the right person, with everything they need
to use it without coming back to ask. A handoff that requires 5 follow-up questions
is not a handoff.

---

## Step 22 — Channel Formatting

### Agent actions
Format the final copy for its delivery channel. Different channels have different
formatting requirements.

**Formatting specs by channel:**

### Landing page (HTML / Figma)
```
## [Hero section]
HEADLINE: [text — H1]
SUBHEAD: [text — H2]
CTA BUTTON: [label]

## [Value props section]
PROP 1 HEADLINE: [text — H3]
PROP 1 BODY: [text — body copy]
[repeat for props 2–3]

## [Social proof section]
[testimonial / data point / firm name]

## [Secondary CTA]
[CTA label]
```
Present in this format so the designer can drop directly into Figma without interpretation.

### Cold email (plain text)
```
SUBJECT LINE: [text]
PREVIEW TEXT: [≤90 chars — what shows in inbox preview]

BODY:
[full email — no HTML, no markdown, as it will read in Gmail]

CTA LINK TEXT: [text to hyperlink]
```

### Email sequence (3–5 emails)
```
## Email 1 of [N]
Subject: [text]
Preview: [text]
Body: [full email]
CTA: [text]
Send trigger: [Day 0 / Day 3 / Day 7 / etc.]
Goal: [what this email achieves in the sequence]

## Email 2 of [N]
[same format]
```

### LinkedIn post
```
[Full post text — formatted with line breaks as it will appear on LinkedIn]
Note: LinkedIn strips markdown. Use line breaks for structure, not headers.
Character count: [N] / 250 limit
```

### Case study (document)
```
HEADLINE: [text]
SUBHEAD: [text]
SUMMARY BOX: [3–4 bullet outcomes — the "results at a glance"]

SECTION 1 — The Challenge: [text]
SECTION 2 — The Approach: [text]
SECTION 3 — The Results: [text with data]
SECTION 4 — What's Next: [text]

CTA: [text]
```

### Conference pitch narrative
```
OPENING LINE (30 sec): [text]
PROBLEM SETUP (60 sec): [text]
STAKES (30 sec): [text — what happens if unsolved]
SAT INTRODUCTION (60 sec): [text]
PROOF POINT (30 sec): [specific data or comparison]
DEMO ASK (30 sec): [text — what you want the audience to do]

Total runtime: ~4 min
```

### Gate
APPROVE STEP 22

---

## Step 23 — Design Annotations

### Agent actions
For assets delivered to a designer (landing pages, email templates, pitch decks),
provide explicit design annotations alongside the copy.

**Annotation format:**
```
[ANNOTATION for HEADLINE]
- Hierarchy: H1 — largest element above the fold
- Emphasis: [specific word(s) to emphasize if any]
- Max width: 600px (don't let it run full-width on desktop — breaks visual rhythm)
- No all-caps

[ANNOTATION for SUBHEAD]
- Hierarchy: H2 — secondary visual weight
- Line length: max 12 words per line (force a break at natural pause if needed)

[ANNOTATION for CTA BUTTON]
- Primary button style — high contrast against background
- Label: "[exact text]" — do NOT rewrite the label
- Position: directly below subhead, above the fold

[ANNOTATION for BODY COPY / PROPS]
- Line length: 60–75 characters max (optimize for readability)
- Spacing: 1.5× line height minimum
- No text over imagery — copy always on solid background or clear overlay

[ANNOTATION for SOCIAL PROOF]
- If logo: grey monochrome preferred (not colored logos that compete with CTA)
- If testimonial: quotation marks + name + title (not just name)
```

Also include:
- **Copy hierarchy map**: list the reading order the designer should reinforce with visual weight
- **Mobile check note**: flag any copy that might be too long for mobile breakpoint

### Gate
APPROVE STEP 23

---

## Step 24 — SEO Metadata (Web Copy Only)

### Agent actions
For any copy that will be published on a web page:

**Generate:**
1. **SEO Title** (≤60 characters) — includes primary keyword, matches headline intent
2. **Meta Description** (≤155 characters) — expands the SEO title with one proof point and CTA
3. **URL slug** — lowercase, hyphens, keyword-first
4. **H1 text** — (should match or closely align with the SEO title)
5. **Primary keyword** — the exact phrase this page targets in search
6. **Secondary keywords** — 2–3 supporting phrases

**Keyword note for SAT:**
Primary keywords to target for Indian market:
- "site analysis tool architects India"
- "solar analysis architecture software India"
- "flood risk analysis site India"
- "NBC compliance architecture tool"
- "passive design analysis software India"

Ask the human: "Is there a specific keyword this page should rank for? Or should I
suggest based on the content?"

### Output format
```
## SEO Metadata

SEO Title: [≤60 chars]
Meta Description: [≤155 chars]
URL Slug: /[slug]
H1: [text]
Primary keyword: [phrase]
Secondary keywords: [phrase 1], [phrase 2], [phrase 3]
```

### Gate
APPROVE STEP 24

---

## Step 25 — Copy Library Archive

### Agent actions
Archive the final approved copy asset to the copy library.

**Copy library location:** Ask the human: "Where should I save the final copy?
Options: (a) `/Volumes/LocalDrive/SAT/docs/copy-library/[asset-type]/` (b) Notion /
Confluence doc (c) other location"

**Archive record format:**
```markdown
---
asset: [type — landing page / email / case study / etc.]
persona: [Head of Design / BIM Head / Principal]
buying_stage: [Awareness / Consideration / Decision]
framework: [name]
features_referenced: [list]
status: [approved / draft / retired]
date_approved: [date]
approved_by: [human name]
sme_gates: [all clear / pending — list]
---

# [Asset name]

[Full final copy]

---
## Copy Rationale
[copy_rationale block]

## Performance Notes (update after publish)
- Published: [date]
- Channel: [where it ran]
- Metric: [what was tracked]
- Result: [outcome — fill after data available]
```

Ask the human to confirm the archive location. Do not create the file without confirmation.

### Gate (Phase Gate)
APPROVE PHASE 6
(Handoff complete. Copy archived. Workflow closed for this asset.)

---

## Phase 6 Completion Checklist

- [ ] Copy formatted for delivery channel (Step 22)
- [ ] Design annotations complete for designer handoff (Step 23)
- [ ] SEO metadata generated for web copy (Step 24 — or marked N/A)
- [ ] Copy archived to copy library with full record (Step 25)
- [ ] Human confirmed archive location (Step 25)
- [ ] Any open SME gates documented in the archive record
- [ ] Performance tracking note added for post-publish follow-up

---

## Copy Library Index Template

Maintain this index at the top of the copy library folder:

```
# SAT Copy Library

| Asset | Persona | Stage | Framework | Features | Date | Status |
|---|---|---|---|---|---|---|
| [type] | [persona] | [stage] | [framework] | [features] | [date] | [approved] |
```
