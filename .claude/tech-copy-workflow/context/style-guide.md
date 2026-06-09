# SAT Technical Copy Style Guide

Research basis: Gemini Deep Research (Technical Copywriter Research Report, June 2026).
Frameworks: Plain Language (plainlanguage.gov), Mailchimp Voice & Tone, Nielsen Norman Group UX writing, John Carroll's Minimalism doctrine, Diataxis (Daniele Procida).

---

## Plain Language Rules (10 Mandates)

1. **Active voice always.** "SAT calculates the flood risk score" not "The flood risk score is calculated."
2. **Address the user as "you."** "Your site" not "the site." "You can export" not "Users can export."
3. **Short sentences.** Target ≤20 words per sentence in UI copy. Help articles: ≤25 words.
4. **One idea per sentence.** Split compound sentences with "and/but/because" into two.
5. **Common words.** "Use" not "utilize." "Show" not "display." "Get" not "retrieve."
6. **Front-load the main point.** The essential information first. Details after.
7. **No nominalizations.** "Analyze" not "perform an analysis." "Export" not "conduct an export."
8. **No jargon without translation.** Every technical term used in user-facing copy must be translatable to plain language on demand (see geospatial-glossary.md).
9. **Positive framing.** "Enter a valid coordinate" not "Don't enter an invalid coordinate."
10. **Omit redundant words.** "Currently" is almost always deletable. "In order to" → "to."

---

## Flesch-Kincaid Readability Targets

| Content type | Target score | Target grade level |
|---|---|---|
| Onboarding modals | 60–70 | 8th grade |
| Tooltips | 65–75 | 7th–8th grade |
| Error messages | 70–80 | 6th–7th grade |
| Help center articles | 50–65 | 9th–10th grade |
| API documentation | 40–55 | 11th grade (technical audience) |
| Technical blog | 45–60 | 10th–11th grade |

High readability does not mean simple topics. It means accessible language. An architect under deadline pressure should parse a sentence in one read.

---

## Microcopy Anatomy

### Error Messages — Problem + Cause + Solution

Every error message must contain all three elements:

```
[P] What happened (the problem, stated plainly)
[C] Why it happened (the cause, specific and honest)
[S] What the user can do (the fix, actionable)
```

**SAT examples:**

| Scenario | Poor | Correct (P+C+S) |
|---|---|---|
| Site boundary too large | "Error: boundary limit exceeded" | "Analysis failed. The site boundary is larger than the 5 sq km limit for wind calculations. Reduce the boundary or switch to a localized zone." |
| No elevation data | "Error 500: Missing DEM data" | "Flood analysis failed. High-resolution elevation data (MERIT DEM) is unavailable for this region. Try expanding your site boundary, or upload your own topographic file." |
| Invalid coordinates | "Invalid input" | "Those coordinates fall outside India. SAT currently covers Indian sites only. Move the pin to a location within India." |
| Network timeout | "Analysis failed" | "The temperature analysis timed out. This usually happens with slow connections. Try again — analysis takes about 30 seconds." |
| No IMD data | "No data found" | "No IMD climate data found for this location. The IMD grid covers India at 0.25° resolution — some remote areas have gaps. Open-Meteo data is available as a fallback." |

### Empty State Patterns — Pre-Action vs No-Data

Distinguish between two distinct empty states:

