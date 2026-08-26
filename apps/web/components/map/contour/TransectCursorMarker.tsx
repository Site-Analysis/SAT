// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { useEffect, useMemo, useRef } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";
import { buildProfileLocator } from "@/lib/contour/geometry";
import { C } from "@/components/contour/theme";
import { useContourStore } from "@/lib/stores/contour";

export function TransectCursorMarker() {
  const map = useMap();
  const markerRef = useRef<L.CircleMarker | null>(null);
  const result = useContourStore((s) => s.transectResult);
  const line = useContourStore((s) => s.transectSubmitted);

  const locator = useMemo(() => {
    if (!result || line.length < 2) return null;
    return buildProfileLocator(line, result.total_length_m, (a, b) => map.distance(a, b));
  }, [result, line, map]);

  useEffect(() => {
    const marker = L.circleMarker([0, 0], {
      radius: 0,
      color: "#fff",
      weight: 2,
      fillColor: C.accent,
      fillOpacity: 1,
      pane: "markerPane",
      interactive: false,
    });
    marker.addTo(map);
    markerRef.current = marker;
    const unsub = useContourStore.subscribe(
      (s) => s.activeProfileIndex,
      (idx) => {
        const m = markerRef.current;
        if (!m) return;
        if (idx == null) {
          m.setRadius(0);
          return;
        }
        const pts = useContourStore.getState().transectResult?.points;
        const pt = pts?.[idx];
        if (!pt) {
          m.setRadius(0);
          return;
        }
        let latlng: [number, number] | null = null;
        if (pt.lat != null && pt.lng != null) latlng = [pt.lat, pt.lng];
        else if (locator) latlng = locator(pt.distance_m);
        if (!latlng) {
          m.setRadius(0);
          return;
        }
        m.setLatLng(latlng);
        m.setRadius(7);
      },
    );
    return () => {
      unsub();
      marker.remove();
      markerRef.current = null;
    };
  }, [map, locator]);

  return null;
}
