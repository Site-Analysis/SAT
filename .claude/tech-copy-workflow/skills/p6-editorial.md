# Phase 6 — Editorial
# Steps 21–24 | EPPO check, voice and tone, loading/microcopy final pass, clarity audit

## Phase Goal
Polish the copy without changing what it says. Editorial is not rewriting — it is refining. The draft's content is approved. This phase makes it perform at the sentence level.

---

## Step 21 — EPPO Check (Every Page Is Page One)

### Agent actions
Verify every section of the content is self-contained for a reader arriving cold.

**EPPO failure patterns:**
- "As described in the previous section..."
- "You'll remember from Step 2 that..."
- "The score you saw on the map earlier..."
- "This continues from the flood analysis tutorial."
- Opening a section with a pronoun whose referent is in a different section ("It calculates..." without naming the subject)

**EPPO fix patterns:**
- Start each section with a 1-sentence self-contained statement of what it covers
- Replace "the analysis above" with "the flood risk analysis"
- Replace "the previous step" with the specific step name or action
- For API docs: each endpoint description must stand alone — no cross-references to endpoints the reader may not have read

**EPPO check process:**
1. Read only one section at a time (cover the rest)
2. Ask: "Could a user who arrived here via search understand what this section is saying without having read anything else?"
3. Flag every failure; apply fixes

### Output format
```
## EPPO Audit

Sections checked: [N]
EPPO failures found: [N]

Failures and fixes:
- Section [name]: "[failing phrase]" → "[EPPO-compliant replacement]"
```

### Gate
APPROVE STEP 21

---

## Step 22 — Voice and Tone Check

### Agent actions
Read the full draft as if encountering SAT for the first time. Apply the voice constants from `style-guide.md`.

**Voice constant (never changes):**
"Precise, honest, technically fluent, architect-respecting."

**Tone check by user state:**
Read each section and identify the user's emotional state at that moment:
- Error states: is the tone calm and action-oriented? No "Oops!" No blame.
- Onboarding: is the tone warm and brief? No feature-list enthusiasm.
- Loading: is the tone matter-of-fact? No false reassurance.
- Help articles: is the tone efficient and direct? No filler padding.

**10 Plain Language Rules check (from style-guide.md):**
- [ ] Active voice: "SAT calculates" not "is calculated by SAT"
- [ ] "You" not "the user" or "users"
- [ ] Sentences ≤20 words (UI copy) / ≤25 words (articles)
- [ ] No nominalizations: "analyze" not "perform an analysis"
- [ ] Common words: "use" not "utilize", "show" not "display"
- [ ] Positive framing: "enter a valid coordinate" not "don't enter an invalid coordinate"
- [ ] No jargon without translation (check geospatial-glossary.md for any flagged terms)
- [ ] Main point first in every sentence and paragraph
- [ ] No redundant words: delete "currently", "in order to", "in the event that"
- [ ] One idea per sentence

**Banned word scan:**
Search for: "leverage", "utilize", "robust", "seamless", "intuitive", "cutting-edge", "powerful", "solution", "ecosystem", "actionable insights", "revolutionary", "game-changing", "world-class", "best-in-class", "state-of-the-art"

Flag any instances. Replace with specific, concrete language.

### Output format
```
## Voice and Tone Audit

Active voice: [PASS / N instances fixed]
"You" consistency: [PASS / N instances fixed]
Sentence length: [PASS / N sentences over limit, fixed]
Banned words: [PASS / list fixed]
Error state tone: [PASS / N/A]
Onboarding tone: [PASS / N/A]
```

### Gate
APPROVE STEP 22

---

## Step 23 — Loading Copy and Microcopy Final Pass

### Agent actions
Specific final checks for UI microcopy types.

**Loading copy:**
- [ ] Stages are sequenced from fast (data fetch) to slow (computation)
- [ ] Each stage names a specific computation or data source
- [ ] No "Loading...", "Please wait...", "Processing..."
- [ ] Final stage has a reassurance tone: "Almost there — finalizing [X]..."
- [ ] Timing approximations are plausible (cross-check against feature map from P2)

**Error messages:**
- [ ] P+C+S structure present and complete
- [ ] ≤25 words total
- [ ] Solution is an action the user can actually take (not "contact support" as the first option)
- [ ] Error does not use HTTP status codes in user-facing message

**Button labels:**
- [ ] Action verb + specific outcome format
- [ ] Consistent across the feature (if "Run Analysis" is used for flood, same verb pattern for wind)
- [ ] No label truncation risk on mobile (≤3 words preferred; max 5 words)

**Tooltips:**
- [ ] Type 2a: has value interpretation (what does a high score mean for me?)
- [ ] Type 2b: action + how-to
- [ ] Both types: ≤30 words

**Empty states:**
- [ ] Pre-action version present (before feature is run)
- [ ] No-data version present (if data coverage can vary)
- [ ] CTA is specific (not "Get started" — use "Draw your site boundary" or "Run flood analysis")

### Output format
```
## Microcopy Final Pass

Loading copy: [PASS / issues fixed]
Error messages: [PASS / issues fixed]
Button labels: [PASS / issues fixed]
Tooltips: [PASS / issues fixed]
Empty states: [PASS / issues fixed]
```

---

## Step 24 — Final Clarity Audit

### Agent actions
One final read-through for clarity only. Ask: "Is there any sentence a reader might need to read twice?"

**Clarity killers to fix:**
- Ambiguous pronoun references ("It shows the score" — what is "it"?)
- Nested qualifications ("The analysis, which runs in 5–10 seconds depending on boundary size, calculates the flood risk...")
- False precision ("approximately 3.7 seconds")
- Implicit assumptions ("Click the export button" — where is it?)
- Missing context in error messages ("Try again" — when? how?)

**Final read test:** Read the copy aloud. Any sentence where you pause, stumble, or need to re-read: rewrite it.

### Output format
```
## Final Clarity Audit

Clarity issues found: [N]
Issues fixed: [list before/after]

Final draft: [clean copy — no markup, no annotations, ready for publishing]
```

### Gate (Phase Gate)
APPROVE PHASE 6
(Editorial complete. Copy polished and ready for P7 Publish.)

---

## Phase 6 Completion Checklist

- [ ] EPPO check done — all sections self-contained
- [ ] Voice check done — active, direct, "you", no banned words
- [ ] Tone check done — appropriate to user's emotional state
- [ ] Loading copy final pass — stages named, timed plausibly
- [ ] Error messages final pass — P+C+S complete, ≤25 words
- [ ] Button labels final pass — action verb + specific outcome
- [ ] Tooltips final pass — typed and within length
- [ ] Empty states final pass — both versions present where applicable
- [ ] Final clarity audit done — no sentences requiring two reads
- [ ] Clean final draft ready — no markup, no brackets, no corrections visible
