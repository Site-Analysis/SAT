// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import type { ModuleResult } from "@/lib/stores/analysis";

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MONSOON = [false, false, false, false, false, true, true, true, true, false, false, false];

function monthly(result: ModuleResult): number[] {
  const pts = result.charts?.find((c) => c.title === "Monthly rainfall")?.points;
  return pts?.map((p) => Number(p.value) || 0) ?? [];
}

export function RainfallRadar({ result, size = 240 }: { result: ModuleResult; size?: number }) {
  const months = monthly(result);
  if (months.length < 12) return null;

  const W = size, H = size;
  const cx = W / 2, cy = H / 2;
  // 30px margin on each side: 18px for label text + 12px breathing room
  const MARGIN = 30;
  const LABEL_R = cx - MARGIN;
  const MAX_R = LABEL_R - 18;
  const maxMo = Math.max(1, ...months);

  const pts = months.map((v, i) => {
    const angle = (i / 12) * 2 * Math.PI - Math.PI / 2;
    const r = (v / maxMo) * MAX_R;
    return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
  });
  const polyPoints = pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
  const ringValues = [1, 2, 3, 4].map((n) => Math.round((n / 4) * maxMo));

  return (
    <div style={{ width: "100%" }}>
      <div style={{
        background: "#F2EDE8",
        borderRadius: 12,
        overflow: "hidden",
      }}>
        <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ display: "block" }}>

          {/* Concentric scale rings */}
          {[1, 2, 3, 4].map((n) => (
            <circle
              key={n}
              cx={cx} cy={cy}
              r={(n / 4) * MAX_R}
              fill="none"
              stroke="#CFD6C4"
              strokeWidth={n === 4 ? 1 : 0.7}
              strokeDasharray={n < 4 ? "3 4" : undefined}
            />
          ))}

          {/* Radial spokes + month labels */}
          {MONTHS.map((label, i) => {
            const angle = (i / 12) * 2 * Math.PI - Math.PI / 2;
            const lx = cx + LABEL_R * Math.cos(angle);
            const ly = cy + LABEL_R * Math.sin(angle);
            const sx = cx + MAX_R * Math.cos(angle);
            const sy = cy + MAX_R * Math.sin(angle);
            const anchor = lx < cx - 6 ? "end" : lx > cx + 6 ? "start" : "middle";
            return (
              <g key={label}>
                <line
                  x1={cx} y1={cy} x2={sx} y2={sy}
                  stroke="#CFD6C4" strokeWidth={0.7}
                />
                <text
                  x={lx} y={ly}
                  textAnchor={anchor}
                  dominantBaseline="middle"
                  fontSize={8.5}
                  fontFamily="inherit"
                  fill={MONSOON[i] ? "#1D4ED8" : "#7B8F83"}
                  fontWeight={MONSOON[i] ? 700 : 400}
                >
                  {label}
                </text>
              </g>
            );
          })}

          {/* Scale mm labels on the Jan (top) spoke, offset slightly right */}
          {[1, 2, 3].map((n) => {
            const r = (n / 4) * MAX_R;
            return (
              <text
                key={n}
                x={cx + 4} y={cy - r + 1}
                fontSize={6.5}
                fontFamily="inherit"
                fill="#B8C4BB"
                textAnchor="start"
              >
                {ringValues[n - 1]}
              </text>
            );
          })}
          {/* Outermost ring label */}
          <text
            x={cx + 4} y={cy - MAX_R + 1}
            fontSize={6.5}
            fontFamily="inherit"
            fill="#7B8F83"
            textAnchor="start"
            fontWeight={600}
          >
            {ringValues[3]} mm
          </text>

          {/* Data polygon */}
          <polygon
            points={polyPoints}
            fill="rgba(29,78,216,0.11)"
            stroke="#1D4ED8"
            strokeWidth={1.5}
            strokeLinejoin="round"
          />

          {/* Vertex dots */}
          {pts.map((p, i) => (
            <circle
              key={i}
              cx={p.x} cy={p.y} r={2.5}
              fill={MONSOON[i] ? "#1D4ED8" : "#93C5FD"}
              stroke="#FDFCFB"
              strokeWidth={0.8}
            />
          ))}

          {/* Center pivot */}
          <circle cx={cx} cy={cy} r={3} fill="#3A3F3B" />
        </svg>
      </div>
    </div>
  );
}
