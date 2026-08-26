// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { copy } from "@/lib/contour/copy";
import { pct } from "@/lib/contour/format";
import type { AspectStats } from "@/lib/contour/types";
import { bodySm } from "./theme";
import { StatTile } from "./StatTile";

export function AspectStatsSection({ stats }: { stats: AspectStats }) {
  return (
    <div>
      <p style={{ ...bodySm, margin: "0 0 8px" }}>{copy.aspect.explanation}</p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
        <StatTile label={copy.aspect.dominant} value={stats.dominant_aspect_label} />
        <StatTile label={copy.aspect.dominantDeg} value={`${Math.round(stats.dominant_aspect_deg)}°`} />
        <StatTile label={copy.aspect.north} value={pct(stats.north_facing_pct)} />
        <StatTile label={copy.aspect.south} value={pct(stats.south_facing_pct)} />
      </div>
    </div>
  );
}
