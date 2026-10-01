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

function bearingDeg(from: [number, number], to: [number, number]): number {
  const dLng = ((to[1] - from[1]) * Math.PI) / 180;
  const lat1 = (from[0] * Math.PI) / 180;
  const lat2 = (to[0] * Math.PI) / 180;
  const y = Math.sin(dLng) * Math.cos(lat2);
  const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLng);
  return ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360;
}

function sectionArrowIcon(color: string, label: string, rotation: number) {
  return L.divIcon({
    className: "transect-section-arrow",
    html: `<div style="display:flex;flex-direction:column;align-items:center;transform:rotate(${rotation}deg);transform-origin:50% 50%">
      <div style="width:0;height:0;border-left:7px solid transparent;border-right:7px solid transparent;border-bottom:12px solid ${color};filter:drop-shadow(0 1px 1px rgba(0,0,0,0.35))"></div>
      <span style="margin-top:2px;background:${color};color:#fff;font:700 9px/1 system-ui;padding:2px 5px;border-radius:3px;transform:rotate(${-rotation}deg)">${label}</span>
    </div>`,
    iconSize: [28, 32],
    iconAnchor: [14, 6],
  });
}

export function TransectPathOverlay() {
  const positions = useTransectPositions();
  if (positions.length === 0) return null;
  const start = positions[0];
  const end = positions.length >= 2 ? positions[positions.length - 1] : null;
  const mids = positions.slice(1, -1);
  const pane = PANE.transect.name;

  return (
    <>
      {positions.length >= 2 ? (
        <>
          <Polyline pane={pane} positions={positions} pathOptions={{ color: "#fff", weight: 5, opacity: 0.9 }} interactive={false} />
          <Polyline
            pane={pane}
            positions={positions}
            pathOptions={{ color: C.ink, weight: 3, opacity: 1, dashArray: "8 7" }}
            interactive={false}
          />
        </>
      ) : null}
      <CircleMarker
        pane={pane}
        center={start}
        radius={5}
        pathOptions={{ fillColor: C.start, color: "#fff", weight: 2, fillOpacity: 1 }}
        interactive={false}
      />
      {mids.map((p, i) => (
        <CircleMarker
          key={`v-${i}`}
          pane={pane}
          center={p}
          radius={4}
          pathOptions={{ fillColor: "#fff", color: C.ink, weight: 2, fillOpacity: 1 }}
          interactive={false}
        />
      ))}
      {end ? (
        <CircleMarker
          pane={pane}
          center={end}
          radius={5}
          pathOptions={{ fillColor: C.end, color: "#fff", weight: 2, fillOpacity: 1 }}
          interactive={false}
        />
      ) : null}
    </>
  );
}

export function TransectStartEndLabels() {
  const positions = useTransectPositions();
  const startIcon = useMemo(() => {
    if (positions.length < 2) return null;
    const rot = (bearingDeg(positions[0], positions[1]) - 90 + 360) % 360;
    return sectionArrowIcon(C.start, copy.transect.startLabel, rot);
  }, [positions]);
  const endIcon = useMemo(() => {
    if (positions.length < 2) return null;
    const a = positions[positions.length - 2];
    const b = positions[positions.length - 1];
    const rot = (bearingDeg(a, b) - 90 + 360) % 360;
    return sectionArrowIcon(C.end, copy.transect.endLabel, rot);
  }, [positions]);
  if (positions.length < 2 || !startIcon || !endIcon) return null;
  const start = positions[0];
  const end = positions[positions.length - 1];
  const pane = PANE.transect.name;
  return (
    <>
      <Marker pane={pane} position={start} icon={startIcon} interactive={false} />
      <Marker pane={pane} position={end} icon={endIcon} interactive={false} />
    </>
  );
}
