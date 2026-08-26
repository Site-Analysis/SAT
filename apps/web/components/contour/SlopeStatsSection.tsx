// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { ModuleChart } from "@/components/layout/ModuleChart";
import { Toggle } from "@/components/ui/Toggle";
import { SLOPE_CLASSES } from "@/lib/contour/constants";
import { copy } from "@/lib/contour/copy";
import { pct } from "@/lib/contour/format";
import type { SlopeStats } from "@/lib/contour/types";
import type { ModuleResult } from "@/lib/stores/analysis";
import type { ContourLayerId } from "@/lib/contour/types";
import { C } from "./theme";
import { InfoTip } from "./InfoTip";
import { StatTile } from "./StatTile";

const STATS: Array<{ key: keyof SlopeStats; label: string; help: string }> = [
  { key: "mean_slope_pct", label: copy.slopeLabels.mean, help: copy.slopeHelp.mean },
  { key: "max_slope_pct", label: copy.slopeLabels.max, help: copy.slopeHelp.max },
  { key: "flat_area_pct", label: copy.slopeLabels.flat, help: copy.slopeHelp.flat },
  { key: "gentle_area_pct", label: copy.slopeLabels.gentle, help: copy.slopeHelp.gentle },
  { key: "moderate_area_pct", label: copy.slopeLabels.moderate, help: copy.slopeHelp.moderate },
  { key: "steep_area_pct", label: copy.slopeLabels.steep, help: copy.slopeHelp.steep },
  { key: "very_steep_area_pct", label: copy.slopeLabels.verySteep, help: copy.slopeHelp.verySteep },
  { key: "hazard_area_pct", label: copy.slopeLabels.hazard, help: copy.slopeHelp.hazard },
];

export function SlopeStatsSection({ stats, moduleResult }: { stats: SlopeStats; moduleResult?: ModuleResult }) {
  const total = SLOPE_CLASSES.reduce((s, c) => s + (stats[c.statKey as keyof SlopeStats] as number), 0) || 1;
  const aria = SLOPE_CLASSES.map((c) => `${c.label} ${pct(stats[c.statKey as keyof SlopeStats] as number)}`).join(", ");
  const chart = moduleResult?.charts?.find((ch) => ch.title === "Slope class share");

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <div
        role="img"
        aria-label={`Slope class share: ${aria}`}
        style={{ display: "flex", height: 14, borderRadius: 4, overflow: "hidden", background: C.border }}
      >
        {SLOPE_CLASSES.map((c) => {
          const v = stats[c.statKey as keyof SlopeStats] as number;
          return (
            <div
              key={c.id}
              style={{ width: `${(v / total) * 100}%`, background: c.color, height: "100%" }}
              title={`${c.label} ${pct(v)}`}
            />
          );
        })}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
        {STATS.map((s) => (
          <StatTile
            key={s.key}
            label={s.label}
            value={pct(stats[s.key])}
            info={<InfoTip label={s.label} text={s.help} />}
          />
        ))}
      </div>
      {chart ? <ModuleChart chart={chart} height={120} /> : null}
    </div>
  );
}

export function LayerToggleGrid({
  layers,
  onToggle,
}: {
  layers: Record<ContourLayerId, boolean>;
  onToggle: (id: ContourLayerId) => void;
}) {
  const rows: Array<{ id: ContourLayerId; label: string }> = [
    { id: "hillshade", label: copy.layers.hillshade },
    { id: "contours", label: copy.layers.contours },
    { id: "slope", label: copy.layers.slope },
    { id: "buildability", label: copy.layers.buildability },
  ];
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
      {rows.map((r) => (
        <Toggle key={r.id} label={r.label} checked={layers[r.id]} onChange={() => onToggle(r.id)} />
      ))}
    </div>
  );
}
