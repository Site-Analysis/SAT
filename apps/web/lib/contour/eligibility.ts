// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

import { polygonAreaM2 } from "../geo";
import type { Project } from "../stores/project";
import { MIN_AREA_HA } from "./constants";
import type { ContourEligibility, GeoJSONLike } from "./types";

function asFeature(geometry: GeoJSON.Geometry): GeoJSONLike {
  return { type: "Feature", geometry };
}

function ringAreaHa(coords: unknown): number {
  if (!Array.isArray(coords) || coords.length === 0) return 0;
  const ring = (coords as number[][]).map(([lng, lat]) => [lat, lng] as [number, number]);
  if (ring.length >= 2) {
    const first = ring[0];
    const last = ring[ring.length - 1];
    if (first[0] === last[0] && first[1] === last[1]) ring.pop();
  }
  return polygonAreaM2(ring) / 10_000;
}

function geometryAreaHa(geometry: GeoJSON.Geometry | undefined): number {
  if (!geometry) return 0;
  if (geometry.type === "Polygon") return ringAreaHa(geometry.coordinates[0]);
  if (geometry.type === "MultiPolygon") {
    return geometry.coordinates.reduce((sum, poly) => sum + ringAreaHa(poly[0]), 0);
  }
  return 0;
}

export function deriveContourEligibility(project: Project | null): ContourEligibility {
  const boundary = project?.boundary;
  if (!boundary) return { eligible: false, reason: "no-boundary" };
  if (boundary.type === "Point") return { eligible: false, reason: "point" };
  if (boundary.type !== "Polygon" && boundary.type !== "MultiPolygon") {
    return { eligible: false, reason: "no-boundary" };
  }

  const fromProject = project?.area_sqm && project.area_sqm > 0 ? project.area_sqm / 10_000 : 0;
  const areaHa = fromProject > 0 ? fromProject : geometryAreaHa(boundary);
  if (areaHa < MIN_AREA_HA) return { eligible: false, reason: "too-small", areaHa };
  return { eligible: true, polygon: asFeature(boundary), areaHa };
}
