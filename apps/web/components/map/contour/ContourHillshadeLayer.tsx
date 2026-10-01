// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { useMemo } from "react";
import { ImageOverlay } from "react-leaflet";
import { HILLSHADE_OPACITY, PANE } from "@/lib/contour/constants";
import { bboxOfPolygon } from "@/lib/contour/geometry";
import type { ContourResponse, GeoJSONLike } from "@/lib/contour/types";
import { useContourStore } from "@/lib/stores/contour";

export function ContourHillshadeLayer({
  result,
  sitePolygon,
}: {
  result: ContourResponse;
  sitePolygon?: GeoJSONLike | null;
}) {
  const opacity = useContourStore((s) => s.hillshadeOpacity) || HILLSHADE_OPACITY;
  const nonce = useContourStore((s) => s.resultNonce);
  const url = useMemo(
    () => `data:image/png;base64,${result.hillshade_png_b64}`,
    // nonce is the cache key so a re-run re-decodes
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [nonce, result.hillshade_png_b64],
  );
  const bounds = result.hillshade_bounds
    ?? (sitePolygon ? bboxOfPolygon(sitePolygon) : null);
  if (!bounds) return null;
  return (
    <ImageOverlay
      url={url}
      bounds={bounds}
      opacity={opacity}
      interactive={false}
      pane={PANE.hillshade.name}
    />
  );
}
