// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import L from "leaflet";
import { GeoJSON } from "react-leaflet";
import { BUILDABILITY_CLASSES, MAX_TOOLTIP_FEATURES, PANE } from "@/lib/contour/constants";
import { featureProp } from "@/lib/contour/format";
import { featureCount } from "@/lib/contour/geometry";
import type { GeoJSONLike } from "@/lib/contour/types";
import { useContourStore } from "@/lib/stores/contour";

export function BuildabilityLayer({ data, renderer }: { data: GeoJSONLike; renderer: L.Renderer }) {
  const nonce = useContourStore((s) => s.resultNonce);
  const n = featureCount(data);
  const tooltips = n <= MAX_TOOLTIP_FEATURES;
  return (
    <GeoJSON
      key={`buildability-${nonce}`}
      data={data as unknown as GeoJSON.GeoJsonObject}
      pane={PANE.fill.name}
      style={(feature) => ({
        color: featureProp<string>(feature, "color") ?? "#2d6a4f",
        fillColor: featureProp<string>(feature, "color") ?? "#2d6a4f",
        weight: 0.8,
        fillOpacity: 0.42,
        opacity: 0.8,
        renderer,
      })}
      onEachFeature={(feature, layer) => {
        if (!tooltips) return;
        const raw = featureProp<string>(feature, "buildability_class");
        const label = BUILDABILITY_CLASSES.find((c) => c.id === raw)?.label ?? raw;
        if (label) layer.bindTooltip(label, { sticky: true });
      }}
    />
  );
}
