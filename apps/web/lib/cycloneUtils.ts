// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

// In-memory cache for storm animation grid availability
const gridAvailabilityCache = new Map<string, boolean>();

/**
 * Returns true if a storm category represents a Depression / Deep Depression
 * or an un-cached weaker system with no pre-computed ERA5 grid.
 */
export function isDepressionOrUncached(category?: string): boolean {
  if (!category) return false;
  return category.toLowerCase().includes("depression");
}

/**
 * Synchronously checks if a storm definitely lacks animation capability
 * based on metadata flags, category, or recorded availability.
 */
export function isStormAnimationUnavailable(
  storm: {
    sid?: string;
    category?: string;
    max_wind_ms?: number | null;
    max_wind_speed?: number | null;
    has_animation?: boolean;
  },
  availabilityRecord?: Record<string, boolean>
): boolean {
  if (storm.has_animation === false) return true;
  if (isDepressionOrUncached(storm.category)) return true;
  const w = storm.max_wind_ms ?? storm.max_wind_speed;
  if (w != null && Number(w) <= 0) return true;
  if (storm.sid && availabilityRecord && availabilityRecord[storm.sid] === false) return true;
  return false;
}

/**
 * Pre-checks whether a storm has pre-cached ERA5 grid data available on MinIO.
 */
export async function checkStormGridAvailability(storm: {
  sid: string;
  category?: string;
  max_wind_ms?: number | null;
  max_wind_speed?: number | null;
  has_animation?: boolean;
}): Promise<boolean> {
  if (storm.has_animation === false) return false;
  if (isDepressionOrUncached(storm.category)) return false;
  const w = storm.max_wind_ms ?? storm.max_wind_speed;
  if (w != null && Number(w) <= 0) return false;
  if (storm.has_animation === true) return true;

  if (gridAvailabilityCache.has(storm.sid)) {
    return gridAvailabilityCache.get(storm.sid)!;
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);
    const res = await fetch(`http://localhost:9000/cyclone-wind-grids/${storm.sid}.json`, {
      method: "HEAD",
      signal: controller.signal,
    });
    clearTimeout(timeoutId);

    if (res.status === 404) {
      gridAvailabilityCache.set(storm.sid, false);
      return false;
    }

    const available = res.ok;
    gridAvailabilityCache.set(storm.sid, available);
    return available;
  } catch {
    gridAvailabilityCache.set(storm.sid, false);
    return false;
  }
}
