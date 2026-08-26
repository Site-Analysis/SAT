// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { copy } from "@/lib/contour/copy";
import { featureCount } from "@/lib/contour/geometry";
import type { ContourEligibility } from "@/lib/contour/types";
import type { ModuleResult } from "@/lib/stores/analysis";
import { useContourStore } from "@/lib/stores/contour";
import { bodySm, caption, C } from "./theme";
import { AspectStatsSection } from "./AspectStatsSection";
import { BuildabilitySection } from "./BuildabilitySection";
import { CollapsibleSubsection } from "./CollapsibleSubsection";
import { ContourEligibilityNotice } from "./ContourEligibilityNotice";
import { ContourRunControls } from "./ContourRunControls";
import { ContourServiceStatus } from "./ContourServiceStatus";
import { DemMetadataCard } from "./DemMetadataCard";
import { LayerToggleGrid } from "./SlopeStatsSection";
import { SlopeStatsSection } from "./SlopeStatsSection";
import { TransectSection } from "./TransectSection";

interface ContourPanelProps {
  result?: ModuleResult;
  eligibility: ContourEligibility;
}

export function ContourPanel({ result: moduleResult, eligibility }: ContourPanelProps) {
  const result = useContourStore((s) => s.result);
  const layers = useContourStore((s) => s.layers);
  const toggleLayer = useContourStore((s) => s.toggleLayer);
  const resultNonce = useContourStore((s) => s.resultNonce);
  const transectResult = useContourStore((s) => s.transectResult);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <p style={{ ...bodySm, margin: 0 }}>{copy.moduleBlurb}</p>
      <p style={{ ...caption, margin: 0 }}>{copy.caveat.dsm}</p>

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        <ContourEligibilityNotice eligibility={eligibility} />
        {eligibility.eligible ? <ContourServiceStatus /> : null}
      </div>

      {!eligibility.eligible ? (
        <p style={caption}>{copy.caveat.session}</p>
      ) : (
        <>
          <ContourRunControls eligibility={eligibility} />
          {result ? (
            <>
              <CollapsibleSubsection title={copy.sections.dem} defaultOpen>
                <DemMetadataCard result={result} />
              </CollapsibleSubsection>
              <CollapsibleSubsection title={copy.sections.layers} defaultOpen>
                <LayerToggleGrid layers={layers} onToggle={toggleLayer} />
              </CollapsibleSubsection>
              <CollapsibleSubsection title={copy.sections.slope} defaultOpen>
                <SlopeStatsSection stats={result.slope_stats} moduleResult={moduleResult} />
              </CollapsibleSubsection>
              <CollapsibleSubsection title={copy.sections.aspect}>
                <AspectStatsSection stats={result.aspect_stats} />
              </CollapsibleSubsection>
              <CollapsibleSubsection
                title={copy.sections.buildability}
                footnote={<p style={{ ...caption, color: C.warn, margin: 0 }}>{copy.caveat.buildability}</p>}
              >
                <BuildabilitySection stats={result.slope_stats} />
              </CollapsibleSubsection>
              <CollapsibleSubsection title={copy.sections.transect} defaultOpen>
                <TransectSection eligibility={eligibility} />
              </CollapsibleSubsection>
              <CollapsibleSubsection title={copy.sections.advanced}>
                <div style={{ ...caption, display: "flex", flexDirection: "column", gap: 4 }}>
                  <span>{copy.advanced.contourFeatures}: {featureCount(result.contour_geojson)}</span>
                  <span>{copy.advanced.slopeFeatures}: {featureCount(result.slope_geojson)}</span>
                  <span>{copy.advanced.buildabilityFeatures}: {featureCount(result.buildability_geojson)}</span>
                  <span>{copy.advanced.sampleCount}: {transectResult?.points.length ?? "—"}</span>
                  <span>{copy.advanced.resultNonce}: {resultNonce}</span>
                </div>
              </CollapsibleSubsection>
            </>
          ) : null}
          <p style={caption}>{copy.caveat.session}</p>
        </>
      )}
    </div>
  );
}
