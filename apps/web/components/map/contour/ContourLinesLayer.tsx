// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import L from "leaflet";
import { useMemo } from "react";
import { GeoJSON } from "react-leaflet";
import { CONTOUR_STROKE, MAX_SVG_FEATURES, PANE } from "@/lib/contour/constants";
import { featureProp } from "@/lib/contour/format";
import { featureCount } from "@/lib/contour/geometry";
import type { GeoJSONLike } from "@/lib/contour/types";
import { useContourStore } from "@/lib/stores/contour";

export function ContourLinesLayer({ data }: { data: GeoJSONLike }) {
  const nonce = useContourStore((s) => s.resultNonce);
  const n = featureCount(data);
  const renderer = useMemo(
    () => (n > MAX_SVG_FEATURES ? L.canvas({ padding: 0.5 }) : undefined),
    [n],
  );
  return (
    <GeoJSON
      key={`contours-${nonce}`}
      data={data as unknown as GeoJSON.GeoJsonObject}
      pane={PANE.lines.name}
      style={(feature) => {
        const isIndex = Boolean(featureProp<boolean>(feature, "is_index"));
        const stroke = isIndex ? CONTOUR_STROKE.index : CONTOUR_STROKE.regular;
        return { color: stroke.color, weight: stroke.weight, opacity: stroke.opacity, renderer };
      }}
      onEachFeature={(feature, layer) => {
        const elev = featureProp<number>(feature, "elevation");
        if (elev != null) layer.bindTooltip(`${elev} m`, { sticky: true });
      }}
    />
  );
}
