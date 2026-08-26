// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { useMemo } from "react";
import { CircleMarker, Marker, Polyline } from "react-leaflet";
import L from "leaflet";
import { copy } from "@/lib/contour/copy";
import { PANE } from "@/lib/contour/constants";
import { C } from "@/components/contour/theme";
import { useContourStore } from "@/lib/stores/contour";

function isLatLng(pt: unknown): pt is [number, number] {
  return (
    Array.isArray(pt) &&
    pt.length >= 2 &&
    Number.isFinite(pt[0]) &&
    Number.isFinite(pt[1])
  );
}

function useTransectPositions() {
  const draft = useContourStore((s) => s.transectDraft);
  const submitted = useContourStore((s) => s.transectSubmitted);
  const status = useContourStore((s) => s.transectStatus);
  const raw = status === "drawing" ? draft : (submitted.length >= 2 ? submitted : draft);
  return raw.filter(isLatLng);
}

export function TransectPathOverlay() {
  const positions = useTransectPositions();
  const endIcon = useMemo(
    () =>
      L.divIcon({
        className: "transect-end",
        html: `<div style="width:14px;height:14px;background:${C.end};border:2px solid #fff;transform:rotate(45deg);box-shadow:0 1px 3px rgba(0,0,0,0.3)"></div>`,
        iconSize: [14, 14],
        iconAnchor: [7, 7],
      }),
    [],
  );
  if (positions.length === 0) return null;
  const start = positions[0];
  const end = positions.length >= 2 ? positions[positions.length - 1] : null;
  const mids = positions.slice(1, -1);
  const pane = PANE.transect.name;

  return (
    <>
      {positions.length >= 2 ? (
        <>
          <Polyline pane={pane} positions={positions} pathOptions={{ color: "#fff", weight: 5, opacity: 0.9 }} />
          <Polyline
            pane={pane}
            positions={positions}
            pathOptions={{ color: C.ink, weight: 3, opacity: 1, dashArray: "8 7" }}
          />
        </>
      ) : null}
      <CircleMarker
        pane={pane}
        center={start}
        radius={7}
        pathOptions={{ fillColor: C.start, color: "#fff", weight: 2, fillOpacity: 1 }}
      />
      {mids.map((p, i) => (
        <CircleMarker
          key={`v-${i}`}
          pane={pane}
          center={p}
          radius={4}
          pathOptions={{ fillColor: "#fff", color: C.ink, weight: 2, fillOpacity: 1 }}
        />
      ))}
      {end ? (
        <Marker pane={pane} position={end} icon={endIcon} zIndexOffset={10} />
      ) : null}
    </>
  );
}

export function TransectStartEndLabels() {
  const positions = useTransectPositions();
  const startIcon = useMemo(
    () =>
      L.divIcon({
        className: "transect-start-label",
        html: `<span style="background:${C.start};color:#fff;font:700 9px/1 system-ui;padding:2px 5px;border-radius:3px">${copy.transect.startLabel}</span>`,
        iconSize: [36, 14],
        iconAnchor: [18, 22],
      }),
    [],
  );
  const endIcon = useMemo(
    () =>
      L.divIcon({
        className: "transect-end-label",
        html: `<span style="background:${C.end};color:#fff;font:700 9px/1 system-ui;padding:2px 5px;border-radius:3px">${copy.transect.endLabel}</span>`,
        iconSize: [28, 14],
        iconAnchor: [14, 22],
      }),
    [],
  );
  if (positions.length === 0) return null;
  const start = positions[0];
  const end = positions.length >= 2 ? positions[positions.length - 1] : null;
  const pane = PANE.transect.name;
  return (
    <>
      <Marker pane={pane} position={start} icon={startIcon} interactive={false} />
      {end ? <Marker pane={pane} position={end} icon={endIcon} interactive={false} /> : null}
    </>
  );
}
