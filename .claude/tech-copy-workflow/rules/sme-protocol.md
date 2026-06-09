# SME Protocol — Technical Copywriter

SME (Subject Matter Expert) interrupts are expensive. Engineers have full calendars.
This protocol ensures every SME interaction is efficient, binary, and batched.

---

## When to Escalate vs. Proceed

### Proceed without SME when:
- The claim is documented in a Feature Validation Document (FVD)
- The claim is in the agent's context files (geospatial-glossary.md has the fact)
- The claim is publicly documented by the primary source (NREL docs, JRC dataset descriptions)
- The content type is non-technical microcopy (button labels, empty states, loading copy)
- The claim is about process, not accuracy (e.g., "SAT queries Open-Meteo for temperature data")

### Escalate to SME when:
- Accuracy figures are required (e.g., "±0.0003°", "90m resolution") and not in FVD
- Coverage scope is claimed ("any location in India", "all urban areas") and not in FVD
- Algorithm internals are described beyond what FVDs document
- Regulatory standard clause is cited (any specific NBC/ECBC/bylaw number)
- API parameters, defaults, or validation rules are being documented
- An error code's behavior or trigger condition is being described
- A feature interaction is described that could have changed since FVD was written

---

## Binary Question Format

Never ask open-ended questions. Open-ended questions result in multi-paragraph answers that require re-interpretation.

**Wrong:**
```
❌ "How does the flood analysis work?"
❌ "Can you explain the MERIT DEM integration?"
❌ "What accuracy can we claim for the solar analysis?"
```

**Right:**
```
✅ "Does the flood analysis use MERIT DEM or ALOS DEM for Indian sites? [A: MERIT / B: ALOS / C: both]"
✅ "Is the NREL SPA accuracy ±0.0003° or ±0.003°? [check: SAT-04 FVD says ±0.0003° — confirm]"
✅ "Is the 90m MERIT DEM resolution the same across all Indian states, or does it vary by region?"
```

Format template:
```
[Question] [specific claim or source to verify against] [expected answer options if binary]
```

---

## Batching Protocol: Max 3 Per Interrupt

Never send more than 3 questions per SME interrupt.

**Why:** more than 3 questions = lower response rate + vague answers. SMEs prioritize short, answerable asks.

**Batching strategy:** collect all SME questions during P2 Discovery and P4 Draft, then send the 3 most critical before proceeding.

**Queue management:**
```
SME Queue (session):
Q1 (critical): [question]
Q2 (critical): [question]
Q3 (high): [question]
Q4 (medium — hold for next interrupt): [question]
```

Present the queue to the human at the end of P2 Discovery. Human decides which to escalate.

---

## SME Gate Resolution Logging

When SME APPROVED is received:

```
## SME Gate Log

| Date | Claim | Question | SME response | Approved by |
|---|---|---|---|---|
| 2026-06-09 | "90m resolution" | "MERIT DEM India resolution?" | "Confirmed 90m" | [name] |
```

Keep this log in the P5 SME Review output. It becomes part of the publish record.

---

## What "SME APPROVED" Means

**SME APPROVED for [specific claim]** — that claim is cleared for publish.

**SME APPROVED** (blanket) — entire draft is cleared. Agent can proceed to P7.

If SME response modifies the claim (e.g., "it's 90m in most regions but 30m available via Copernicus"), update the draft accordingly and re-present the modified claim before proceeding.

**Do not assume SME approval = unlimited approval.** Approval covers the specific draft at the time of review. If content changes after SME review, re-flag the changed sections.

---

## SME Availability Fallback

If an SME is not available within the session:

1. Mark all unverified claims with `[PENDING SME: {question}]` in the draft
2. Set content status to "DRAFT — NOT PUBLISHABLE — pending [N] SME gates"
3. Document the pending gates in the P5 review output
4. Provide the publish-ready draft with placeholders so no work is lost when SME responds
5. Never push content to publish state while SME gates are open

Human is responsible for SME escalation outside the agent workflow. The agent tracks and surfaces; it does not chase SMEs directly.
