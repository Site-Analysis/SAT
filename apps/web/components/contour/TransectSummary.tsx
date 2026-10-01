// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { copy } from "@/lib/contour/copy";
import { demSourceLabel, metres } from "@/lib/contour/format";
import type { TransectResponse } from "@/lib/contour/types";
import { StatTile } from "./StatTile";

export function TransectSummary({ result }: { result: TransectResponse }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6, marginBottom: 10 }}>
      <StatTile label={copy.transect.length} value={metres(result.total_length_m)} />
      <StatTile label={copy.transect.minElev} value={metres(result.min_elevation_m, 1)} />
      <StatTile label={copy.transect.maxElev} value={metres(result.max_elevation_m, 1)} />
      <StatTile label={copy.transect.relief} value={metres(result.relief_m, 1)} />
      <StatTile label={copy.dem.source} value={demSourceLabel(result.dem_source)} />
      <StatTile label={copy.transect.samples} value={String(result.points.length)} />
    </div>
  );
}
