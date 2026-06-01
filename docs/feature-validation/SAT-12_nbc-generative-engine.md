# FVD-12 — NBC 2016 Constraints + Generative Design Engine

**Jira Ticket:** — (no ticket; partially maps to US-09 Accessibility Standards / US-10 Environmental Clearance)
**Status:** Done — V3 in org repo (`Site-Analysis/SiteAnalysisToolV3`)
**Resolved:** 2026-05-26 (SiteAnalysisToolV3)
**Type:** New Feature
**Authors:** V3 team
**Repository:** [`Site-Analysis/SiteAnalysisToolV3`](https://github.com/Site-Analysis/SiteAnalysisToolV3) — `frontend/src/lib/`
**Latest Commit:** `4bf53de` (2026-05-15, `Site-Analysis/SiteAnalysisToolV3` main)

---

## Feature Overview

**User Story:** As a planner, I want to know the maximum permissible FAR, setbacks, ground coverage, and parking for a plot, and get auto-generated building layout options that comply with NBC 2016, so that I can evaluate design envelopes at pre-design stage.

**Business Value:** Encodes NBC 2016 (National Building Code of India) rules as a computable engine — eliminating manual lookup. Generative engine produces 4–6 typology variants (tower-podium, courtyard, linear-block, plotted, mixed-use, commercial) on the plot, all respecting FAR/setback constraints. AI enhancer scores variants on 8 climate-weighted criteria.

---

## Acceptance Criteria (derived)

| # | Acceptance Criterion |
|---|---|
| 1 | Max FAR calculated from plot area + road width + zone type |
| 2 | Setbacks (front, rear, side) calculated per NBC 2016 |
| 3 | Max ground coverage and min open space returned |
| 4 | Minimum parking ECS calculated |
| 5 | 6 building typologies available (tower-podium, courtyard, linear-block, plotted, mixed-use, commercial) |
| 6 | Generative engine places buildings on plot respecting all NBC constraints |
| 7 | Variants scored on 8 criteria: NFA, FAR efficiency, sun hours, wind comfort, noise, ventilation, NBC compliance, open space |
| 8 | Climate-adaptive scoring weights applied per India climate zone |

---

## Code Traceability Matrix

| # | Acceptance Criterion | File | Function / Class |
|---|---|---|---|
| 1 | Max FAR | `lib/modeling-math.ts` | `getMaxAllowedFAR(plotArea, roadWidth, zoneType)` |
| 2 | NBC setbacks | `lib/modeling-math.ts` | `calculateNBCSetbacks(plotArea, maxHeight, roadWidth)` |
| 3 | Ground coverage | `lib/modeling-math.ts` | `getMaxGroundCoverage(plotArea)` |
| 4 | Parking ECS | `lib/nbc-constraints.ts` | `calculateNBCConstraints()` → `minParkingECS` |
| 1–4 | Full constraints object | `lib/nbc-constraints.ts` | `calculateNBCConstraints(plotArea, roadWidth, zoneType, maxHeight)` → `NBCConstraints` |
| 5–6 | Typology presets | `lib/generative-engine.ts` | `TYPOLOGY_PRESETS: Record<BuildingTypology, TypologyPreset>` — 6 typologies |
| 6 | Building placement | `lib/generative-engine.ts` | `generateVariants(params, constraints)` → `GeneratedVariant[]` |
| 6 | Setback enforcement | `lib/nbc-constraints.ts` | `calculateBuildableArea(plotWidth, plotDepth, constraints)` |
| 6 | FAR validation | `lib/nbc-constraints.ts` | `validateFAR(buildings, plotArea, maxFAR)` |
| 6 | Coverage validation | `lib/nbc-constraints.ts` | `validateGroundCoverage(buildings, plotArea, maxCoverage)` |
| 7 | Variant scoring | `lib/ai-enhancer.ts` | `scoreVariant(variant, params, constraints)` → score 0–100 |
| 7 | Spacing quality | `lib/ai-enhancer.ts` | `spacingQualityScore(buildings, plotArea)` |
| 8 | Climate weights | `lib/ai-enhancer.ts` | `CLIMATE_WEIGHTS: Record<IndiaClimateZone, Record<string, number>>` |
| — | Types | `types/simulation.ts` | `NBCConstraints`, `GeneratedVariant`, `BuildingTypology`, `TypologyPreset` |
| — | Floor count calc | `lib/nbc-constraints.ts` | `maxFloorsAllowed(maxHeight, floorHeight, hasPodium)` |
| — | Min spacing | `lib/nbc-constraints.ts` | `minBuildingSpacing(buildingHeight)` |

---

## Implementation Breakdown

### Architecture

```
calculateNBCConstraints(plotArea, roadWidth, zoneType, maxHeight)
    └── getMaxAllowedFAR(plotArea, roadWidth, zoneType)    # lib/modeling-math.ts
    └── getMaxGroundCoverage(plotArea)                      # lib/modeling-math.ts
    └── calculateNBCSetbacks(plotArea, maxHeight, roadWidth) # lib/modeling-math.ts
    └── minParkingECS (residential: units, commercial: per 100 m² GFA)
    → NBCConstraints { maxFAR, maxGroundCoverage, frontSetback, rearSetback,
                       sideSetback, maxHeight, minParkingECS, minOpenSpace }

generateVariants(params, constraints)
    └── For each typology (tower-podium, courtyard, linear-block, plotted, …):
        ├── calculateBuildableArea(plotWidth, plotDepth, constraints)
        ├── maxFloorsAllowed(maxHeight, floorHeight, hasPodium)
        ├── Place buildings in grid/staggered/courtyard layout
        ├── Check: validateFAR + validateGroundCoverage
        └── Return GeneratedVariant { buildings, totalGFA, farAchieved, coveragePercent }

scoreVariant(variant, params, constraints)
    └── 8 subscores × climate-zone weights
    └── CLIMATE_WEIGHTS[climateZone] = { nfa, farEfficiency, sunHours, windComfort, noise, ventilation, nbcCompliance, openSpace }
    └── spacingQualityScore(buildings, plotArea) — ideal spacing = 1.5× avg building height
    └── Final score 0–100
```

### Technology Stack

| Component | Technology |
|---|---|
| Constraint engine | Pure TypeScript — `nbc-constraints.ts` + `modeling-math.ts` |
| Generative engine | Pure TypeScript — `generative-engine.ts` |
| Scoring / AI enhancer | Rule-based heuristics — `ai-enhancer.ts` (no actual ML model) |
| Types | `types/simulation.ts`, `types/modeling.ts` |

### Typology Presets

| Typology | Default Floors | Footprint | Has Podium | Courtyard Ratio | Ventilation Bonus |
|---|---|---|---|---|---|
| `tower-podium` | 15 | 25×25 m | Yes (2F) | 0 | 0.30 |
| `courtyard` | 5 | 35×30 m | No | 0.25 | 0.80 |
| `linear-block` | 7 | 40×12 m | No | 0 | 0.50 |
| `plotted` | 3 | configurable | No | 0 | configurable |
| `mixed-use` | configurable | configurable | configurable | 0 | configurable |
| `commercial` | configurable | configurable | configurable | 0 | configurable |

### Climate-Adaptive Scoring Weights

| Weight Key | hot-dry | warm-humid | composite | temperate | cold |
|---|---|---|---|---|---|
| nfa | 0.20 | 0.20 | 0.22 | 0.25 | 0.22 |
| farEfficiency | 0.12 | 0.12 | 0.14 | 0.15 | 0.15 |
| sunHours | 0.08 | 0.10 | 0.12 | 0.15 | 0.18 |
| windComfort | 0.15 | 0.12 | 0.10 | 0.08 | 0.05 |
| ventilation | 0.18 | 0.20 | 0.12 | 0.10 | 0.08 |
| nbcCompliance | 0.10 | 0.10 | 0.12 | 0.12 | 0.12 |

### NBC 2016 Rules Encoded

| Rule | Implementation |
|---|---|
| FAR by plot + road width + zone | `getMaxAllowedFAR()` — lookup table |
| Front setback by plot area | `calculateNBCSetbacks()` |
| Side/rear setbacks | `calculateNBCSetbacks()` |
| Max ground coverage | `getMaxGroundCoverage()` — % of plot area |
| Max height | Default 45 m (configurable) |
| Parking (residential) | 1 ECS per estimated unit |
| Parking (commercial) | 1.5 ECS per 100 m² GFA |

---

## Automated Validation Plan

> Pure frontend library — tests run with Vitest. File: `frontend/src/tests/nbc.test.ts`

### AC-1 to AC-4: NBC constraints calculation

```bash
cd /Volumes/LocalDrive/SiteAnalysisToolV3/frontend
npx vitest run src/tests/nbc.test.ts
```

### AC-1: Manual spot check (500 m² plot, 7.5 m road, residential)

```typescript
// Run in browser console or test:
import { calculateNBCConstraints } from '@/lib/nbc-constraints';
const c = calculateNBCConstraints(500, 7.5, 'residential', 45);
console.log('FAR:', c.maxFAR);               // expected: 1.5–2.5 range
console.log('Front setback:', c.frontSetback); // expected: ≥ 1.5 m
console.log('Parking ECS:', c.minParkingECS);
console.assert(c.maxFAR > 0, 'FAR must be > 0');
console.assert(c.maxGroundCoverage <= 100, 'Coverage ≤ 100%');
console.assert(c.minOpenSpace + c.maxGroundCoverage <= 100, 'Open+coverage ≤ 100');
```

### AC-6: Generative engine produces valid variants

```typescript
// Generate variants on 2000 m² plot:
import { generateVariants } from '@/lib/generative-engine';
import { calculateNBCConstraints } from '@/lib/nbc-constraints';
const constraints = calculateNBCConstraints(2000, 9, 'residential', 45);
const params = { plotArea: 2000, plotWidth: 40, plotDepth: 50, climateZone: 'composite' };
const variants = generateVariants(params, constraints);
console.log('Variants generated:', variants.length);
variants.forEach(v => {
  console.assert(v.farAchieved <= constraints.maxFAR * 1.01, `${v.typology}: FAR violation`);
  console.assert(v.coveragePercent <= constraints.maxGroundCoverage * 1.01, `${v.typology}: Coverage violation`);
  console.log(v.typology, '— FAR:', v.farAchieved.toFixed(2), '— Coverage:', v.coveragePercent.toFixed(1) + '%');
});
```

### AC-7 to AC-8: Variant scoring

```typescript
import { scoreVariant } from '@/lib/ai-enhancer';
const topVariant = variants[0];
const score = scoreVariant(topVariant, params, constraints);
console.assert(score >= 0 && score <= 100, 'Score out of range');
console.log('Best variant score:', score, '/100');
```

---

## Outstanding Actions

1. **NBC data accuracy** — FAR/setback lookup tables in `modeling-math.ts` need review by a licensed architect against NBC 2016 Table 15 & bylaw appendices. Not independently verified.
2. **Jira ticket** — No ticket exists. Raise as new story under E2 (US-09 Accessibility / US-10 Environmental Clearance overlap).
3. **Full NBC module** — `nbc-full.ts` exists but relationship to `nbc-constraints.ts` not yet clear; may have duplicate logic. Audit before integration.
4. **Generative UI** — `generative-engine.ts` and `ai-enhancer.ts` libraries are complete but no UI panel found in V3 that exposes them to users. UI component needed.
5. **Variant persistence** — `variant-manager.ts` handles save/load but not yet connected to generative output. Wire up.
