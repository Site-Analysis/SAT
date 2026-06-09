# Phase 4 — Draft
# Steps 12–16 | Write by quadrant, microcopy patterns, GeoJSON check, F-K check, India alignment

## Phase Goal
Write the copy. Every word against the locked brief (P1), discovered specs (P2), and approved structure (P3). No structural decisions during drafting — only language decisions.

---

## Step 12 — Draft by Diataxis Quadrant

### Agent actions
Apply the quadrant-specific writing rules from P1 to the outline from P3.

**Tutorial drafting rules:**
- Use "you" — direct address throughout
- Numbered steps, short sentences, one action per step
- Tone: warm, present-tense imperative ("Click the boundary tool", not "You will need to click...")
- Stop when the tutorial goal is achieved — no extending scope
- No jargon that wasn't pre-translated in the step before it was needed

**How-To Guide drafting rules:**
- Start with a brief statement of the goal — EPPO opener
- Steps are short, task-focused (≤20 words per step)
- Prereqs up front
- Include expected outcome for each step where non-obvious
- No explanatory asides mid-step — those belong in the Explanation quadrant; link to them

**Reference drafting rules:**
- Tables, lists, code blocks preferred over prose
- No narrative — information density > readability (this audience tolerates density)
- Every entry complete and accurate — no approximations
- For API docs: every field must have type + required flag + plain description + example value
- GeoJSON coordinate warning in every endpoint that accepts or returns geographic data

**Explanation drafting rules:**
- Start with the mental model (the concept the user will understand after reading)
- Use analogies where helpful — but only analogies that are accurate, not just convenient
- Avoid "in order to understand X, you need to first understand Y, which requires understanding Z" chains — EPPO applies
- End with: what this means for the reader's specific work (not a general conclusion)

### Output format
Write the full draft section-by-section per the approved outline. Present one section at a time for complex docs; single response for short content types.

---

## Step 13 — Microcopy Pattern Application

### Agent actions
For UI copy (onboarding, tooltips, errors, empty states, loading), apply the patterns from `style-guide.md` systematically.

**Checklist as you write:**

**Error messages:**
- [ ] Contains Problem (P): describes what failed
- [ ] Contains Cause (C): explains why, specifically
- [ ] Contains Solution (S): tells them what to do
- [ ] Total ≤25 words
- [ ] Tone is calm — no blame, no apology ("Oops!")
- [ ] No technical jargon in the problem or solution (OK in cause if needed for precision)

**Empty states:**
- [ ] Distinguishes pre-action from no-data
- [ ] Pre-action: includes the value proposition + how to start
- [ ] No-data: specifies why (data coverage, location, etc.) + what to try instead

**Loading copy:**
- [ ] Names the specific computation or data source
- [ ] Progresses through stages (not static)
- [ ] Stage timing is plausible (matches feature map from P2)

**Tooltips:**
- [ ] Classified as Type 2a (data) or Type 2b (UI control) — not mixed
- [ ] Type 2a: has scale/unit + meaning for their decision
- [ ] Type 2b: has action + how-to

**Buttons:**
- [ ] Action verb + specific outcome
- [ ] No generic labels (Submit, OK, Done, Generate)

**Onboarding modals:**
- [ ] Screen 1: what + why (outcome-first, not feature-list)
- [ ] Screen 2: how to start (one action)
- [ ] Screen 3: CTA only
- [ ] Skip button on all screens
- [ ] No more than 3 screens

---

## Step 14 — GeoJSON Coordinate Verification

### Agent actions
If the content includes any geographic coordinate, GeoJSON example, bounding box, or coordinate parameter description: verify [Lon, Lat] order before presenting the draft.

**Coordinate check:**
```
⚠️ Coordinate Check:
Examples used in this draft:
- [77.5946, 12.9716] → Bengaluru → [Lon, Lat] ✅ CORRECT
- [72.8, 8.4, 97.4, 37.6] → India bbox → [minLon, minLat, maxLon, maxLat] ✅ CORRECT
```

If any example has incorrect [Lat, Lon] order: correct it immediately and note the correction.

For API docs: every coordinate parameter must include an explicit note:
```
coordinates: [Longitude, Latitude]  // not [Lat, Lon] — see GeoJSON RFC 7946
```

