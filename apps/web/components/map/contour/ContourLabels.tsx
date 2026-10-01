// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { useEffect, useMemo, useState } from "react";
import { Marker, useMap } from "react-leaflet";
import L from "leaflet";
import { CONTOUR_STROKE, LABEL_INTERMEDIATE_ZOOM, LABEL_MIN_ZOOM, MAX_LABELS } from "@/lib/contour/constants";
import { featureProp } from "@/lib/contour/format";
import { featureLength, labelAnchor } from "@/lib/contour/geometry";
import type { GeoJSONLike } from "@/lib/contour/types";

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
    const includeIntermediate = zoom >= LABEL_INTERMEDIATE_ZOOM;
    const features = ((data as { features?: GeoJSONLike[] }).features ?? []).filter((f) => {
      const isIndex = Boolean(featureProp<boolean>(f, "is_index"));
      return isIndex || includeIntermediate;
    });
    const ranked = [...features].sort((a, b) => {
      const ai = featureProp<boolean>(a, "is_index") ? 1 : 0;
      const bi = featureProp<boolean>(b, "is_index") ? 1 : 0;
      if (ai !== bi) return bi - ai;
      return featureLength(b) - featureLength(a);
    }).slice(0, MAX_LABELS);
    return ranked.flatMap((f, i) => {
      const anchor = labelAnchor(f);
      const elev = featureProp<number>(f, "elevation");
      const isIndex = Boolean(featureProp<boolean>(f, "is_index"));
      if (!anchor || elev == null) return [];
      return [{ id: `lbl-${i}-${elev}`, position: anchor, elev, isIndex }];
    });
  }, [data, zoom, hidden]);

  if (!labels.length) return null;
  return (
    <>
      {labels.map((l) => {
        const color = l.isIndex ? CONTOUR_STROKE.index.color : CONTOUR_STROKE.regular.color;
        return (
          <Marker
            key={l.id}
            position={l.position}
            interactive={false}
            icon={L.divIcon({
              className: "contour-index-label",
              html: `<span style="color:${color};font:700 10px/1 system-ui;white-space:nowrap;paint-order:stroke fill;-webkit-text-stroke:3px rgba(253,252,251,0.95)">${l.elev} m</span>`,
              iconSize: [1, 1],
              iconAnchor: [0, 0],
            })}
          />
        );
      })}
    </>
  );
}
