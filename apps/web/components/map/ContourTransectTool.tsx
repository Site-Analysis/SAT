// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { useEffect, useState } from "react";
import { Check, X } from "lucide-react";
import { Polyline, useMapEvents } from "react-leaflet";
import type { GeoJSONLike } from "@/lib/stores/analysis";

interface ContourTransectToolProps {
  active: boolean;
  polygon: GeoJSONLike;
  loading?: boolean;
  onConfirm: (line: GeoJSONLike) => void;
  onPositionsChange?: (positions: [number, number][]) => void;
  onCancel: () => void;
}

export function ContourTransectTool({
  active,
  loading = false,
  onConfirm,
  onPositionsChange,
  onCancel,
}: ContourTransectToolProps) {
  const [positions, setPositions] = useState<[number, number][]>([]);

  useEffect(() => {
    if (!active) setPositions([]);
  }, [active]);

  useEffect(() => {
    onPositionsChange?.(positions);
  }, [positions, onPositionsChange]);

  useMapEvents({
    click(e) {
      if (!active) return;
      setPositions((prev) => [...prev, [e.latlng.lat, e.latlng.lng]]);
    },
    dblclick() {
      if (!active || positions.length < 2) return;
      confirm();
    },
  });

  function confirm() {
    if (positions.length < 2) return;
    onConfirm({
      type: "LineString",
      coordinates: positions.map(([lat, lng]) => [lng, lat]),
    });
  }

  if (!active) return null;

  return (
    <>
      {positions.length > 0 && <Polyline positions={positions} pathOptions={{ color: "#fff", weight: 2, dashArray: "6 5" }} />}
      <div style={{
        position: "absolute", top: 72, left: 16, zIndex: 500, pointerEvents: "auto",
        background: "rgba(253,252,251,0.96)", border: "1px solid #CFD6C4",
        borderRadius: 8, padding: 8, display: "flex", gap: 6, alignItems: "center",
      }}>
        <span style={{ fontSize: 10, color: "#3A3F3B", marginRight: 4 }}>{positions.length} pts</span>
        <button onClick={confirm} disabled={positions.length < 2 || loading} title="Confirm transect" style={toolButton}>
          <Check size={14} />
        </button>
        <button onClick={() => { setPositions([]); onCancel(); }} title="Cancel transect" style={toolButton}>
          <X size={14} />
        </button>
      </div>
    </>
  );
}

const toolButton: React.CSSProperties = {
  width: 28,
  height: 28,
  borderRadius: 6,
  border: "1px solid #CFD6C4",
  background: "#FDFCFB",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  cursor: "pointer",
};
