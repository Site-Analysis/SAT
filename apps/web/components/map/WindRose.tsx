// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { Circle, Polygon } from "react-leaflet";

// We now expect the raw distribution object from the backend (e.g., { "North": 12.5, "East": 30.0 })
interface WindRoseProps {
  center: [number, number];
  distribution: Record<string, number>; 
  meanSpeed: number;
}

// 8-point compass matching backend 'Orientation' Literal
const DIRS = [
  { name: "North", bearing: 0 }, { name: "Northeast", bearing: 45 },
  { name: "East", bearing: 90 }, { name: "Southeast", bearing: 135 },
  { name: "South", bearing: 180 }, { name: "Southwest", bearing: 225 },
  { name: "West", bearing: 270 }, { name: "Northwest", bearing: 315 },
];

export function speedColor(s: number): string {
  if (s < 2)  return "#DBEAFE";
  if (s < 4)  return "#93C5FD";
  if (s < 6)  return "#3B82F6";
  if (s < 8)  return "#2563EB";
  if (s < 10) return "#F59E0B";
  if (s < 12) return "#F97316";
  return "#EF4444";
}

function dest(center: [number, number], bearingDeg: number, distM: number): [number, number] {
  const br = (bearingDeg * Math.PI) / 180;
  const dLat = (distM * Math.cos(br)) / 111320;
  const dLng = (distM * Math.sin(br)) / (111320 * Math.cos((center[0] * Math.PI) / 180));
  return [center[0] + dLat, center[1] + dLng];
}

function wedge(
  center: [number, number],
  bearing: number,
  halfWidth: number,
  ri: number,
  ro: number,
): [number, number][] {
  const pts: [number, number][] = [];
  const steps = 5;
  for (let k = 0; k <= steps; k++) {
    pts.push(dest(center, bearing - halfWidth + (2 * halfWidth * k) / steps, ro));
  }
  for (let k = steps; k >= 0; k--) {
    pts.push(dest(center, bearing - halfWidth + (2 * halfWidth * k) / steps, ri));
  }
  return pts;
}

export function WindRose({ center, distribution, meanSpeed }: WindRoseProps) {
  const R_MIN = 40;   
  const R_SPAN = 240; 
  const HALF_WIDTH = 22.5; // Wider petals for 8-point compass

  // Find the maximum frequency to scale the petals properly
  const frequencies = DIRS.map(dir => distribution[dir.name] || 0);
  const maxFreq = Math.max(...frequencies, 0.0001);

  const petals = DIRS.map((dir, i) => {
    const rawFreq = frequencies[i];
    const normalizedFreq = rawFreq / maxFreq; 
    const ro = R_MIN + (normalizedFreq * R_SPAN);
    
    // Scale color bands based on frequency and mean speed
    const dirSpeed = meanSpeed * (0.55 + 0.7 * normalizedFreq);
    const bands = [
      { ri: 0,         ro: ro * 0.5, color: speedColor(dirSpeed * 0.45) },
      { ri: ro * 0.5,  ro: ro * 0.8, color: speedColor(dirSpeed * 0.75) },
      { ri: ro * 0.8,  ro,           color: speedColor(dirSpeed) },
    ];
    return { dir, bands };
  });

  const maxRo = R_MIN + R_SPAN;

  return (
    <>
      <Circle
        center={center} radius={maxRo}
        pathOptions={{ color: "#06B6D4", weight: 1, opacity: 0.5, fill: false, dashArray: "4 4" }}
      />
      <Circle
        center={center} radius={maxRo * 0.5}
        pathOptions={{ color: "#06B6D4", weight: 0.8, opacity: 0.3, fill: false, dashArray: "3 5" }}
      />
      {petals.map(({ dir, bands }) =>
        bands.map((b, bi) => (
          <Polygon
            key={`${dir.name}-${bi}`}
            positions={wedge(center, dir.bearing, HALF_WIDTH, b.ri, b.ro)}
            pathOptions={{
              fillColor: b.color, fillOpacity: 0.82,
              color: "#FFFFFF", weight: 0.6, opacity: 0.7,
            }}
          />
        )),
      )}
      <Circle
        center={center} radius={6}
        pathOptions={{ color: "#0E7490", weight: 1.5, fillColor: "#06B6D4", fillOpacity: 1 }}
      />
    </>
  );
}