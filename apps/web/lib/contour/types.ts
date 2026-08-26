// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

import type { BUILDABILITY_CLASSES, SLOPE_CLASSES } from "./constants";

export type GeoJSONLike = Record<string, unknown>;

export type SlopeClassId = (typeof SLOPE_CLASSES)[number]["id"];
export type BuildabilityClassId = (typeof BUILDABILITY_CLASSES)[number]["id"];

export type ContourLayerId = "hillshade" | "contours" | "slope" | "buildability";
export type ContourRunStatus = "idle" | "running" | "succeeded" | "failed" | "cancelled";
export type TransectStatus = "idle" | "drawing" | "ready" | "running" | "succeeded" | "failed";

/** Reactive, derived from the last real request outcome — never from /health (AD-15). */
export type ServiceStatus = "unknown" | "ready" | "flag-disabled" | "unreachable" | "degraded";

export type ContourErrorAction = "retry" | "adjust-interval" | "draw-polygon" | "contact-ops";

export interface ContourErrorView {
  title: string;
  detail?: string;
  recoverable: boolean;
  action?: ContourErrorAction;
}

export interface DEMMetadata {
  source: "copernicus" | string;
  resolution_m: number;
  vertical_rmse_m: number;
  contour_interval_m: number;
  warning?: string | null;
}

export interface SlopeStats {
  mean_slope_pct: number;
  max_slope_pct: number;
  flat_area_pct: number;
  gentle_area_pct: number;
  moderate_area_pct: number;
  steep_area_pct: number;
  very_steep_area_pct: number;
  hazard_area_pct: number;
}

export interface AspectStats {
  dominant_aspect_deg: number;
  dominant_aspect_label: string;
  north_facing_pct: number;
  south_facing_pct: number;
}

/** Added by the WP-0 contract addendum. Optional — always guard. */
export interface ContourResponse {
  dem_metadata: DEMMetadata;
  slope_stats: SlopeStats;
  aspect_stats: AspectStats;
  contour_geojson: GeoJSONLike;
  slope_geojson: GeoJSONLike;
  buildability_geojson: GeoJSONLike;
  hillshade_png_b64: string;
  hillshade_bounds?: [[number, number], [number, number]];
}

/** Added by the WP-0 contract addendum (AD-5b). Optional — always guard. */
export interface TransectPoint {
  distance_m: number;
  elevation_m: number;
  slope_pct: number;
  slope_class: SlopeClassId | string;
  lat?: number;
  lng?: number;
}

export interface TransectResponse {
  total_length_m: number;
  min_elevation_m: number;
  max_elevation_m: number;
  relief_m: number;
  dem_source: string;
  points: TransectPoint[];
}

export type ContourEligibility =
  | { eligible: true; polygon: GeoJSONLike; areaHa: number }
  | { eligible: false; reason: "no-boundary" | "point" | "too-small"; areaHa?: number };
