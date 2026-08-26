// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { BUILDABILITY_CLASSES, SLOPE_CLASSES } from "@/lib/contour/constants";
import { copy } from "@/lib/contour/copy";
import { featureCount } from "@/lib/contour/geometry";
import { MAX_TOOLTIP_FEATURES } from "@/lib/contour/constants";
import { useContourStore } from "@/lib/stores/contour";
import { C, caption, hudCard } from "@/components/contour/theme";

function SwatchRow({ color, label, range }: { color: string; label: string; range?: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
      <span aria-hidden style={{ width: 10, height: 10, borderRadius: 2, background: color, border: `1px solid ${C.border}`, flexShrink: 0 }} />
      <span style={{ fontSize: 10.5, color: C.ink, flex: 1 }}>{label}</span>
      {range ? <span style={{ ...caption }}>{range}</span> : null}
    </div>
  );
}

export function ContourLegend() {
  const result = useContourStore((s) => s.result);
  const layers = useContourStore((s) => s.layers);
  const opacity = useContourStore((s) => s.hillshadeOpacity);
  if (!result) return null;
  const interval = result.dem_metadata.contour_interval_m;
  const approx = !result.hillshade_bounds;
  const slopeHeavy = featureCount(result.slope_geojson) > MAX_TOOLTIP_FEATURES;

  return (
    <div
      style={{
        ...hudCard,
        position: "absolute",
        bottom: 76,
        left: "50%",
        transform: "translateX(-50%)",
        zIndex: 420,
        minWidth: 220,
        maxWidth: 280,
        pointerEvents: "auto",
      }}
    >
      {layers.hillshade ? (
        <div style={{ marginBottom: 8 }}>
          <div style={caption}>{copy.legend.hillshade(Math.round(opacity * 100))}</div>
          {approx ? <div style={{ ...caption, color: C.warn, marginTop: 2 }}>{copy.legend.hillshadeApprox}</div> : null}
        </div>
      ) : null}
      {layers.contours ? (
        <div style={{ marginBottom: 8 }}>
          <div style={caption}>{copy.legend.contours(interval, interval * 5)}</div>
        </div>
      ) : null}
      {layers.slope ? (
        <div style={{ marginBottom: 8 }}>
          <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: "0.5px", textTransform: "uppercase", color: C.inkSoft, marginBottom: 6 }}>
            {copy.legend.slopeTitle}
          </div>
          {SLOPE_CLASSES.map((c) => (
            <SwatchRow key={c.id} color={c.color} label={c.label} range={c.range} />
          ))}
          <div style={{ ...caption, marginTop: 4 }}>{copy.caveat.slopeLayer}</div>
          {slopeHeavy ? <div style={{ ...caption, color: C.warn }}>{copy.errors.geometrySimplified}</div> : null}
        </div>
      ) : null}
      {layers.buildability ? (
        <div>
          <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: "0.5px", textTransform: "uppercase", color: C.inkSoft, marginBottom: 6 }}>
            {copy.legend.buildabilityTitle}
          </div>
          {BUILDABILITY_CLASSES.map((c) => (
            <SwatchRow key={c.id} color={c.color} label={c.label} />
          ))}
          <div style={{ ...caption, color: C.warn, marginTop: 4 }}>{copy.caveat.buildability}</div>
        </div>
      ) : null}
    </div>
  );
}