**Pre-action empty state** (feature exists but hasn't been run yet):
```
Format: [What this shows] + [Why it's useful] + [How to start]
Example: "Run a flood risk analysis to see a 0–100 risk score for your site,
          scored across elevation, hydrology, rainfall, and soil type.
          Draw your site boundary to begin."
```

**No-data empty state** (analysis ran but no data exists for this location):
```
Format: [What was tried] + [Why no data] + [What to try instead]
Example: "No climate data found for this coordinate. This usually happens in
          ocean regions or areas outside IMD coverage. Adjust the site pin
          to a land location in India."
```

### Loading State Copy — Name the Computation

Loading copy must reference the actual computational step:
```
Never: "Loading..." / "Please wait..." / "Processing..."

Always: Name what SAT is actually doing
```

**SAT loading copy by analysis:**

**Flood analysis:**
- 0–2s: "Fetching MERIT DEM elevation data..."
- 2–5s: "Querying JRC Global Surface Water for historical flooding..."
- 5–8s: "Calculating 4-component risk score..."
- 8+s: "Almost there — finalizing flood risk map..."

**Solar / Sun Path:**
- 0–2s: "Computing NREL SPA solar position for your coordinates..."
- 2–4s: "Fetching nearby building heights from OpenStreetMap..."
- 4–7s: "Simulating shadow coverage for selected date..."

**Temperature:**
- 0–2s: "Querying Open-Meteo climate archive..."
- 2–5s: "Building thermal profile for your location..."
- 5+s: "Generating material recommendations..."

**Wind:**
- 0–2s: "Fetching Open-Meteo wind climatology..."
- 2–5s: "Calculating prevailing wind directions..."

**Rainfall:**
- 0–2s: "Querying IMD precipitation data..."
- 2–5s: "Mapping seasonal rainfall patterns..."

### Tooltip Patterns — What It Is vs How to Use It

Differentiate two tooltip types:

**Type 1 — Technical data field (explains a metric):**
```
Format: [What it measures] + [The scale/unit] + [What it means for the user]
Example (NDVI Score): "Measures vegetation health using infrared satellite imagery.
                        Scores from -1 to 1 — above 0.5 indicates dense greenery.
                        Below 0.1 usually indicates concrete or bare soil."
```

**Type 2 — UI control (explains an interaction):**
```
Format: [What the control does] + [How to use it]
Example (Sun path slider): "Move the slider to see how shadows change
                             across the day. Drag to the left for morning,
                             right for afternoon."
```

Never combine both types in one tooltip. If both are needed: Type 2 in the tooltip, Type 1 behind a "What is this?" link.

### Button Labels — Action Verb + Specific Outcome

| Wrong | Right |
|---|---|
| Submit | Run Analysis |
| OK | Save Proposal |
| Done | Export GeoJSON |
| Generate | View Sun Path |
| Click here | Download Report |
| Continue | Start Drawing |

### Confirmation Patterns — Non-Intrusive Toast

```
Format: [Action] + [outcome] + [location if helpful]
Example: "Wind analysis saved to Proposal B."
Example: "GeoJSON exported to Downloads."
Example: "Sun path analysis added to your project."
```
No modal confirmation required for non-destructive actions. Use toast only.
Destructive actions (delete, overwrite) require modal confirmation.

### Onboarding Modal Copy — 3 Screens Maximum

```
Screen 1 — Value proposition:
  Headline: ≤7 words — what this feature does for them
  Body: ≤25 words — the outcome, not the mechanism

Screen 2 — Core interaction:
  Headline: ≤7 words — the main action
  Body: ≤20 words — how to start

Screen 3 — First action:
  CTA only — specific verb + outcome
  Skip button visible on all screens
```

---

## The Coordinate Law

**GeoJSON arrays use [Longitude, Latitude]. Always. Without exception.**

```json
// CORRECT
{
  "type": "Point",
  "coordinates": [77.5946, 12.9716]  // [Longitude, Latitude] → Bengaluru
}

// WRONG — causes silent geographic query failures
{
  "type": "Point",
  "coordinates": [12.9716, 77.5946]  // [Latitude, Longitude] ← NEVER
}
```

This must be displayed prominently in:
- All API endpoint documentation
- All code examples with coordinate parameters
- The SAT developer quickstart guide
- Any error message involving invalid coordinates

Source: RFC 7946 (GeoJSON standard), Mapbox documentation.

**Bounding box format:**
```
[minLon, minLat, maxLon, maxLat]
Example: [72.8, 8.4, 97.4, 37.6]  // India bounding box
```
CRS default: WGS84 (EPSG:4326) unless explicitly overridden.

---

## Diataxis Application Rules

Never mix quadrants in a single document. Classify before writing.

**Tutorial signals (use when):**
- The user has never done this before
- Success = completing a specific first task
- Tone: warm, encouraging, step-by-step
- Length: short — stop once the goal is achieved

**How-To Guide signals (use when):**
- The user knows the basics and has a specific task
- Success = task completed
- Tone: direct, professional, goal-oriented
- Heading style: "How to [verb] [specific outcome]"

**Reference signals (use when):**
- The user needs accurate, complete information to do something else
- Success = found the fact they needed
- Tone: neutral, austere, no prose padding
- Structure: tables, lists, no storytelling

**Explanation signals (use when):**
- The user wants to understand, not act
- Success = mental model built
- Tone: thoughtful, contextual
- Use for: "Understanding flood risk scoring", "How NREL SPA works"

---

## Voice and Tone Matrix (Adapted from Mailchimp)

SAT's **voice** is constant: precise, honest, technically fluent, architect-respecting.

SAT's **tone** shifts by context:

| User state | Tone |
|---|---|
| Learning a new feature | Encouraging, clear, brief |
| Completing a task | Efficient, direct |
| Encountering an error | Calm, empathetic, actionable — never accusatory |
| Waiting for analysis | Informative, reassuring |
| Receiving analysis results | Neutral, precise, data-first |
| First-time onboarding | Warm, value-focused |

**What we never do:**
- Blame the user ("You entered an invalid...") → reframe ("That coordinate is outside...")
- Sound excited about an error ("Oops! Something went wrong!")
- Anthropomorphize ("SAT is thinking really hard...")
- Use exclamation marks in neutral states

---

## Content Lifecycle and Audit

Trigger a content review when:
- A referenced data source changes (e.g., IMD grid resolution update)
- A feature is moved from 🔄 to ✅ (onboarding copy may need updating)
- Support tickets spike on a specific topic (tooltip or help article failing)
- A feature is deprecated or moved to 📋

Content audit ROT check:
- **Redundant**: Is this covered elsewhere? Consolidate.
- **Outdated**: Does this reference a stale feature state? Update.
- **Trivial**: Does this add nothing? Delete.

Target audit cadence for SAT (early-stage): every 2 months or post-sprint.
