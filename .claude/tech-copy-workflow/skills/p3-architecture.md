# Phase 3 — Architecture
# Steps 9–11 | Information hierarchy, doc structure, progressive disclosure map

## Phase Goal
Plan the structure before writing. A well-structured outline takes 15 minutes; a structural rewrite after drafting takes 2 hours. For technical content, structure IS the user experience.

---

## Step 9 — Information Hierarchy

### Agent actions
Determine what information the user needs and in what order they need it.

**Hierarchy principle:** Lead with the most important, most frequently needed information. Supporting detail follows.

**By content type:**

**Onboarding modal:**
```
1. What the feature produces (the outcome they care about)
2. Why it matters for their specific work
3. How to start (single action)
```

**Tooltip:**
```
Type 2a (data field): 1. What it measures → 2. The scale/unit → 3. What the number means for their decision
Type 2b (UI control): 1. What it does → 2. How to use it
```

**Error message:**
```
1. What failed (P)
2. Why (C)
3. Fix (S)
```

**Help article (How-To):**
```
1. What this article helps you do (≤2 sentences — EPPO: self-contained intro)
2. Prerequisites (if any)
3. Steps (numbered, sequential)
4. Expected result
5. Troubleshooting / next steps (if needed)
```

**Help article (Explanation):**
```
1. The key concept or question this article answers (≤2 sentences)
2. The mental model
3. How SAT applies it
4. What it means for the reader's work
5. Related How-To links
```

**API endpoint doc:**
```
1. What this endpoint does (one sentence)
2. Request — method, URL, parameters, example
3. Response — success fields, example
4. Error codes — code, meaning, fix
5. GeoJSON coordinate note (if applicable)
```

**Technical blog:**
```
1. Hook — a specific problem, data point, or question
2. The insight — the key knowledge
3. SAT's application or solution
4. The takeaway
5. Soft CTA
```

### Output format
Present the hierarchy as a numbered list matching the content type. This becomes the writing order in P4 Draft.

### Gate
APPROVE STEP 9

---

## Step 10 — Doc Structure Outline

### Agent actions
Write the full structural outline — headings, subheadings, and purpose notes for each section. No copy yet.

**Heading quality check:**
- Help article headings: describe what the section covers, not generic labels ("How to draw your site boundary" not "Step 3")
- API doc headings: match OpenAPI naming conventions (`## POST /flood/analyze`, not "Flood Endpoint")
- Technical blog headings: active, specific, intriguing (not "Introduction", "Conclusion")

**EPPO check on the outline:**
At this stage, verify the article can be read starting from any section without requiring context from a previous section. If any section depends on prior reading, add a brief self-contained intro sentence to that section in the outline note.

**Example output for a help article:**
```
## How to Export Flood Risk Analysis Results as GeoJSON

### Overview [self-contained: who this is for + when to use]
### Before you start [prerequisites]
### Step 1: Run the flood analysis [desc: drawing the boundary]
### Step 2: Review the results [desc: reading the score + map]
### Step 3: Export as GeoJSON [desc: where the button is, what downloads]
### What the GeoJSON contains [desc: field definitions for developers who receive it]
### Troubleshooting [desc: 3 most common issues with recovery actions]
```

### Gate
APPROVE STEP 10

---

## Step 11 — Progressive Disclosure Map

### Agent actions
Map which information appears at which layer of the UI, and what links bridge layers.

Progressive disclosure rule: essential insight at the surface. Methodology and detail behind "Learn more."

**Layer definitions for SAT:**

| Layer | What appears here | Copy type |
|---|---|---|
| UI result panel | Score / chart / map | Label + unit only. No methodology. |
| Tooltip (hover) | Plain-English translation of the metric | 1–2 sentences. |
| Help article | How to use the result | Step-by-step, methodology-light |
| Explanation article | How SAT calculated it | Full methodology, data source |
| Developer docs | Technical specification | Complete, reference-grade |

**For the current content piece:**
Map where the copy being written sits in this hierarchy, and identify what links it should carry to adjacent layers.

**Example (Flood Risk Score tooltip):**
```
Layer 1 (UI): "Flood Risk: 72/100" — no copy, just the value
Layer 2 (this tooltip): "SAT's 4-component flood risk score for your site. Higher = greater risk."
→ Link: "What does this score mean?" → Explanation article
→ Link: "How to read the flood risk map" → How-To article
```

Produce a progressive disclosure map for every piece of content being written.

### Output format
```
## Progressive Disclosure Map — [Feature/Content]

Current layer: [Layer 1–5 from table above]
This content contains: [what's here]
Link to deeper layer: [text + destination]
Link to related layer: [text + destination]
What must NOT appear here (belongs to a deeper layer): [list]
```

### Gate (Phase Gate)
APPROVE PHASE 3
(Structure locked. Information hierarchy, outline, and progressive disclosure map approved. Proceed to P4 Draft.)

---

## Phase 3 Completion Checklist

- [ ] Information hierarchy defined — matches content type requirements
- [ ] Full structural outline written — headings + purpose notes
- [ ] EPPO check done — each section self-contained
- [ ] Progressive disclosure map complete — knows what links to include
- [ ] Knows what NOT to include (content that belongs to a different layer)
- [ ] No writing started (outline only — writing begins in P4)
