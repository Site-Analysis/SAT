// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { CircleMarker, Polyline } from "react-leaflet";

export function TransectOverlay({ positions }: { positions: [number, number][] }) {
  if (positions.length < 2) return null;
  return (
    <>
      <Polyline positions={positions} pathOptions={{ color: "#ffffff", weight: 2, dashArray: "6 5", opacity: 0.95 }} />
      <CircleMarker center={positions[0]} radius={5} pathOptions={{ color: "#2d6a4f", fillColor: "#fff", fillOpacity: 1, weight: 2 }} />
      <CircleMarker center={positions[positions.length - 1]} radius={5} pathOptions={{ color: "#2d6a4f", fillColor: "#fff", fillOpacity: 1, weight: 2 }} />
    </>
  );
}
