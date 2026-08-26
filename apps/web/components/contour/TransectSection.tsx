// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { Button } from "@/components/ui/Button";
import { copy } from "@/lib/contour/copy";
import type { ContourEligibility } from "@/lib/contour/types";
import { useContourStore } from "@/lib/stores/contour";
import { C, bodySm, caption } from "./theme";
import { TransectPointReadout } from "./TransectPointReadout";
import { TransectProfileChart } from "./TransectProfileChart";
import { TransectSummary } from "./TransectSummary";

export function TransectSection({ eligibility }: { eligibility: ContourEligibility }) {
  const canDraw = useContourStore((s) => s.runStatus === "succeeded" && !!s.result);
  const status = useContourStore((s) => s.transectStatus);
  const draft = useContourStore((s) => s.transectDraft);
  const result = useContourStore((s) => s.transectResult);
  const error = useContourStore((s) => s.transectError);
  const startTransect = useContourStore((s) => s.startTransect);
  const finishTransectDrawing = useContourStore((s) => s.finishTransectDrawing);
  const clearTransect = useContourStore((s) => s.clearTransect);
  const runTransect = useContourStore((s) => s.runTransect);
  const drawing = status === "drawing";
  const running = status === "running";
  const ready = status === "ready" || (draft.length >= 2 && (status === "drawing" || status === "failed"));

  if (!canDraw) {
    return <div style={{ ...bodySm, color: C.warn }}>{copy.transect.needsAnalysis}</div>;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      <p style={bodySm}>{copy.transect.instructions}</p>
      <p style={caption}>{copy.transect.cost}</p>
      <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
        <Button size="sm" variant={drawing ? "secondary" : "primary"} onClick={() => startTransect()} disabled={running}>
          {copy.transect.start}
        </Button>
        <Button
          size="sm"
          variant="secondary"
          disabled={!drawing || draft.length < 2 || running}
          onClick={() => finishTransectDrawing()}
        >
          {copy.transect.stop}
        </Button>
        <Button
          size="sm"
          variant="primary"
          loading={running}
          disabled={running || (!ready && draft.length < 2 && !result)}
          onClick={() => {
            if (!eligibility.eligible) return;
            void runTransect(eligibility.polygon);
          }}
        >
          {copy.transect.run}
        </Button>
        {running ? (
          <Button size="sm" variant="ghost" onClick={() => useContourStore.getState().cancelRun()}>
            {copy.run.cancel}
          </Button>
        ) : null}
        <Button size="sm" variant="ghost" onClick={() => clearTransect()} disabled={running}>
          {copy.transect.clear}
        </Button>
      </div>
      {drawing ? <div style={caption}>{copy.transect.pointCount(draft.length)}</div> : null}
      {error ? (
        <div role="alert" style={{ background: C.badBg, borderRadius: 8, padding: "8px 10px" }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.bad }}>{error.title}</div>
          {error.detail ? <div style={{ ...caption, marginTop: 2 }}>{error.detail}</div> : null}
        </div>
      ) : null}
      {running ? <div role="status" style={bodySm}>{copy.transect.running}</div> : null}
      {result ? (
        <>
          <TransectSummary result={result} />
          <TransectProfileChart result={result} />
          <TransectPointReadout />
        </>
      ) : null}
    </div>
  );
}
