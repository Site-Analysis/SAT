# Phase 2 — Discovery
# Steps 5–8 | Spec ingestion, feature mapping, SME question preparation, data source identification

## Phase Goal
Understand the feature technically before writing a single word of copy. Technical copy written without discovery produces generic text that misses edge cases and invents claims. Discovery prevents both.

---

## Step 5 — Spec and Code Ingestion

### Agent actions
Read every available source about the feature before writing.

**Priority order for reading:**

1. **Feature Validation Document (FVD)** — if exists at `/Volumes/LocalDrive/SAT/docs/feature-validation/`
   - Read the full FVD. Note: the acceptance criteria, data sources, accuracy specs, and any known limitations.
   
2. **Backend service code** — if the feature has a live backend service, read the relevant endpoint:
   - `/Volumes/LocalDrive/SAT/` → find the relevant service (sunpath/8001, flood/8002, temperature/8000, wind/8003, rainfall/8004)
   - Read the endpoint handler and schema definitions
   
3. **Frontend code** — if writing UI microcopy, read the component that will display the copy:
   - Understand what data the component receives and in what states it can appear (loading, success, error, empty)

4. **Existing documentation** — read any existing help center articles or technical docs on this feature to understand what already exists and avoid duplication

**Note what you find:**
```
## Spec Ingestion Notes

FVD: [path or "not found"]
Key technical claims in FVD: [list]
Data sources identified: [list]
Accuracy specs (if any): [list]
Known limitations: [list]
```

---

## Step 6 — Feature Mapping

### Agent actions
Map every user-visible surface of the feature that requires copy.

**Mapping dimensions:**

**Inputs (what the user provides):**
- What parameters does the user set? (boundary, date, time, building type, etc.)
- What format must inputs be in? (GeoJSON, decimal degrees, ISO 8601, etc.)
- What are the valid ranges? (lat 8.4–37.6°N for India, etc.)
- What happens if inputs are invalid? (→ error states map)

**Processing (what SAT does):**
- What data sources are queried?
- What computation is performed? (brief — enough to write loading copy)
- How long does it typically take? (informs loading copy stages)

**Outputs (what the user sees):**
- What result surfaces? (number, map, chart, downloadable file)
- What is the output format? (score 0–100, GeoJSON, JSON object, CSV)
- What does a successful result look like? (informs success state copy and result tooltips)

**Error states (what can go wrong):**
- Network timeout → loading copy recovery
- Data unavailable for location → no-data empty state
- Invalid input → input error message
- Server error → generic error with recovery action
- Rate limiting or quota exceeded → API error (developer docs)

**Empty states:**
- Pre-action: feature exists but analysis not yet run
- No-data: analysis ran, no data for this location

### Output format
```
## Feature Map — [Feature name]

Inputs:
- [field]: [format] [valid range]

Loading stages:
1. [data source query 1] — ~[N]s
2. [computation] — ~[N]s

Output:
- [result type]: [format/range/what it means]

Error states:
- [condition]: [cause] → [recovery action]

Empty states:
- Pre-action: [trigger condition]
- No-data: [trigger condition + typical cause]
```

---

## Step 7 — SME Question Preparation

### Agent actions
Identify every technical claim that cannot be verified from the FVD, spec, or code reading, and prepare them as binary questions.

**For each gap:**
- What claim does the copy need?
- What source would verify it?
- Can it be inferred from available docs?
- If not: write a binary SME question

**Binary question format:**
```
Q: [Specific claim to verify] — [confirm/deny/specify]
Context: [what the copy will say if true; what the fallback is if false]
Source check: [FVD section, code file, or "not found" — reason I can't self-verify]
```

**Queue all questions. Rank by criticality:**
- Critical: claim will be false/misleading if wrong — cannot write copy until resolved
- High: claim affects technical accuracy but has a safe fallback phrase
- Medium: claim adds precision but isn't wrong if absent

Present the top 3 critical/high questions to the human for escalation. Hold medium questions for later phases.

**Recall batch limit:** max 3 per SME interrupt (see sme-protocol.md).

### Output format
```
## SME Question Queue

Critical (blocking):
Q1: [question] | Context: [impact] | Source: [checked, not found]

High (preferred but has fallback):
Q2: [question] | Context: [impact] | Fallback: [safe alternative phrase]

Medium (hold):
Q3: [question] | Context: [impact]
```

### Gate
APPROVE STEP 7
(Human decides which questions to escalate to SME before P4 drafting begins.)

---

## Step 8 — Data Source Identification

### Agent actions
For each data source used by this feature, retrieve the copy-safe translation from `geospatial-glossary.md`.

**For each data source:**
1. Look up the entry in `context/geospatial-glossary.md`
2. Note the copy-safe phrase for user-facing content
3. Note the technical name for developer-facing content
4. Note any "do not say" warnings

If a data source is used by this feature but NOT in the glossary: flag it as a glossary gap. Do not invent a translation.

### Output format
```
## Data Source Map — [Feature name]

| Technical name | Copy-safe phrase (user-facing) | Technical name (developer-facing) | Limitations |
|---|---|---|---|
| MERIT DEM | "bare-earth elevation data" | MERIT DEM | 90m resolution |
| [source] | [phrase] | [name] | [limit] |
```

### Gate (Phase Gate)
APPROVE PHASE 2
(Discovery complete. Feature mapped, data sources identified, SME questions queued. Proceed to P3 Architecture.)

---

## Phase 2 Completion Checklist

- [ ] FVD read (or flagged as absent)
- [ ] Backend/frontend code read (if relevant to content type)
- [ ] Feature fully mapped: inputs, loading stages, outputs, error states, empty states
- [ ] SME question queue prepared and ranked
- [ ] Top 3 questions presented to human for escalation
- [ ] Data sources mapped to copy-safe phrases
- [ ] No data source used without glossary entry (or gap flagged)
