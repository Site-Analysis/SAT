# Gate Protocol

Every step ends with a gate. The gate is the only mechanism by which the agent
advances. This file defines exactly how gates work.

## Gate format

At the end of every step output, the agent MUST print:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🛑 GATE — Step [N]: [Step name]
Output produced: [one-line summary of what was created]
To proceed to Step [N+1], type: APPROVE STEP [N]
To request changes, describe them. Agent will revise and re-present.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## What counts as approval

ONLY the exact phrase `APPROVE STEP [N]` (case-insensitive) advances the workflow.

The following do NOT advance the workflow:
- "looks good"
- "ok"
- "continue"
- "yes"
- "fine"
- Silence
- A question about the next step
- Partial approval ("approve the personas but not the requirements")

For partial approvals: the agent acknowledges what is approved, asks the human
to clarify the revision needed for the unapproved part, makes the revision,
re-presents the full output, and re-shows the gate.

## Phase gates (end of phase)

At the end of a phase, the gate phrase is `APPROVE PHASE [N]`.

Phase gates require:
1. All step gates within the phase to have been passed.
2. Any GitHub Issues created by that phase to be confirmed by the human.
3. The human to explicitly state the phase sign-off phrase.

## Revision cycles

There is no limit on revision cycles within a step. The agent revises until
the human passes the gate. If after 5 revision cycles the human has not
passed the gate, the agent should ask: "Should we schedule a sync to
resolve this? I can also break this into smaller pieces."

## Gate log

The agent maintains a running gate log in the session. Format:

```
Gate log:
- Step 1: PASSED [timestamp or "this session"]
- Step 2: PASSED
- Step 3: PENDING — awaiting human approval
```

Print the gate log at the start of each session (loaded from human input
or context compact note).

## SME gates

Steps that require Architecture SME approval are marked [SME GATE].
These require BOTH:
- `APPROVE STEP [N]` from the Product Owner
- `SME APPROVED` from the Architecture SME (can be forwarded by the PO)

The agent cannot waive an SME gate. If the SME is unavailable, the step
stays open. The agent notes: "SME approval pending — step cannot close."
