// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { copy } from "@/lib/contour/copy";
import type { ContourLayerId } from "@/lib/contour/types";
import { useContourStore } from "@/lib/stores/contour";
import { C, glassPill } from "@/components/contour/theme";

const ROWS: Array<{ id: ContourLayerId; label: string; swatch: string }> = [
  { id: "hillshade", label: copy.layers.hillshade, swatch: "#7B8F83" },
  { id: "contours", label: copy.layers.contours, swatch: "#2D6A4F" },
  { id: "slope", label: copy.layers.slope, swatch: "#f4a261" },
  { id: "buildability", label: copy.layers.buildability, swatch: "#52b788" },
];

export function ContourLayerControl() {
  const layers = useContourStore((s) => s.layers);
  const toggle = useContourStore((s) => s.toggleLayer);
  const result = useContourStore((s) => s.result);
  if (!result) return null;
  return (
    <div
      style={{
        ...glassPill,
        position: "absolute",
        top: 84,
        right: 16,
        zIndex: 430,
        padding: "10px 12px",
        minWidth: 168,
        pointerEvents: "auto",
      }}
    >
      <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: "0.5px", textTransform: "uppercase", color: C.inkSoft, marginBottom: 8 }}>
        {copy.sections.layers}
      </div>
      {ROWS.map((row) => {
        const on = layers[row.id];
        return (
          <button
            key={row.id}
            type="button"
            role="switch"
            aria-checked={on}
            aria-label={row.label}
            onClick={() => toggle(row.id)}
            className="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-secondary"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              width: "100%",
              background: "none",
              border: "none",
              padding: "4px 0",
              cursor: "pointer",
              color: on ? C.ink : C.inkSoft,
              font: "600 12px/1 system-ui, sans-serif",
            }}
          >
            <span aria-hidden style={{ width: 8, height: 8, borderRadius: 2, background: row.swatch }} />
            <span style={{ flex: 1, textAlign: "left" }}>{row.label}</span>
            <span
              aria-hidden
              style={{
                width: 26,
                height: 15,
                borderRadius: 999,
                background: on ? C.primary : C.border,
                position: "relative",
                flexShrink: 0,
              }}
            >
              <span
                style={{
                  position: "absolute",
                  top: 2,
                  left: on ? 13 : 2,
                  width: 11,
                  height: 11,
                  borderRadius: "50%",
                  background: C.surface,
                  boxShadow: "0 1px 2px rgba(0,0,0,0.3)",
                }}
              />
            </span>
          </button>
        );
      })}
    </div>
  );
}
