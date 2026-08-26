// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import L from "leaflet";
import { useMemo } from "react";
import { Pane } from "react-leaflet";
import { PANE } from "@/lib/contour/constants";
import type { GeoJSONLike } from "@/lib/contour/types";
import { useContourStore } from "@/lib/stores/contour";
import { BuildabilityLayer } from "./BuildabilityLayer";
import { ContourHillshadeLayer } from "./ContourHillshadeLayer";
import { ContourLabels } from "./ContourLabels";
import { ContourLinesLayer } from "./ContourLinesLayer";
import { SlopeClassLayer } from "./SlopeClassLayer";

export function ContourMapLayers({ sitePolygon }: { sitePolygon?: GeoJSONLike | null }) {
  const result = useContourStore((s) => s.result);
  const layers = useContourStore((s) => s.layers);
  const renderer = useMemo(() => L.canvas({ padding: 0.5 }), []);
  if (!result) return null;
  return (
    <>
      <Pane name={PANE.hillshade.name} style={{ zIndex: PANE.hillshade.zIndex }} />
      <Pane name={PANE.fill.name} style={{ zIndex: PANE.fill.zIndex }} />
      <Pane name={PANE.lines.name} style={{ zIndex: PANE.lines.zIndex }} />
      <Pane name={PANE.transect.name} style={{ zIndex: PANE.transect.zIndex }} />
      {layers.hillshade ? <ContourHillshadeLayer result={result} sitePolygon={sitePolygon} /> : null}
      {layers.slope ? <SlopeClassLayer data={result.slope_geojson} renderer={renderer} /> : null}
      {layers.buildability ? (
        <BuildabilityLayer data={result.buildability_geojson} renderer={renderer} />
      ) : null}
      {layers.contours ? (
        <>
          <ContourLinesLayer data={result.contour_geojson} />
          <ContourLabels data={result.contour_geojson} />
        </>
      ) : null}
    </>
  );
}
