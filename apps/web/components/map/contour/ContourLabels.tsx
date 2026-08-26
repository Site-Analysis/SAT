// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { useEffect, useMemo, useState } from "react";
import { Marker, useMap } from "react-leaflet";
import L from "leaflet";
import { LABEL_MIN_ZOOM, MAX_LABELS } from "@/lib/contour/constants";
import { featureProp } from "@/lib/contour/format";
import { featureLength, labelAnchor } from "@/lib/contour/geometry";
import type { GeoJSONLike } from "@/lib/contour/types";
import { C } from "@/components/contour/theme";

export function ContourLabels({ data }: { data: GeoJSONLike }) {
  const map = useMap();
  const [zoom, setZoom] = useState(map.getZoom());
  const [hidden, setHidden] = useState(false);

  useEffect(() => {
    const hide = () => setHidden(true);
    const onEnd = () => {
      setZoom(map.getZoom());
      setHidden(false);
    };
    map.on("zoomstart", hide);
    map.on("zoomend", onEnd);
    return () => {
      map.off("zoomstart", hide);
      map.off("zoomend", onEnd);
    };
  }, [map]);

  const labels = useMemo(() => {
    if (hidden || zoom < LABEL_MIN_ZOOM) return [];
    const features = ((data as { features?: GeoJSONLike[] }).features ?? []).filter(
      (f) => featureProp<boolean>(f, "is_index"),
    );
    const ranked = [...features].sort((a, b) => featureLength(b) - featureLength(a)).slice(0, MAX_LABELS);
    return ranked.flatMap((f, i) => {
      const anchor = labelAnchor(f);
      const elev = featureProp<number>(f, "elevation");
      if (!anchor || elev == null) return [];
      return [{ id: `lbl-${i}-${elev}`, position: anchor, elev }];
    });
  }, [data, zoom, hidden]);

  if (!labels.length) return null;
  return (
    <>
      {labels.map((l) => (
        <Marker
          key={l.id}
          position={l.position}
          interactive={false}
          icon={L.divIcon({
            className: "contour-index-label",
            html: `<span style="background:rgba(253,252,251,0.92);border:1px solid ${C.border};color:${C.ink};font:600 9px/1.2 system-ui;padding:1px 4px;border-radius:3px;white-space:nowrap">${l.elev} m</span>`,
            iconSize: [1, 1],
            iconAnchor: [0, 0],
          })}
        />
      ))}
    </>
  );
}
