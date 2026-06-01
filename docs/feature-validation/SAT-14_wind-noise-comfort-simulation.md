# FVD-14 — Pedestrian Wind Comfort + Noise Simulation + Thermal Comfort

**Jira Ticket:** — (no ticket)
**Status:** Done — V3 in org repo (`Site-Analysis/SiteAnalysisToolV3`)
**Resolved:** 2026-05-26 (SiteAnalysisToolV3)
**Type:** New Feature
**Authors:** V3 team
**Repository:** [`Site-Analysis/SiteAnalysisToolV3`](https://github.com/Site-Analysis/SiteAnalysisToolV3) — `frontend/src/lib/wind-sim.ts`, `noise-sim.ts`, `thermal-comfort.ts`
**Latest Commit:** `4bf53de` (2026-05-15, `Site-Analysis/SiteAnalysisToolV3` main)

---

## Feature Overview

**User Story:** As an urban designer, I want client-side wind comfort, noise exposure, and thermal comfort maps for a proposed site, so that I can assess pedestrian experience without running cloud simulations.

**Business Value:** Three complementary microclimate simulations run entirely in the browser in real time as massing changes. Wind uses a simplified CFD model (power-law profile + building wake effects). Noise uses logarithmic propagation with Maekawa barrier attenuation. Thermal comfort uses the ISO 7730 PMV/PPD model. All three are calibrated for India (India climate zones, CPCB noise standards, IMD seasons).

---

## Acceptance Criteria (derived)

| # | Module | Acceptance Criterion |
|---|---|---|
| 1 | Wind | Wind vector field calculated per grid point accounting for building wakes and Venturi effects |
| 2 | Wind | Pedestrian comfort classified per Lawson criteria (comfortable / moderate / uncomfortable / dangerous) |
| 3 | Wind | Wind comfort grid summary: avg speed, max amplification, % by comfort class |
| 4 | Wind | India climate zone wind defaults (5 zones × 2 seasons) |
| 5 | Noise | Noise at distance calculated using inverse-square law + atmospheric absorption |
| 6 | Noise | Barrier attenuation from buildings via simplified Maekawa method |
| 7 | Noise | Multiple sources combined logarithmically |
| 8 | Noise | CPCB noise limits enforced per zone (industrial/commercial/residential/silence) |
| 9 | Noise | Grid summary: average/max exposure, % above limit, % silent |
| 10 | Thermal | PMV (Predicted Mean Vote) calculated per ISO 7730 (Fanger model) |
| 11 | Thermal | UTCI (Universal Thermal Climate Index) or equivalent microclimate results returned |

---

## Code Traceability Matrix

| # | File | Function / Symbol |
|---|---|---|
| 1 | `lib/wind-sim.ts` | `getWindVector(x, y, z, baseSpeed, directionDeg, buildings)` |
| 1 | `lib/wind-sim.ts` | Power-law vertical profile: `heightFactor = (z/10)^0.28` |
| 1 | `lib/wind-sim.ts` | Wake zone: downwind reduction 0.3→1.0 over `3×buildingHeight` |
| 1 | `lib/wind-sim.ts` | Venturi: gap acceleration up to ×1.4 |
| 1 | `lib/wind-sim.ts` | Corner acceleration ×1.3 |
| 2 | `lib/wind-sim.ts` | `getWindComfort(speed)` → `'comfortable'|'moderate'|'uncomfortable'|'dangerous'` |
| 3 | `lib/wind-sim.ts` | `calculateWindComfortGrid(…)` → `WindResults` |
| 3 | `types/simulation.ts` | `WindResults: {avgPedestrianSpeed, maxAmplification, comfortableArea%, moderateArea%, uncomfortableArea%, dangerousArea%, comfortGrid}` |
| 4 | `lib/wind-sim.ts` | `INDIA_WIND_DATA: Record<IndiaClimateZone, IndiaWindData>` — 5 zones |
| 4 | `lib/wind-sim.ts` | `getDefaultWind(zone, isMonsoon)` |
| 5 | `lib/noise-sim.ts` | `noiseAtDistance(sourcedB, distanceM, absorption=0.005)` |
| 5 | `lib/noise-sim.ts` | Formula: `dB(r) = dB_source - 20·log10(r) - α·r` |
| 6 | `lib/noise-sim.ts` | `barrierAttenuation(sourcePos, receiverPos, buildings)` — Maekawa method |
| 6 | `lib/noise-sim.ts` | Attenuation range: 5–25 dB based on barrier height factor |
| 7 | `lib/noise-sim.ts` | `combineNoiseLevels(levels[])` — `10·log10(Σ 10^(Li/10))` |
| 8 | `lib/noise-sim.ts` | `INDIA_NOISE_LIMITS: IndiaNoiseLimits[]` — industrial 75/70, commercial 65/55, residential 55/45, silence 50/40 dB(A) |
| 8 | `lib/noise-sim.ts` | `getNoiseLimitForZone(zoneType, isDaytime)` |
| 9 | `lib/noise-sim.ts` | `calculateNoiseGrid(…)` → `NoiseResults` |
| 9 | `types/simulation.ts` | `NoiseResults: {averageExposure, maxExposure, areaAboveLimit%, silentArea%, noiseGrid, indianStandardLimit}` |
| 10 | `lib/thermal-comfort.ts` | `calculatePMV(ta, tr, vel, rh, met, clo)` — ISO 7730 Fanger iterative |
| 11 | `types/simulation.ts` | `MicroclimateResults` — thermal comfort grid |
| — | `lib/wind-sim.ts` | `getBeaufortScale(speed)` — 0–8 Beaufort |
| — | `lib/wind-sim.ts` | `getWindComfortColor(comfort)` — green/yellow/orange/red |
| — | `lib/noise-sim.ts` | `getRoadNoisedB(roadType)` — motorway 78dB → footway 40dB |
| — | `lib/noise-sim.ts` | `getNoiseColor(dB)` + `getNoiseDescription(dB)` |

---

## Implementation Breakdown

### Wind Model

```
getWindVector(x, y, z, baseSpeed, directionDeg, buildings)
    ├── Direction vector: (270 + directionDeg) × π/180
    ├── Power-law height: vx,vy × (z/10)^0.28  (urban α=0.28)
    └── Per building:
        ├── If inside footprint (z < height): wind → 0.05×, updraft 0.1×
        ├── Wake (downwind, < 3×height): reduce 0.3→1.0 + turbulence ±0.2×
        ├── Venturi (gap, 1.2–3× radius): accelerate ×(1 + 0.4·exp(-dist/r))
        └── Corner (0.9–1.5× radius): accelerate ×1.3

Lawson Criteria:
  ≤ 4.0 m/s  → comfortable (sitting/standing)
  ≤ 6.0 m/s  → moderate   (walking)
  ≤ 10.0 m/s → uncomfortable
  > 10.0 m/s → dangerous
```

### Noise Model

```
noiseAtDistance(sourcedB, distanceM)
    = sourcedB - 20·log10(dist/1m) - 0.005·dist

barrierAttenuation(source, receiver, buildings)
    ├── Project building onto source→receiver line (t = 0.1–0.9)
    ├── Check perpendicular distance ≤ halfWidth
    └── Attenuation = 5 + 10·min(height/10, 2)  [5–25 dB]

combineNoiseLevels(levels)
    = 10·log10(Σ 10^(Li/10))
```

### Thermal Comfort Model (PMV, ISO 7730)

```
calculatePMV(ta, tr, vel, rh, met, clo)
    ├── M = met × 58.2 W/m²
    ├── Icl = clo × 0.155 m²·K/W
    ├── pa = (rh/100) × 610.5 × exp(17.269·ta / (237.3+ta))  [Pa]
    ├── Iterative tcl (clothing surface temp) over 20 cycles
    └── PMV formula (Fanger): heat balance with radiant, convective, evaporative terms
        Range: −3 (cold) to +3 (hot), comfort band −0.5 to +0.5
```

### Technology Stack

| Component | Technology |
|---|---|
| Wind CFD | Pure TypeScript — `wind-sim.ts` (simplified, not full CFD) |
| Noise propagation | Pure TypeScript — `noise-sim.ts` |
| Thermal comfort | Pure TypeScript — `thermal-comfort.ts` |
| Indian standards | CPCB noise limits, NBC 2016, IMD seasons, ECBC climate zones |

---

## Automated Validation Plan

### Wind comfort grid test

```typescript
import { calculateWindComfortGrid, getDefaultWind } from '@/lib/wind-sim.ts';

const wind = getDefaultWind('composite', false); // Winter composite
const result = calculateWindComfortGrid(
  0, 0,           // origin
  100, 100,       // 100×100 m
  5,              // 5 m resolution (20×20 = 400 points)
  wind.speed, wind.direction,
  [{ cx: 50, cy: 50, width: 20, depth: 20, height: 15 }] // one building
);
console.log('Avg speed:', result.avgPedestrianSpeed, 'm/s');
console.log('Comfortable area:', result.comfortableArea, '%');
console.assert(result.comfortableArea + result.moderateArea + result.uncomfortableArea + result.dangerousArea === 100, 'Percentages must sum to 100');
console.assert(result.avgPedestrianSpeed > 0, 'Avg speed > 0');
console.assert(result.maxAmplification >= 1, 'Max amplification ≥ 1');
```

### Noise propagation test

```typescript
import { noiseAtDistance, combineNoiseLevels, INDIA_NOISE_LIMITS } from '@/lib/noise-sim.ts';

// Point source at 1 m, 10 m, 100 m:
const db1   = noiseAtDistance(75, 1);    // Should be 75
const db10  = noiseAtDistance(75, 10);   // Should be ~55 (−20 dB)
const db100 = noiseAtDistance(75, 100);  // Should be ~35 (−40 dB)
console.assert(db1 === 75, 'At 1m source level unchanged');
console.assert(db10 < db1, '10m < 1m');
console.assert(db100 < db10, '100m < 10m');
console.log('1m:', db1, '| 10m:', db10.toFixed(1), '| 100m:', db100.toFixed(1));

// CPCB limits present:
const residentialDay = INDIA_NOISE_LIMITS.find(l => l.zone === 'residential').dayLimit;
console.assert(residentialDay === 55, `Residential day limit should be 55 dB(A), got ${residentialDay}`);
```

### PMV thermal comfort test

```typescript
import { calculatePMV } from '@/lib/thermal-comfort.ts';

// Comfortable outdoor conditions: ta=25°C, tr=27°C, vel=0.5 m/s, rh=50%, met=1.2, clo=0.5
const pmv = calculatePMV(25, 27, 0.5, 50, 1.2, 0.5);
console.log('PMV:', pmv.toFixed(2)); // Expected: near 0 (comfortable)
console.assert(pmv > -1 && pmv < 1, `PMV ${pmv} outside comfort range for normal conditions`);

// Hot humid: ta=38°C, tr=40°C, vel=0.1 m/s, rh=80%
const hotPmv = calculatePMV(38, 40, 0.1, 80, 1.2, 0.5);
console.assert(hotPmv > 2, `Hot humid should give PMV > 2, got ${hotPmv}`);
```

---

## Outstanding Actions

1. **Wind CFD limitations** — Model is a simplified approximation (not a true CFD solver). Disclaimer needed in UI. For production accuracy, couple to a server-side CFD service (OpenFOAM or EnergyPlus).
2. **No UI panels** — `wind-sim.ts`, `noise-sim.ts`, `thermal-comfort.ts` are library files only. No `WindComfortPanel` or `NoiseMappingPanel` component found in V3. UI needed to expose these to users.
3. **Real noise sources** — Noise grid requires `NoiseSource[]` input; no automatic road/traffic noise extraction from OSM found. Need to wire `getRoadNoisedB(roadType)` to OSM context roads.
4. **Thermal coupling** — PMV requires `tr` (mean radiant temperature), which depends on sun path analysis. Coupling to SunPath backend output not implemented.
5. **Jira ticket** — No story. Raise as new features or sub-features under the simulation epic.
