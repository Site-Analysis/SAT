// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { copy } from "@/lib/contour/copy";
import { demSourceLabel, metres } from "@/lib/contour/format";
import type { ContourResponse } from "@/lib/contour/types";
import { C, caption } from "./theme";
import { StatTile } from "./StatTile";

export function DemMetadataCard({ result }: { result: ContourResponse }) {
  const m = result.dem_metadata;
  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
        <StatTile label={copy.dem.source} value={demSourceLabel(m.source)} />
        <StatTile label={copy.dem.resolution} value={metres(m.resolution_m)} />
        <StatTile label={copy.dem.rmse} value={metres(m.vertical_rmse_m, 1)} />
        <StatTile label={copy.dem.interval} value={metres(m.contour_interval_m)} />
      </div>
      {m.warning ? (
        <div style={{ ...caption, color: C.warn, background: C.warnBg, borderRadius: 6, padding: "6px 8px", marginTop: 8 }}>
          {m.warning}
        </div>
      ) : null}
    </div>
  );
}
