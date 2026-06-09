# Technical Copywriter Gate Protocol

Gates prevent publishing unverified technical claims, coordinate errors, and content for unbuilt features.
Same philosophy as the copy workflow — different triggers.

---

## Gate Phrase Convention

**Step gates:**
```
APPROVE STEP [N]
```

**Phase gates (end of each phase):**
```
APPROVE PHASE [N]
```

**SME gates (technical accuracy holds):**
```
SME APPROVED — [claim]
```

Human must type one of these exact phrases to proceed. Agent must not auto-advance.

---

## Gate Positions by Phase

| Phase | Gate | What it locks |
|---|---|---|
| P1 Brief | APPROVE PHASE 1 | Content type, audience, Diataxis quadrant, feature status confirmed |
| P2 Discovery | APPROVE PHASE 2 | Spec reading done, SME questions queued, data sources identified |
| P3 Architecture | APPROVE PHASE 3 | Doc structure + information hierarchy confirmed |
| P4 Draft | APPROVE PHASE 4 | Final draft written, coordinate check done, F-K score checked |
| P5 SME Review | APPROVE PHASE 5 | All SME gates resolved (or documented as pending) |
| P6 Editorial | APPROVE PHASE 6 | EPPO + voice + clarity pass complete |
| P7 Publish | APPROVE PHASE 7 | Formatted, changelog entry written, archived |

---

## SME Gate Protocol

When an SME gate is triggered, the agent must:

1. **Clearly mark the unverified claim** in the draft with `[SME REVIEW REQUIRED: {specific question}]`
2. **List all open SME gates** at the end of the phase output
3. **Refuse to advance to P7 Publish** while any SME gate is open
4. **Document gate resolution** — when `SME APPROVED` is received, note which claim it closes and by whom

Example SME gate in draft:
```
SAT calculates flood risk from MERIT DEM elevation data at 90m resolution
[SME REVIEW REQUIRED: confirm 90m resolution for India coverage]
```

After `SME APPROVED` received:
```
✅ SME APPROVED by [name] on [date]: MERIT DEM India resolution confirmed at 90m
```

---

## Quick-Task Exception

For single-piece requests (one tooltip, one error message, one button label, one empty state):

**Compressed flow:** P1 + P4 + P6 in one response. No step gates.

**Still required:**
- `tech_copy_rationale` block in the output
- Coordinate warning if applicable
- Technical Risk flag if any claim needs verification
- Human approval before archiving

**Not required:**
- Separate phase gates between P1/P4/P6
- Full phase documentation

**Quick-task threshold:** request specifies ≤3 content pieces of the same type.
If the request spans multiple types or a full feature doc suite, run full workflow.

---

## Blocked at Gate: What Agent Does

If a gate is not approved (human says "no", "wait", or provides corrections):

1. Acknowledge the correction specifically
2. Revise the flagged element only — do not rewrite unrelated copy
3. Re-present the updated section
4. Re-offer the gate

Do not ask "are you sure?" Do not re-pitch the original copy. Apply the feedback and move forward.

---

## SME Gate vs. Human Gate

| Gate type | Who approves | When required |
|---|---|---|
| Phase gate | Human (copywriter's manager / stakeholder) | End of every phase |
| SME gate | Engineer / domain expert | Before any technical accuracy claim publishes |
| Regulatory gate | Architecture SME + project lead | Before any specific NBC/ECBC/bylaw claim publishes |

**A phase gate does not substitute for an SME gate.** A human can approve a phase while SME gates remain open — in that case, copy status is "APPROVED - SME PENDING" and cannot publish until SME gates resolve.
