// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

import type { LatLng } from "../geo";
import type { GeoJSONLike } from "./types";

function walkCoords(coords: unknown, visit: (lng: number, lat: number) => void): void {
  if (!Array.isArray(coords) || coords.length === 0) return;
  if (typeof coords[0] === "number") {
    visit(coords[0] as number, coords[1] as number);
    return;
  }
  for (const c of coords) walkCoords(c, visit);
}

function featureCoords(geojson: GeoJSONLike): unknown[] {
  const obj = geojson as {
    type?: string;
    geometry?: { coordinates?: unknown };
    features?: Array<{ geometry?: { coordinates?: unknown } }>;
    coordinates?: unknown;
  };
  if (obj.type === "FeatureCollection" && Array.isArray(obj.features)) {
    return obj.features.map((f) => f.geometry?.coordinates);
  }
  if (obj.type === "Feature") return [obj.geometry?.coordinates];
  if (obj.coordinates) return [obj.coordinates];
  if (obj.geometry?.coordinates) return [obj.geometry.coordinates];
  return [];
}

/** Hillshade fallback bounds — walks every ring of every feature (AD-5). */
export function bboxOfPolygon(geojson: GeoJSONLike): [[number, number], [number, number]] {
  let minLat = 90, minLng = 180, maxLat = -90, maxLng = -180;
  let any = false;
  for (const coords of featureCoords(geojson)) {
    walkCoords(coords, (lng, lat) => {
      any = true;
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
      minLng = Math.min(minLng, lng);
      maxLng = Math.max(maxLng, lng);
    });
  }
  if (!any) return [[0, 0], [0, 0]];
  return [[minLat, minLng], [maxLat, maxLng]];
}

function lineVertices(feature: GeoJSONLike): number[][] {
  const geom = (feature as { geometry?: { type?: string; coordinates?: unknown } }).geometry
    ?? (feature as { type?: string; coordinates?: unknown });
  if (!geom) return [];
  const type = (geom as { type?: string }).type;
  const coords = (geom as { coordinates?: unknown }).coordinates;
  if (type === "MultiLineString" && Array.isArray(coords)) {
    return (coords as number[][][])[0] ?? [];
  }
  if (Array.isArray(coords) && Array.isArray(coords[0]) && typeof (coords as number[][])[0]?.[0] === "number") {
    return coords as number[][];
  }
  return [];
}

/** Middle vertex of the feature coordinate array — no Leaflet construction (AD-9). */
export function labelAnchor(feature: GeoJSONLike): [number, number] | null {
  const coords = lineVertices(feature);
  if (!coords.length) return null;
  const mid = coords[Math.floor(coords.length / 2)];
  if (!mid || mid.length < 2) return null;
  return [mid[1], mid[0]];
}

export function featureLength(feature: GeoJSONLike): number {
  return lineVertices(feature).length;
}

export function featureCount(geojson: GeoJSONLike | null | undefined): number {
  if (!geojson) return 0;
  const features = (geojson as { features?: unknown[] }).features;
  return Array.isArray(features) ? features.length : 0;
}

export type DistanceFn = (a: LatLng, b: LatLng) => number;

/**
 * Place a transect sample on the drawn line when the backend did not emit lat/lng.
 * Scales haversine length to the backend UTM total so endpoints land exactly.
 */
export function buildProfileLocator(
  line: [number, number][],
  backendTotalM: number,
  distanceFn: DistanceFn,
): (distanceM: number) => [number, number] {
  const segs: number[] = [0];
  for (let i = 1; i < line.length; i++) {
    segs.push(segs[i - 1] + distanceFn(line[i - 1], line[i]));
  }
  const localTotal = segs[segs.length - 1] || 1;
  const scale = backendTotalM > 0 ? localTotal / backendTotalM : 1;

  return (distanceM: number): [number, number] => {
    if (line.length === 0) return [0, 0];
    if (line.length === 1) return line[0];
    const d = Math.max(0, Math.min(distanceM * scale, localTotal));
    let lo = 0;
    let hi = segs.length - 1;
    while (lo < hi) {
      const mid = Math.floor((lo + hi) / 2);
      if (segs[mid] < d) lo = mid + 1;
      else hi = mid;
    }
    const i = Math.max(1, lo);
    const a = line[i - 1];
    const b = line[i];
    const span = segs[i] - segs[i - 1];
    const t = span > 0 ? (d - segs[i - 1]) / span : 0;
    return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
  };
}

export function transectLineGeoJSON(positions: [number, number][]): GeoJSONLike {
  return {
    type: "LineString",
    coordinates: positions.map(([lat, lng]) => [lng, lat]),
  };
}
