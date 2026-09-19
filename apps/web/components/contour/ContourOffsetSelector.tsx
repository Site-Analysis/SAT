// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { BUFFER_PRESETS } from "@/lib/contour/constants";
import { copy } from "@/lib/contour/copy";
import { useContourStore } from "@/lib/stores/contour";
import { C, bodySm, caption } from "./theme";

export function ContourOffsetSelector() {
  const bufferM = useContourStore((s) => s.bufferM);
  const resultBufferM = useContourStore((s) => s.resultBufferM);
  const setBufferM = useContourStore((s) => s.setBufferM);
  const stale = resultBufferM != null && resultBufferM !== bufferM;

  return (
    <div>
      <label htmlFor="contour-offset" style={{ ...caption, display: "block", marginBottom: 4 }}>
        {copy.offset.label}
      </label>
      <select
        id="contour-offset"
        value={bufferM}
        onChange={(e) => setBufferM(Number(e.target.value))}
        className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-secondary"
        style={{
          width: "100%",
          height: 32,
          borderRadius: 8,
          border: `1px solid ${C.border}`,
          background: C.surface,
          color: C.ink,
          fontSize: 12,
          padding: "0 8px",
        }}
      >
        {BUFFER_PRESETS.map((n) => (
          <option key={n} value={n}>
            {n === 0 ? copy.offset.none : `${n} m`}
          </option>
        ))}
      </select>
      <div style={{ ...caption, marginTop: 4 }}>{copy.offset.hint}</div>
      {stale ? (
        <div style={{ ...bodySm, marginTop: 4 }}>{copy.run.staleOffset(resultBufferM, bufferM)}</div>
      ) : null}
    </div>
  );
}
