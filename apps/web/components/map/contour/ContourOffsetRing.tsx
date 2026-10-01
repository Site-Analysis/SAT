// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { Polyline } from "react-leaflet";
import { PANE } from "@/lib/contour/constants";
import { offsetRingLatLngs } from "@/lib/contour/geometry";
import type { GeoJSONLike } from "@/lib/contour/types";
import { C } from "@/components/contour/theme";
import { useContourStore } from "@/lib/stores/contour";

export function ContourOffsetRing({ sitePolygon }: { sitePolygon?: GeoJSONLike | null }) {
  const result = useContourStore((s) => s.result);
  const bufferM = result?.dem_metadata.buffer_m ?? 0;
  if (!sitePolygon || !(bufferM > 0)) return null;
  const positions = offsetRingLatLngs(sitePolygon, bufferM);
  if (!positions || positions.length < 2) return null;
  return (
    <Polyline
      pane={PANE.lines.name}
      positions={positions}
      pathOptions={{ color: C.inkSoft, weight: 2, dashArray: "6 6", opacity: 0.85 }}
      interactive={false}
    />
  );
}
