// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { copy } from "@/lib/contour/copy";
import { useContourStore } from "@/lib/stores/contour";
import { C, hudBadge } from "@/components/contour/theme";

export function ContourMapStatus() {
  const runStatus = useContourStore((s) => s.runStatus);
  const transectStatus = useContourStore((s) => s.transectStatus);
  const running = runStatus === "running" || transectStatus === "running";
  if (!running) return null;
  return (
    <div
      role="status"
      style={{
        ...hudBadge,
        position: "absolute",
        top: 14,
        left: 14,
        zIndex: 430,
        pointerEvents: "none",
      }}
    >
      <div style={{ fontSize: 11, fontWeight: 600, color: C.ink }}>
        {transectStatus === "running" ? copy.progress.mapTransect : copy.progress.mapRunning}
      </div>
    </div>
  );
}
