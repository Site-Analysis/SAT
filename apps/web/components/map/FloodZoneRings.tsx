// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { Circle, Polygon } from "react-leaflet";
import type { ModuleResult } from "@/lib/stores/analysis";

interface FloodZoneRingsProps {
  center: [number, number];
  result: ModuleResult;
  boundaryPolygon?: [number, number][] | null;
}

function clamp(v: number, lo: number, hi: number) {
  return Math.min(hi, Math.max(lo, v));
}

function indFrac(result: ModuleResult, label: string): number {
  return result.indicators?.find((i) => i.label === label)?.barFraction ?? 0;
}

function scalePoly(
  positions: [number, number][],
  scale: number,
  cLat: number,
  cLng: number,
): [number, number][] {
  const cosLat = Math.cos(cLat * Math.PI / 180);
  return positions.map(([lat, lng]) => [
    cLat + (lat - cLat) * scale,
    cLng + ((lng - cLng) * cosLat * scale) / cosLat,
  ] as [number, number]);
}

function polyAvgRadDeg(positions: [number, number][], cLat: number, cLng: number): number {
  const cosLat = Math.cos(cLat * Math.PI / 180);
  const dists = positions.map(([lat, lng]) =>
    Math.hypot(lat - cLat, (lng - cLng) * cosLat),
  );
  return dists.reduce((s, d) => s + d, 0) / dists.length || 0.001;
}

// Flood factor metadata — buffer range (metres) and legend color per factor
const FACTORS = [
  { key: "overallRisk",     bufMin:  30, bufRange:  50, color: "#1E3A8A", opacityScale: 0.72, opacityMax: 0.55 },
  { key: "lowLyingRisk",    bufMin:  80, bufRange:  80, color: "#2563EB", opacityScale: 0.58, opacityMax: 0.44 },
  { key: "waterOccurrence", bufMin: 160, bufRange: 120, color: "#3B82F6", opacityScale: 0.48, opacityMax: 0.35 },
  { key: "riverProximity",  bufMin: 280, bufRange: 120, color: "#93C5FD", opacityScale: 0.36, opacityMax: 0.24 },
] as const;

export function FloodZoneRings({ center, result, boundaryPolygon }: FloodZoneRingsProps) {
  const score           = result.score ?? 50;
  const overallRisk     = clamp(1 - score / 100, 0, 1);
  const riverProximity  = clamp(indFrac(result, "Nearest river distance"), 0, 1);
  const waterOccurrence = clamp(indFrac(result, "Water occurrence"), 0, 1);
  const lowLyingRisk    = clamp(indFrac(result, "Low-lying area"), 0, 1);

  const values: Record<string, number> = { overallRisk, lowLyingRisk, waterOccurrence, riverProximity };

  // Pick the dominant flood driver — the one with the highest normalised value
  const dominant = FACTORS.reduce((best, f) =>
    values[f.key] > values[best.key] ? f : best,
  );
  const v = values[dominant.key];
  const opacity = clamp(v * dominant.opacityScale, 0.12, dominant.opacityMax);

  if (boundaryPolygon && boundaryPolygon.length >= 3) {
    const cLat = boundaryPolygon.reduce((s, p) => s + p[0], 0) / boundaryPolygon.length;
    const cLng = boundaryPolygon.reduce((s, p) => s + p[1], 0) / boundaryPolygon.length;
    const avgRadDeg = polyAvgRadDeg(boundaryPolygon, cLat, cLng);

    const bufM  = dominant.bufMin + v * dominant.bufRange;
    const scale = (avgRadDeg + bufM / 111000) / avgRadDeg;

    return (
      <Polygon
        positions={scalePoly(boundaryPolygon, scale, cLat, cLng)}
        pathOptions={{ color: dominant.color, fillColor: dominant.color, fillOpacity: opacity, weight: 1.0 }}
      />
    );
  }

  // Fallback: single circle for pin-only sites
  const rScale = clamp(0.75 + overallRisk * 0.50, 0.75, 1.25);
  const radius = (dominant.bufMin + v * dominant.bufRange) * rScale;

  return (
    <Circle
      center={center}
      radius={radius}
      pathOptions={{ color: dominant.color, fillColor: dominant.color, fillOpacity: opacity, weight: 1.0 }}
    />
  );
}
