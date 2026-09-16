// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import React, { useMemo } from "react";
import { GeoJSON, Circle, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import type { PathOptions } from "leaflet";

const BOUNDARY_STYLE: PathOptions = {
  color: "#306223",
  weight: 1.5,
  fillColor: "#DAEBE3",
  fillOpacity: 0.12, // Reduced fill opacity so it acts as subtle background boundary
};

export interface SiteBoundaryOverlayProps {
  shape: "circle" | "polygon";
  coordinates:
    | { center: [number, number]; radius: number }
    | [number, number][];
}

export function SiteBoundaryOverlay({
  shape,
  coordinates,
}: SiteBoundaryOverlayProps) {
  const centroid: [number, number] | null = useMemo(() => {
    if (shape === "circle" && !Array.isArray(coordinates)) {
      return coordinates.center;
    }
    if (shape === "polygon" && Array.isArray(coordinates) && coordinates.length > 0) {
      const latSum = coordinates.reduce((s, p) => s + p[0], 0);
      const lngSum = coordinates.reduce((s, p) => s + p[1], 0);
      return [latSum / coordinates.length, lngSum / coordinates.length];
    }
    return null;
  }, [shape, coordinates]);

  const markerIcon = useMemo(() => {
    if (typeof window === "undefined") return null;
    return L.divIcon({
      className: "site-centroid-marker",
      html: `
        <div style="position:relative; width:32px; height:32px; display:flex; align-items:center; justify-content:center; transform:translate(-50%, -50%); pointer-events:auto; cursor:pointer;">
          <div style="position:absolute; width:32px; height:32px; border-radius:50%; background:rgba(48, 98, 35, 0.35); animation:sat-pulse 2s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>
          <div style="position:absolute; width:18px; height:18px; border-radius:50%; background:#0F172A; border:2.5px solid #FFFFFF; box-shadow:0 2px 8px rgba(0,0,0,0.45); display:flex; align-items:center; justify-content:center;">
            <div style="width:6px; height:6px; border-radius:50%; background:#22C55E;"></div>
          </div>
        </div>
      `,
      iconSize: [0, 0],
      iconAnchor: [0, 0],
    });
  }, []);

  return (
    <>
      {shape === "circle" && !Array.isArray(coordinates) && (
        <Circle
          center={coordinates.center}
          radius={coordinates.radius}
          pathOptions={BOUNDARY_STYLE}
        />
      )}

      {shape === "polygon" && Array.isArray(coordinates) && (
        <GeoJSON
          key={JSON.stringify(coordinates)}
          data={{
            type: "Feature",
            properties: {},
            geometry: {
              type: "Polygon",
              coordinates: [coordinates.map(([lat, lng]) => [lng, lat])],
            },
          } as any}
          style={BOUNDARY_STYLE}
        />
      )}

      {centroid && markerIcon && (
        <Marker position={centroid} icon={markerIcon}>
          <Popup>
            <div className="p-1 font-sans text-xs space-y-0.5">
              <div className="font-bold text-neutral-900">Project Site Location</div>
              <div className="text-[10px] text-neutral-500 font-mono">
                {centroid[0].toFixed(5)}, {centroid[1].toFixed(5)}
              </div>
            </div>
          </Popup>
        </Marker>
      )}
    </>
  );
}
