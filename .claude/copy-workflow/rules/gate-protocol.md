# Copy Workflow — Gate Protocol

Identical in structure to the UX workflow gate protocol. Adapted for copy-specific
review stages.

---

## Gate Format

At the end of every step output, the agent MUST print:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛑 GATE — Step [N]: [Step name]
Output produced: [one-line summary]
To proceed to Step [N+1], type: APPROVE STEP [N]
To request changes, describe them. Agent will revise and re-present.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## What Counts as Approval

ONLY the exact phrase `APPROVE STEP [N]` (case-insensitive) advances the workflow.

These do NOT advance the workflow:
- "looks good"
- "ok / sure / fine"
- "continue"
- "yes"
- Silence
- A question about the next step
- Emoji reactions

For partial approvals (e.g., "approve headline 2 but not the CTA"): acknowledge what
is approved, ask for clarification on the revision, make the change, re-present the
full step output, re-show the gate.

---

## Phase Gates

At the end of a phase, the gate phrase is `APPROVE PHASE [N]`.

Phase gates require:
1. All step gates within the phase to have been passed.
2. Human confirmation that any copy delivered in that phase is saved to the copy library.
3. Explicit phase sign-off phrase.

---

## SME Gates (Regulatory Copy)

Steps that include specific regulatory claims (NBC 2016, ECBC 2017, BBMP, Auto-DCR)
are marked `[SME GATE]`. These require:
- `APPROVE STEP [N]` from the Product Owner
- `SME APPROVED` from the Architecture SME confirming regulatory accuracy

The agent cannot waive an SME gate. If SME is unavailable:
"SME review pending — this copy cannot be published until Architecture SME confirms
the regulatory claims in Step [N]."

---

## Revision Cycles

No limit on revision cycles within a step. Agent revises until gate is passed.

After 5 revision cycles without gate passage, the agent asks:
"We've revised this 5 times. Should I approach it from a different angle or framework?
Or would it help to revisit the brief at Step 1?"

---

## Gate Log

The agent maintains a running gate log:

```
Gate log:
- Step 1: PASSED
- Step 2: PASSED
- Step 3: PENDING — awaiting approval
```

Print the gate log at the start of each session.

---

## Quick-Task Exception

For single-asset quick tasks where the full 6-phase workflow is not invoked:
- Compress P1+P4+P5 into a single response
- Still output `<copy_rationale>` and `> ⚠️ Brand Risk:` as applicable
- No gate required — human approves or requests revision conversationally
- Document the approved output in the copy library before closing the task
