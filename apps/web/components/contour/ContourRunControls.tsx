// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { Button } from "@/components/ui/Button";
import { copy } from "@/lib/contour/copy";
import { featureCount } from "@/lib/contour/geometry";
import type { ContourEligibility } from "@/lib/contour/types";
import { useContourStore } from "@/lib/stores/contour";
import { C, caption, warnCard } from "./theme";
import { ContourIntervalSelector } from "./ContourIntervalSelector";
import { ContourOffsetSelector } from "./ContourOffsetSelector";
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
  const emptyContours = result != null && featureCount(result.contour_geojson) === 0;
  const emptyWarning = result?.dem_metadata.warning && /no contour lines/i.test(result.dem_metadata.warning)
    ? result.dem_metadata.warning
    : copy.emptyContours;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <ContourIntervalSelector />
      <ContourOffsetSelector />
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
      {emptyContours && runStatus === "succeeded" ? (
        <div role="status" style={warnCard}>
          {emptyWarning}
        </div>
      ) : null}
      {error ? (
        <div role="alert" style={{ background: C.badBg, borderRadius: 8, padding: "8px 10px" }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: C.bad }}>{error.title}</div>
          {error.detail ? <div style={{ ...caption, marginTop: 2 }}>{error.detail}</div> : null}
        </div>
      ) : null}
    </div>
  );
}
