// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { useMemo, useState } from "react";
import L from "leaflet";
import { GeoJSON, ImageOverlay, Marker, useMap } from "react-leaflet";
import type { ContourResponse } from "@/lib/stores/analysis";

interface ContourOverlayProps {
  contour: ContourResponse;
}

function boundsFromGeojson(data: any): L.LatLngBoundsExpression | null {
  const coords: [number, number][] = [];
  const visit = (node: any) => {
    if (!node) return;
    if (typeof node[0] === "number" && typeof node[1] === "number") {
      coords.push([node[1], node[0]]);
      return;
    }
    if (Array.isArray(node)) node.forEach(visit);
  };
  visit(data?.features?.[0]?.geometry?.coordinates ?? data?.features?.map((f: any) => f.geometry.coordinates));
  if (coords.length === 0) return null;
  return L.latLngBounds(coords);
}

export function ContourOverlay({ contour }: ContourOverlayProps) {
  const map = useMap();
  const [layers, setLayers] = useState({ contours: true, slope: false, buildability: false, hillshade: false });
  const bounds = useMemo(() => boundsFromGeojson(contour.slope_geojson), [contour.slope_geojson]);
  const labels = useMemo(() => {
    const group = L.geoJSON(contour.contour_geojson as any);
    return (contour.contour_geojson.features ?? [])
      .filter((feature: any) => feature.properties?.is_index)
      .map((feature: any, index: number) => {
        const layer = L.geoJSON(feature);
        const b = layer.getBounds();
        return {
          key: `${feature.properties?.elevation}-${index}`,
          position: b.isValid() ? b.getCenter() : map.getCenter(),
          elevation: feature.properties?.elevation,
        };
      })
      .filter(Boolean);
  }, [contour.contour_geojson, map]);

  return (
    <>
      {layers.hillshade && bounds && (
        <ImageOverlay
          url={`data:image/png;base64,${contour.hillshade_png_b64}`}
          bounds={bounds}
          opacity={0.3}
        />
      )}
      {layers.slope && (
        <GeoJSON
          key="slope"
          data={contour.slope_geojson as any}
          style={(feature) => ({
            color: feature?.properties?.color ?? "#52b788",
            fillColor: feature?.properties?.color ?? "#52b788",
            fillOpacity: 0.5,
            weight: 0.5,
          })}
        />
      )}
      {layers.buildability && (
        <GeoJSON
          key="buildability"
          data={contour.buildability_geojson as any}
          style={(feature) => ({
            color: feature?.properties?.color ?? "#2d6a4f",
            fillColor: feature?.properties?.color ?? "#2d6a4f",
            fillOpacity: 0.6,
            weight: 0.5,
          })}
        />
      )}
      {layers.contours && (
        <>
          <GeoJSON
            key="contours"
            data={contour.contour_geojson as any}
            style={(feature) => ({
              color: feature?.properties?.color ?? "#31688e",
              weight: feature?.properties?.line_weight ?? 1,
              opacity: 0.95,
            })}
          />
          {labels.map((label) => (
            <Marker
              key={label.key}
              position={label.position}
              interactive={false}
              icon={L.divIcon({
                className: "contour-label",
                html: `<span style="font-size:10px;font-weight:700;color:#2d6a4f;background:rgba(253,252,251,.85);padding:1px 4px;border-radius:3px;">${label.elevation}m</span>`,
              })}
            />
          ))}
        </>
      )}
      <div style={{
        position: "absolute", bottom: 20, right: 14, zIndex: 500, pointerEvents: "auto",
        background: "rgba(253,252,251,0.96)", border: "1px solid #CFD6C4",
        borderRadius: 8, padding: 10, display: "grid", gap: 6,
      }}>
        {[
          ["contours", "Contours"],
          ["slope", "Slope"],
          ["buildability", "Buildability"],
          ["hillshade", "Hillshade"],
        ].map(([key, label]) => (
          <label key={key} style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 10, color: "#3A3F3B" }}>
            <input
              type="checkbox"
              checked={layers[key as keyof typeof layers]}
              onChange={() => setLayers((prev) => ({ ...prev, [key]: !prev[key as keyof typeof prev] }))}
            />
            {label}
          </label>
        ))}
      </div>
    </>
  );
}
