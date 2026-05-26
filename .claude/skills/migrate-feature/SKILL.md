---
name: migrate-feature
description: One-shot feature migration from the Site Analysis review workspace to the SAT monorepo. Usage: /migrate-feature <service-name>. Invokes feature-reviewer first (in source workspace), then feature-migrator (in SAT).
trigger: /migrate-feature
---

# /migrate-feature

Migrate one feature from `/Volumes/LocalDrive/Site Analysis/` to `/Volumes/LocalDrive/SAT/`.

## Usage

```
/migrate-feature <service>
```

Where `<service>` is one of: `temperature`, `sunpath`, `flood`, `wind`, `geo`.

## What this skill does

1. **Pre-flight checks** in SAT:
   - Working tree clean
   - On `main` branch
   - FVD exists at `docs/feature-validation/SAT-XX_<service>*.md`
   - Contract YAML exists or will be created

2. **Source review** (in `/Volumes/LocalDrive/Site Analysis/`):
   - Spawn `feature-reviewer` agent
   - Report any blockers — STOP if NOT READY
   - Apply fixes if user authorizes

3. **Migration** (in `/Volumes/LocalDrive/SAT/`):
   - Spawn `feature-migrator` agent
   - Branch: `feat/<service>-service`
   - Logical commits: contracts → flag → service → docker → tests → frontend
   - Open PR

4. **Validation**:
   - Wait for CI
   - Report PR URL + CI status to user
   - User merges after manual validation

## Hard rules

- **One service per invocation.** Don't bundle.
- **Never push to main.** PR always.
- **Never enable flag by default.** Always off.
- **Never skip the review step.** No "I know this code, skip review."

## Output

End with:
```
PR: <url>
Branch: feat/<service>-service
Status: <CI pending|passed|failed>
Files changed: <count> in <N> commits
Next: <user action>
```

## Underlying agents

This skill orchestrates two agents:
- `feature-reviewer` (lives in Site Analysis workspace `.claude/agents/`)
- `feature-migrator` (lives in SAT workspace `.claude/agents/`)

If those agents aren't available, fall back to the manual workflow documented in:
- `CLAUDE.md` § Feature Migration Workflow
- `docs/integration-rules.md`
