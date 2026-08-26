// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

import { DEFAULT_INTERVAL } from "./constants";
import type { ContourResponse, TransectResponse } from "./types";

const PLACEHOLDER_PNG =
  "iVBORw0KGgoAAAANSUhEUgAAAQAAAAABCAYAAAA7+k0hAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";

export function contourFixture(interval = DEFAULT_INTERVAL): ContourResponse {
  return {
    dem_metadata: {
      source: "copernicus",
      resolution_m: 30,
      vertical_rmse_m: 4.0,
      contour_interval_m: interval,
      warning: interval === 10 ? "Minimum reliable contour interval for Copernicus GLO-30 is 10m." : null,
    },
    slope_stats: {
      mean_slope_pct: 8.4,
      max_slope_pct: 28.1,
      flat_area_pct: 42.0,
      gentle_area_pct: 31.0,
      moderate_area_pct: 14.0,
      steep_area_pct: 8.0,
      very_steep_area_pct: 4.0,
      hazard_area_pct: 1.0,
    },
    aspect_stats: {
      dominant_aspect_deg: 184,
      dominant_aspect_label: "S",
      north_facing_pct: 22.5,
      south_facing_pct: 41.2,
    },
    contour_geojson: { type: "FeatureCollection", features: [] },
    slope_geojson: { type: "FeatureCollection", features: [] },
    buildability_geojson: { type: "FeatureCollection", features: [] },
    hillshade_png_b64: PLACEHOLDER_PNG,
    hillshade_bounds: [[12.97, 77.58], [12.98, 77.59]],
  };
}

export function transectFixture(): TransectResponse {
  const points = Array.from({ length: 21 }, (_, i) => {
    const t = i / 20;
    return {
      distance_m: i * 50,
      elevation_m: 910 + Math.sin(t * Math.PI) * 12,
      slope_pct: 4 + Math.cos(t * Math.PI) * 6,
      slope_class: t < 0.3 ? "FLAT" : t < 0.7 ? "GENTLE" : "MODERATE",
      lat: 12.971 + t * 0.008,
      lng: 77.581 + t * 0.008,
    };
  });
  return {
    total_length_m: 1000,
    min_elevation_m: 910,
    max_elevation_m: 922,
    relief_m: 12,
    dem_source: "copernicus",
    points,
  };
}
