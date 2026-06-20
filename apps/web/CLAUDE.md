@AGENTS.md

## Frontend Patterns

### CSS Modules — hyphenated class names
Use `const $ = styles as Record<string, string>` then `$["class-name"]` for bracket access. Dot notation fails for hyphenated names. Pattern in `components/landing/LandingPage.tsx`.

### Monthly rainfall data path
`result.charts?.find(c => c.title === "Monthly rainfall")?.points` → 12 `{label: "Jan"…"Dec", value: mm}` objects. Reuse the `monthly()` helper at `components/layout/RainfallPanel.tsx:26` instead of re-extracting.
