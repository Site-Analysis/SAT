# Feature Flags

All new features must be behind flags and default to off.

## Naming
Use dot notation:
- feature.<domain>.<name>

Examples:
- feature.map.drawing
- feature.sunpath.timeseries

## Rules
- Flags must be checked in both service and frontend.
- Flags default false in all environments except test.
- Removing a flag requires deprecation notes.
