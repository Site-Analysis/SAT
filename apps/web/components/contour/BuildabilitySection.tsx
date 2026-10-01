// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { BUILDABILITY_CLASSES, SLOPE_CLASSES } from "@/lib/contour/constants";
import { copy } from "@/lib/contour/copy";
import { pct } from "@/lib/contour/format";
import type { SlopeStats } from "@/lib/contour/types";
import { C, caption, bodySm } from "./theme";

export function BuildabilitySection({ stats }: { stats: SlopeStats }) {
  return (
    <div>
      <p style={{ ...bodySm, margin: "0 0 8px", color: C.warn }}>{copy.caveat.buildability}</p>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {BUILDABILITY_CLASSES.map((row) => {
          const share = row.slopeIds.reduce((sum, id) => {
            const cls = SLOPE_CLASSES.find((s) => s.id === id);
            if (!cls) return sum;
            return sum + (stats[cls.statKey as keyof SlopeStats] as number);
          }, 0);
          return (
            <div key={row.id} style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span
                aria-hidden
                style={{
                  width: 12,
                  height: 12,
                  borderRadius: 3,
                  background: row.color,
                  flexShrink: 0,
                  border: `1px solid ${C.border}`,
                }}
              />
              <span style={{ flex: 1, fontSize: 11, color: C.ink }}>{row.label}</span>
              <span style={{ ...caption, fontWeight: 600 }}>{pct(share)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
