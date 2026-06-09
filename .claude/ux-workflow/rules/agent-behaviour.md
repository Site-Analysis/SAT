# Agent Behaviour Rules

IMPORTANT: These rules override everything else. No phase instruction, no human
request, and no apparent efficiency gain ever overrides these.

## The five absolutes

1. **Never advance past a gate without explicit human sign-off.**
   A gate is passed only when the human types an explicit approval phrase
   (see gate-protocol.md). Silence, partial review, or "looks good" without
   the gate phrase does NOT count.

2. **Never assume a missing input.**
   If a step requires human input and it has not been provided, STOP and ask.
   Do not infer, estimate, or proceed with a placeholder. Ask the exact
   questions listed in the step. One question at a time if multiple are needed.

3. **Never fabricate research data.**
   Personas, pain points, requirements, and observations must trace to approved
   transcripts or explicit human input. If you cannot cite the source, do not
   include the claim. Say "I cannot find evidence for this in the approved
   transcripts" instead.

4. **Never batch steps.**
   Execute one step at a time. Present the output of that step. Wait for the
   gate to be passed before starting the next step. Even if steps seem
   sequential and fast, do not chain them without human approval between each.

5. **Never modify Figma after design freeze without a GitHub Issue reference.**
   After Step 29 (design freeze), every Figma change requires the human to
   provide a GitHub Issue number first. The agent opens the issue, confirms
   it exists, then makes the change. No exceptions.

## Efficiency rules (what the agent SHOULD do)

- Be terse in status updates. One sentence confirming what was done is enough.
- Do not re-explain rules the human already knows. State the action, show the
  output, state the gate.
- When generating artifacts (wireframes, personas, reports), show them
  immediately — do not describe what you are about to generate first.
- Use the exact output format specified in each step. Do not add sections,
  caveats, or commentary unless the step asks for it.
- When GitHub Issues need creating, batch the full list for human review first,
  then create on approval — do not create one at a time without prior review.

## What to do when stuck

If you are unsure what to do:
1. State what you know: the current step number and what its output should be.
2. State what is missing: the exact input you need.
3. Ask one specific question. Wait.
Never guess and proceed.

## Context window management

- Load only the current phase skill file. Unload previous phases by not
  referencing them.
- When context compacts, preserve: current step number, last gate status,
  approved artifacts list, and any open GitHub Issue numbers.
- Compact note to prepend: "SAT Workflow — Phase [N] Step [N] — Last gate:
  [PASSED/PENDING] — Approved artifacts: [list]"
