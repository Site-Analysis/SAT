// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { CONTOUR_INTERVALS } from "@/lib/contour/constants";
import { copy } from "@/lib/contour/copy";
import { useContourStore } from "@/lib/stores/contour";
import { C, bodySm, caption } from "./theme";

export function ContourIntervalSelector() {
  const interval = useContourStore((s) => s.interval);
  const resultInterval = useContourStore((s) => s.resultInterval);
  const intervalError = useContourStore((s) => s.intervalError);
  const setInterval = useContourStore((s) => s.setInterval);
  const stale = resultInterval != null && interval !== resultInterval;

  return (
    <div>
      <label htmlFor="contour-interval" style={{ ...caption, display: "block", marginBottom: 4 }}>
        {copy.interval.label}
      </label>
      <select
        id="contour-interval"
        value={interval}
        onChange={(e) => setInterval(Number(e.target.value))}
        className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-secondary"
        style={{
          width: "100%",
          height: 32,
          borderRadius: 8,
          border: `1px solid ${intervalError ? C.bad : C.border}`,
          background: C.surface,
          color: C.ink,
          fontSize: 12,
          padding: "0 8px",
        }}
      >
        {CONTOUR_INTERVALS.map((n) => (
          <option key={n} value={n}>
            {n} m
          </option>
        ))}
      </select>
      <div style={{ ...caption, marginTop: 4 }}>{copy.interval.hint}</div>
      {interval === 10 ? (
        <div style={{ ...caption, color: C.warn, marginTop: 4 }}>{copy.interval.minWarning}</div>
      ) : null}
      {intervalError ? (
        <div role="alert" style={{ ...caption, color: C.bad, marginTop: 4 }}>
          {intervalError}
        </div>
      ) : null}
      {stale ? (
        <div style={{ ...bodySm, marginTop: 4 }}>{copy.run.stale(resultInterval, interval)}</div>
      ) : null}
    </div>
  );
}
