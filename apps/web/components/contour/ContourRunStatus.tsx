// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { useEffect, useState } from "react";
import { copy } from "@/lib/contour/copy";
import { useContourStore } from "@/lib/stores/contour";
import { caption } from "./theme";

function lineForElapsed(ms: number): string {
  if (ms < 3000) return copy.progress.fetching;
  if (ms < 10000) return copy.progress.contours;
  if (ms < 20000) return copy.progress.slope;
  const base = copy.progress.rendering;
  return ms >= 30000 ? `${base} ${copy.progress.slow}` : base;
}

export function ContourRunStatus() {
  const runStatus = useContourStore((s) => s.runStatus);
  const runStartedAt = useContourStore((s) => s.runStartedAt);
  const cancelledNotice = useContourStore((s) => s.cancelledNotice);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (runStatus !== "running" || runStartedAt == null) return;
    setElapsed(Date.now() - runStartedAt);
    const id = window.setInterval(() => setElapsed(Date.now() - runStartedAt), 400);
    return () => window.clearInterval(id);
  }, [runStatus, runStartedAt]);

  if (runStatus === "running") {
    return (
      <div role="status" style={{ marginTop: 8 }}>
        <div style={{ fontSize: 11, color: "#3A3F3B", fontWeight: 600 }}>{lineForElapsed(elapsed)}</div>
        <div style={{ ...caption, marginTop: 2 }}>{copy.progress.typical}</div>
      </div>
    );
  }
  if (cancelledNotice) {
    return (
      <div role="status" style={{ ...caption, marginTop: 8 }}>
        {copy.run.cancelled}
      </div>
    );
  }
  return null;
}
