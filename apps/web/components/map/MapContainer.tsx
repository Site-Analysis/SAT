// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { useEffect, useRef } from "react";
import { MapContainer as LeafletMap, TileLayer, useMap } from "react-leaflet";
import { cn } from "@/lib/utils";
import "leaflet/dist/leaflet.css";

// react-leaflet's center/zoom props apply only on mount. This child recenters
// the live map whenever the site coordinates resolve or change.
function MapController({ center, zoom }: { center: [number, number]; zoom: number }) {
  const map = useMap();
  const last = useRef<string>("");
  useEffect(() => {
    const key = `${center[0]},${center[1]},${zoom}`;
    if (key === last.current) return;
    last.current = key;
    map.flyTo(center, zoom, { duration: 0.8 });
  }, [map, center, zoom]);
  return null;
}

export interface MapContainerProps {
  mode: "full-screen" | "split";
  center?: [number, number];
  zoom?: number;
  children?: React.ReactNode;
  className?: string;
}

export function MapContainer({
  mode,
  center = [12.9716, 77.5946], // Bangalore default
  zoom = 13,
  children,
  className,
}: MapContainerProps) {
  // CARTO retired anonymous raster basemap tiles (28 Aug 2026) — unkeyed
  // requests now return a 200 with an "API KEY REQUIRED" watermark baked
  // into the tile image instead of an error. Free key, no account/approval
  // queue: https://carto.com/basemaps/apikey/
  const cartoKey = process.env.NEXT_PUBLIC_CARTO_API_KEY;
  const tileUrl = cartoKey
    ? `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=${cartoKey}`
    : "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png";

  return (
    <div
      className={cn(
        "relative",
        mode === "full-screen" && "fixed inset-0 z-0",
        mode === "split" && "flex-1 h-full",
        className
      )}
      role="application"
      aria-label="Site map"
    >
      <LeafletMap
        center={center}
        zoom={zoom}
        style={{ width: "100%", height: "100%" }}
        zoomControl={false}
      >
        <TileLayer
          url={tileUrl}
          attribution='&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
          subdomains="abcd"
          maxZoom={20}
        />
        <MapController center={center} zoom={zoom} />
        {children}
      </LeafletMap>
    </div>
  );
}
