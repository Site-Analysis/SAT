// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

// Palettes must equal services/contour/app/services/slope_engine.py:10-25.
// Map geometry still renders from each feature's own `color` property; these
// constants are for legends, chips, and the report where no feature is present.

export const SLOPE_CLASSES = [
  { id: "FLAT",       label: "Flat",       range: "0-5%",   color: "#2d6a4f", statKey: "flat_area_pct" },
  { id: "GENTLE",     label: "Gentle",     range: "5-10%",  color: "#52b788", statKey: "gentle_area_pct" },
  { id: "MODERATE",   label: "Moderate",   range: "10-15%", color: "#ffd166", statKey: "moderate_area_pct" },
  { id: "STEEP",      label: "Steep",      range: "15-25%", color: "#f4a261", statKey: "steep_area_pct" },
  { id: "VERY_STEEP", label: "Very steep", range: "25-33%", color: "#e76f51", statKey: "very_steep_area_pct" },
  { id: "HAZARD",     label: "Hazard",     range: ">33%",   color: "#c1121f", statKey: "hazard_area_pct" },
] as const;

export const BUILDABILITY_CLASSES = [
  { id: "BUILDABLE_FLAT",          label: "Buildable Flat",                            color: "#2d6a4f", slopeIds: ["FLAT"] },
  { id: "BUILDABLE_WITH_GRADING",  label: "Buildable With Grading",                    color: "#52b788", slopeIds: ["GENTLE"] },
  { id: "CONSTRAINED_RETAINING",   label: "Constrained: Retaining/Engineering Needed",  color: "#ffd166", slopeIds: ["MODERATE"] },
  { id: "NON_BUILDABLE_REGULATED", label: "Non-Buildable: Regulated/Very Steep",       color: "#e76f51", slopeIds: ["STEEP", "VERY_STEEP"] },
  { id: "NON_BUILDABLE_HAZARD",    label: "Non-Buildable: Hazard",                     color: "#c1121f", slopeIds: ["HAZARD"] },
] as const;

export const CONTOUR_INTERVALS = [10, 20, 30, 40, 50, 60] as const;
export const DEFAULT_INTERVAL = 20;
export const MIN_INTERVAL = 10;
export const MAX_INTERVAL = 60;
export const MIN_AREA_HA = 0.5;

export const LABEL_MIN_ZOOM = 16;
export const MAX_LABELS = 40;
export const MAX_SVG_FEATURES = 800;
export const MAX_TOOLTIP_FEATURES = 20_000;

export const HILLSHADE_OPACITY = 0.45;
export const CONTOUR_TIMEOUT_MS = 90_000;

export const PANE = {
  hillshade: { name: "contour-hillshade", zIndex: 350 },
  fill:      { name: "contour-fill",      zIndex: 401 },
  lines:     { name: "contour-lines",     zIndex: 402 },
  transect:  { name: "contour-transect",  zIndex: 403 },
} as const;

export const LAYER_DEFAULTS = {
  hillshade: true,
  contours: true,
  slope: false,
  buildability: false,
} as const;

export const ACCENT = "#2D6A4F";
export const START_COLOR = "#306223";
export const END_COLOR = "#B45309";
export const TRANSECT_LINE = "#3A3F3B";
