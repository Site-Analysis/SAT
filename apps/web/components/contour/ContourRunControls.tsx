// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { Button } from "@/components/ui/Button";
import { copy } from "@/lib/contour/copy";
import type { ContourEligibility } from "@/lib/contour/types";
import { useContourStore } from "@/lib/stores/contour";
import { C, caption } from "./theme";
import { ContourIntervalSelector } from "./ContourIntervalSelector";
import { ContourRunStatus } from "./ContourRunStatus";

export function ContourRunControls({ eligibility }: { eligibility: ContourEligibility }) {
  const runStatus = useContourStore((s) => s.runStatus);
  const result = useContourStore((s) => s.result);
  const interval = useContourStore((s) => s.interval);
  const error = useContourStore((s) => s.error);
  const runAnalysis = useContourStore((s) => s.runAnalysis);
  const cancelRun = useContourStore((s) => s.cancelRun);
  const running = runStatus === "running";
  const label = result ? copy.run.again(interval) : copy.run.first;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <ContourIntervalSelector />
      <div style={{ display: "flex", gap: 8 }}>
        <Button
          size="sm"
          variant="primary"
          loading={running}
          disabled={running || !eligibility.eligible}
          onClick={() => {
            if (!eligibility.eligible) return;
            void runAnalysis(eligibility.polygon);
          }}
        >
          {label}
        </Button>
        {running ? (
          <Button size="sm" variant="ghost" onClick={() => cancelRun()}>
            {copy.run.cancel}
          </Button>
        ) : null}
      </div>
      <ContourRunStatus />
      {error ? (
        <div role="alert" style={{ background: C.badBg, borderRadius: 8, padding: "8px 10px" }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.bad }}>{error.title}</div>
          {error.detail ? <div style={{ ...caption, marginTop: 2 }}>{error.detail}</div> : null}
        </div>
      ) : null}
    </div>
  );
}
