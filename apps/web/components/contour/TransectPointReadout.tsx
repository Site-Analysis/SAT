// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { useEffect, useRef, useState } from "react";
import { copy } from "@/lib/contour/copy";
import { metres, pct } from "@/lib/contour/format";
import { useContourStore } from "@/lib/stores/contour";
import { C, caption, innerCard } from "./theme";

export function TransectPointReadout() {
  const [view, setView] = useState<{
    distance: number;
    elevation: number;
    slope: number;
    slopeClass: string;
  } | null>(null);
  const raf = useRef<number>(0);
  const pending = useRef<typeof view>(null);

  useEffect(() => {
    const unsub = useContourStore.subscribe(
      (s) => s.activeProfileIndex,
      (idx) => {
        const result = useContourStore.getState().transectResult;
        const pt = idx != null ? result?.points[idx] : null;
        pending.current = pt
          ? {
              distance: pt.distance_m,
              elevation: pt.elevation_m,
              slope: pt.slope_pct,
              slopeClass: String(pt.slope_class),
            }
          : null;
        if (raf.current) return;
        raf.current = requestAnimationFrame(() => {
          raf.current = 0;
          setView(pending.current);
        });
      },
    );
    return () => {
      unsub();
      if (raf.current) cancelAnimationFrame(raf.current);
    };
  }, []);

  if (!view) return null;
  return (
    <div style={{ ...innerCard, marginTop: 8 }} aria-live="polite">
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
        <div>
          <div style={caption}>{copy.transect.distance}</div>
          <div style={{ fontSize: 12, fontWeight: 700, color: C.ink }}>{metres(view.distance)}</div>
        </div>
        <div>
          <div style={caption}>{copy.transect.elevation}</div>
          <div style={{ fontSize: 12, fontWeight: 700, color: C.ink }}>{metres(view.elevation, 1)}</div>
        </div>
        <div>
          <div style={caption}>{copy.transect.slopePct}</div>
          <div style={{ fontSize: 12, fontWeight: 700, color: C.ink }}>{pct(view.slope)}</div>
        </div>
        <div>
          <div style={caption}>{copy.transect.slopeClass}</div>
          <div style={{ fontSize: 12, fontWeight: 700, color: C.ink }}>{view.slopeClass.replace(/_/g, " ")}</div>
        </div>
      </div>
    </div>
  );
}
