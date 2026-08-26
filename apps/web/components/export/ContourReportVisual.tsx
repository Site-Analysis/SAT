// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { BUILDABILITY_CLASSES, SLOPE_CLASSES } from "@/lib/contour/constants";
import { copy } from "@/lib/contour/copy";
import { demSourceLabel, metres, pct } from "@/lib/contour/format";
import type { ContourResponse, TransectResponse } from "@/lib/contour/types";

const HEX = {
  text: "#3A3F3B",
  muted: "#7B8F83",
  border: "#CFD6C4",
  accent: "#2D6A4F",
  start: "#306223",
  end: "#B45309",
  fill: "rgba(45,106,79,0.10)",
};

interface ContourReportVisualProps {
  result: ContourResponse;
  transect?: TransectResponse | null;
}

export function ContourReportVisual({ result, transect }: ContourReportVisualProps) {
  const stats = result.slope_stats;
  const total = SLOPE_CLASSES.reduce((s, c) => s + Number(stats[c.statKey as keyof typeof stats] ?? 0), 0) || 1;
  let x = 0;
  const segs = SLOPE_CLASSES.map((c) => {
    const w = (Number(stats[c.statKey as keyof typeof stats] ?? 0) / total) * 320;
    const seg = { ...c, x, w };
    x += w;
    return seg;
  });

  return (
    <svg viewBox="0 0 360 260" width="100%" height="260" role="img" aria-label={copy.moduleTitle}>
      <text x="0" y="14" fontSize="11" fill={HEX.muted} fontWeight={700}>{copy.sections.slope}</text>
      {segs.map((s) => (
        <rect key={s.id} x={s.x} y="24" width={Math.max(s.w, 0)} height="16" fill={s.color} />
      ))}
      {SLOPE_CLASSES.map((c, i) => (
        <g key={c.id} transform={`translate(${(i % 3) * 120} ${i < 3 ? 52 : 78})`}>
          <rect width="8" height="8" fill={c.color} />
          <text x="12" y="8" fontSize="9" fill={HEX.text}>{c.label} {pct(Number(stats[c.statKey as keyof typeof stats] ?? 0))}</text>
        </g>
      ))}
      <text x="0" y="112" fontSize="10" fill={HEX.muted}>
        {demSourceLabel(result.dem_metadata.source)} · {metres(result.dem_metadata.resolution_m)} · {metres(result.dem_metadata.contour_interval_m)} interval
      </text>
      {transect && transect.points.length > 1 ? (
        <g transform="translate(0 128)">
          <text x="0" y="0" fontSize="11" fill={HEX.muted} fontWeight={700}>{copy.sections.transect}</text>
          {(() => {
            const pts = transect.points;
            const min = transect.min_elevation_m;
            const max = transect.max_elevation_m;
            const span = max - min || 1;
            const totalL = transect.total_length_m || 1;
            const d = pts.map((p, i) => {
              const px = 20 + (p.distance_m / totalL) * 320;
              const py = 90 - ((p.elevation_m - min) / span) * 70;
              return `${i === 0 ? "M" : "L"}${px.toFixed(1)},${py.toFixed(1)}`;
            }).join("");
            return (
              <>
                <path d={d} fill="none" stroke={HEX.accent} strokeWidth="2" />
                <circle cx={20} cy={90 - ((pts[0].elevation_m - min) / span) * 70} r="4" fill={HEX.start} />
                <rect
                  x={340 - 4}
                  y={90 - ((pts[pts.length - 1].elevation_m - min) / span) * 70 - 4}
                  width="8"
                  height="8"
                  fill={HEX.end}
                  transform={`rotate(45 340 ${90 - ((pts[pts.length - 1].elevation_m - min) / span) * 70})`}
                />
                <text x="20" y="108" fontSize="9" fill={HEX.start}>{copy.transect.startLabel}</text>
                <text x="340" y="108" fontSize="9" fill={HEX.end} textAnchor="end">{copy.transect.endLabel}</text>
              </>
            );
          })()}
        </g>
      ) : null}
    </svg>
  );
}

export function ContourReportExtras({ result, transect }: ContourReportVisualProps) {
  const s = result.slope_stats;
  const a = result.aspect_stats;
  return (
    <div style={{ fontSize: 10, color: HEX.text, lineHeight: 1.45 }}>
      <div style={{ marginBottom: 6, color: HEX.muted }}>{copy.caveat.dsm}</div>
      <div style={{ marginBottom: 6, color: HEX.muted }}>{copy.report.disclaimer}</div>
      <div style={{ marginBottom: 6, color: "#C4865A" }}>{copy.caveat.buildability}</div>
      <div>Mean {pct(s.mean_slope_pct)} · Max {pct(s.max_slope_pct)} · Aspect {a.dominant_aspect_label} {Math.round(a.dominant_aspect_deg)}°</div>
      <div style={{ marginTop: 4 }}>
        {BUILDABILITY_CLASSES.map((c) => c.label).join(" · ")}
      </div>
      {transect ? (
        <div style={{ marginTop: 4 }}>
          Transect {metres(transect.total_length_m)} · relief {metres(transect.relief_m, 1)}
        </div>
      ) : null}
    </div>
  );
}