For developer-facing error messages about coordinates: the correction itself should show the right order.

### Output format
Include the coordinate check block at the end of the draft if any coordinates appear.

---

## Step 15 — Flesch-Kincaid Self-Check

### Agent actions
Before presenting the draft, self-assess readability against the targets from `style-guide.md`.

**Approximate self-check method (no tool required):**
- Sentence length: average ≤15 words for UI copy, ≤20 for articles
- Word syllables: majority 1–2 syllables; flag any sentence where 3+ syllable words cluster
- Active voice: >90% of sentences (passive voice is a readability cost)

**Target by content type (from style-guide.md):**
| Content type | Target F-K score |
|---|---|
| Onboarding / error / empty | 70–80 (6th–8th grade) |
| Tooltips | 65–75 (7th–8th grade) |
| Help articles | 50–65 (9th–10th grade) |
| API docs | 40–55 (11th grade) |
| Technical blog | 45–60 (10th–11th grade) |

**Common readability drains to fix:**
- Nominalizations: "perform an analysis" → "analyze"
- Passive: "the score is calculated" → "SAT calculates the score"
- Long prepositional chains: "in the event that" → "if"
- Buried verbs: "make a selection of" → "select"

Self-assess and revise before presenting. Do not present copy you already know fails the readability target.

---

## Step 16 — India Context Check

### Agent actions
For any content that will be user-facing in the SAT product (not developer API docs):

**Check 1 — India-relevant examples:**
All cities, firms, locations, and regulatory references must be Indian.
- Coordinates: use Indian cities (Bengaluru: 77.59°E, 12.97°N; Mumbai: 72.87°E, 19.07°N; Delhi: 77.22°E, 28.63°N; Chennai: 80.27°E, 13.08°N)
- Regulatory references: NBC 2016, ECBC 2017, BBMP/BDA — not IBC, ASHRAE, or US/EU standards
- Firm names in examples: use Indian architectural firms or generic "your firm"

**Check 2 — Regulatory terminology accuracy:**
If the content references an Indian regulatory standard, the phrasing must be:
- Specific to the standard version (NBC 2016, not "National Building Code")
- Specific to the right metric if named
- Verified against Step 7 SME queue — is this claim pending SME verification?

**Check 3 — Climate context accuracy:**
India has 5 major climate zones (hot-dry, warm-humid, composite, temperate, cold) — SAT content referencing climate recommendations must not imply a single recommendation applies India-wide.

Example of wrong framing: "Optimal window orientation for Indian climate is north-facing."
Example of correct framing: "In hot-dry climates (Rajasthan, Gujarat), north-facing orientation reduces solar heat gain..."

### Output format
```
## India Context Check

City examples: [PASS / corrections made]
Regulatory terminology: [PASS / [SME gate opened for claim X]]
Climate zone accuracy: [PASS / N/A / correction made]
```

### Gate (Phase Gate)
APPROVE PHASE 4
(Draft complete. Coordinate verified, readability checked, India context confirmed. Proceed to P5 SME Review.)

---

## Phase 4 Completion Checklist

- [ ] Full draft written per approved outline (P3)
- [ ] Microcopy patterns applied (P+C+S errors, empty states, loading stages, button labels)
- [ ] GeoJSON coordinate check done — all examples are [Lon, Lat]
- [ ] Flesch-Kincaid self-check done — copy meets target for content type
- [ ] India context check done — Indian city examples, correct regulatory terminology
- [ ] No unfilled placeholders or [METRIC NEEDED] brackets in final draft
- [ ] `<tech_copy_rationale>` block present at end of draft
- [ ] Technical Risk flags noted for SME review in P5

---

## Required Output Block

End every P4 Draft with:

```
<tech_copy_rationale>
Content type: [name]
Diataxis quadrant: [name]
Audience: [architect / developer / internal]
Cognitive state: [description]
Data sources used: [list]
Geospatial constraints: [coordinate order confirmed / N/A]
Plain language choices: [key simplifications made from technical spec language]
Pending SME verifications: [list claims flagged for P5 review, or "none"]
</tech_copy_rationale>
```
