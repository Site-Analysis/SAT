# FVD-13 — Energy Use & Embodied Carbon (ECBC 2017)

**Jira Ticket:** — (no ticket; partially maps to US-10 Environmental Clearance / ECBC)
**Status:** Done — V3 in org repo (`Site-Analysis/SiteAnalysisToolV3`)
**Resolved:** 2026-05-26 (SiteAnalysisToolV3)
**Type:** New Feature
**Authors:** V3 team
**Repository:** [`Site-Analysis/SiteAnalysisToolV3`](https://github.com/Site-Analysis/SiteAnalysisToolV3) — `frontend/src/lib/energy-carbon.ts`
**Latest Commit:** `4bf53de` (2026-05-15, `Site-Analysis/SiteAnalysisToolV3` main)

---

## Feature Overview

**User Story:** As a sustainability consultant, I want to estimate annual energy use and embodied carbon for proposed buildings, so that I can compare design variants against ECBC 2017 benchmarks at concept stage.

**Business Value:** Provides Energy Use Intensity (EUI) calculations anchored to ECBC 2017 benchmarks for all 5 India climate zones. Per-building and portfolio-level energy and carbon figures update live as massing changes in the simulation. Enables ECBC compliance pre-screening without a full energy simulation.

---

## Acceptance Criteria (derived)

| # | Acceptance Criterion |
|---|---|
| 1 | Baseline EUI values from ECBC 2017 for residential and commercial use per climate zone |
| 2 | EUI adjustments applied for surface-to-volume ratio, building height, aspect ratio, natural ventilation |
| 3 | Annual energy (kWh/year) calculated per building |
| 4 | Total portfolio energy and average EUI calculated |
| 5 | Embodied carbon (kgCO₂e) estimated per building and in live simulation metrics |
| 6 | All 5 India climate zones supported: hot-dry, warm-humid, composite, temperate, cold |

---

## Code Traceability Matrix

| # | Acceptance Criterion | File | Function / Symbol |
|---|---|---|---|
| 1 | ECBC 2017 baseline EUI | `lib/energy-carbon.ts` | `BASELINE_EUI: Record<IndiaClimateZone, {residential, commercial}>` |
| 2 | Surface-to-volume penalty | `lib/energy-carbon.ts` | `calculateEUIAdjustments()` → `surfaceRatio` |
| 2 | Height penalty | `lib/energy-carbon.ts` | `calculateEUIAdjustments()` → `heightPenalty` (+2% per floor above 5) |
| 2 | Exposure factor | `lib/energy-carbon.ts` | `calculateEUIAdjustments()` → `exposureFactor` (E-W elongated) |
| 2 | Ventilation discount | `lib/energy-carbon.ts` | `calculateEUIAdjustments()` → `ventilationDiscount` (-8% low-rise cross-vent) |
| 3 | Per-building energy | `lib/energy-carbon.ts` | `calculateBuildingEUI(building, climateZone, useType)` → `{euiKwhPerSqm, totalKwh}` |
| 4 | Portfolio totals | `lib/energy-carbon.ts` | `calculateTotalEnergyUse(buildings, climateZone)` → `{totalKwh, avgEui, perBuildingKwh}` |
| 5 | Carbon in live metrics | `simulation/stores/useProposalAnalysisStore.ts` | `proposalMetrics.carbon` (kgCO₂e) |
| 5 | Carbon display | `simulation/components/panels/AnalysisPanel.tsx` | `MetricRow label="Carbon"` |
| 6 | Climate zone coverage | `lib/energy-carbon.ts` | `BASELINE_EUI` has all 5 zones |

---

## Implementation Breakdown

### Architecture

```
calculateBuildingEUI(building, climateZone, useType)
    └── baseEUI = BASELINE_EUI[climateZone][useType]  (kWh/m²/year)
    └── calculateEUIAdjustments(building):
        ├── surfaceArea = 2×(width+depth)×height + footprintArea
        ├── surfaceRatio = surfaceArea / volume
        │   penalty = max(0, (surfaceRatio - 0.25) × 0.5)
        ├── heightPenalty = max(0, numFloors - 5) × 0.02
        ├── exposureFactor = (aspectRatio > 2) ? 0.05 : 0
        └── ventilationDiscount = (numFloors ≤ 5 && aspectRatio < 3) ? -0.08 : 0
    └── totalFactor = 1 + surfaceRatio + heightPenalty + exposureFactor + ventilationDiscount
    └── euiKwhPerSqm = round(baseEUI × totalFactor)
    └── totalKwh = euiKwhPerSqm × grossFloorArea

calculateTotalEnergyUse(buildings, climateZone)
    └── Per building: detect useType from floor.use (commercial vs residential)
    └── Sum totalKwh, GFA-weighted avgEui
```

### ECBC 2017 Baseline EUI Table (from code)

| Climate Zone | Residential (kWh/m²/yr) | Commercial (kWh/m²/yr) |
|---|---|---|
| hot-dry | 85 | 180 |
| warm-humid | 95 | 200 |
| composite | 90 | 190 |
| temperate | 65 | 140 |
| cold | 110 | 160 |

### Technology Stack

| Component | Technology |
|---|---|
| Energy engine | Pure TypeScript — `energy-carbon.ts` |
| Use type detection | Per-floor `.use` field from `UserBuilding` model |
| Carbon proxy | `proposalMetrics.carbon` in `useProposalAnalysisStore` |
| Tests | `frontend/src/tests/energy-carbon.test.ts` |

---

## Automated Validation Plan

> Pure frontend library — tests run with Vitest.

### Run existing test suite

```bash
cd /Volumes/LocalDrive/SiteAnalysisToolV3/frontend
npx vitest run src/tests/energy-carbon.test.ts
```

### AC-1: Baseline EUI spot check

```typescript
import { calculateBuildingEUI } from '@/lib/energy-carbon';
// Minimal building: 10×10 m, 3 floors, 3 m/floor
const building = { width: 10, depth: 10, numFloors: 3, totalHeight: 9,
                   footprintArea: 100, volume: 900, grossFloorArea: 300, floors: [] };
const { euiKwhPerSqm, totalKwh } = calculateBuildingEUI(building, 'composite', 'residential');
console.log('EUI:', euiKwhPerSqm, 'kWh/m²/yr');   // Expected: ~90 (no penalties for compact)
console.log('Total:', totalKwh, 'kWh/yr');          // Expected: ~27,000 kWh/yr
console.assert(euiKwhPerSqm >= 80 && euiKwhPerSqm <= 120, 'EUI out of expected range');
```

### AC-2: Height penalty applies above 5 floors

```typescript
const tall = { ...building, numFloors: 15, totalHeight: 45, grossFloorArea: 1500 };
const { euiKwhPerSqm: tallEUI } = calculateBuildingEUI(tall, 'composite', 'residential');
const short = { ...building, numFloors: 3, totalHeight: 9, grossFloorArea: 300 };
const { euiKwhPerSqm: shortEUI } = calculateBuildingEUI(short, 'composite', 'residential');
console.assert(tallEUI > shortEUI, `Tall building (${tallEUI}) should have higher EUI than short (${shortEUI})`);
console.log('✓ Height penalty confirmed:', tallEUI, '>', shortEUI);
```

### AC-4: Portfolio total

```typescript
import { calculateTotalEnergyUse } from '@/lib/energy-carbon';
const buildings = [building, tall];
const { totalKwh, avgEui } = calculateTotalEnergyUse(buildings, 'composite');
console.assert(totalKwh > 0, 'Portfolio total must be > 0');
console.assert(avgEui > 0, 'Average EUI must be > 0');
console.log('Portfolio total:', totalKwh, 'kWh/yr | Avg EUI:', avgEui, 'kWh/m²/yr');
```

### AC-6: All climate zones return values

```typescript
const zones = ['hot-dry', 'warm-humid', 'composite', 'temperate', 'cold'];
zones.forEach(zone => {
  const { euiKwhPerSqm } = calculateBuildingEUI(building, zone, 'residential');
  console.assert(euiKwhPerSqm > 0, `${zone}: EUI is 0`);
  console.log(zone, '→', euiKwhPerSqm, 'kWh/m²/yr');
});
```

---

## Outstanding Actions

1. **ECBC baseline accuracy** — Values in `BASELINE_EUI` (e.g. hot-dry residential 85, commercial 180) should be cross-checked against ECBC 2017 Section 4 Table 4.1 by a certified energy auditor.
2. **Carbon calculation** — `proposalMetrics.carbon` in simulation is computed in `useProposalAnalysisStore`; relationship to `energy-carbon.ts` not confirmed. Verify they share the same formula.
3. **Embodied carbon (LCA)** — Code comment references "Material-based LCA proxy" but no material lookup table found in `energy-carbon.ts`. Appears to be deferred or in a different file.
4. **Jira ticket** — Map to US-10 (Environmental Clearance / ECBC/IGBC/GRIHA) and raise ticket.
5. **UI panel** — No dedicated energy results panel found in V3 frontend. Carbon shows in AnalysisPanel live metric, but detailed EUI breakdown has no UI.
