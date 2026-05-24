# Integration Rules

These rules prevent breakage while integrating features incrementally.

1. Contract-first: update OpenAPI specs before code changes.
2. Feature flags default off for all new behavior.
3. Backward compatibility: breaking changes require versioning and migration plan.
4. One feature per PR, small and reviewable.
5. No direct DB access from frontend; all access via services.
6. All migrations require rollback notes.
7. Tests must cover acceptance criteria.
