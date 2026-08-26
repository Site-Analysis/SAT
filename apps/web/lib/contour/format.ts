// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

import { copy } from "./copy";

export function pct(n: number, digits = 1): string {
  return `${Number.isFinite(n) ? n.toFixed(digits) : "—"}%`;
}

export function metres(n: number, digits = 0): string {
  if (!Number.isFinite(n)) return "—";
  return `${digits === 0 ? Math.round(n) : n.toFixed(digits)} m`;
}

export function elevation(n: number): string {
  return metres(n, 1);
}

export function demSourceLabel(source: string | undefined): string {
  if (!source || source === "copernicus") return copy.demSourceLabel;
  return source;
}

export function areaHaLabel(areaHa: number | undefined): string {
  if (areaHa == null || !Number.isFinite(areaHa)) return "—";
  return areaHa < 0.01 ? areaHa.toFixed(3) : areaHa.toFixed(2);
}

export function featureProp<T>(feature: unknown, key: string): T | undefined {
  const props = (feature as { properties?: Record<string, unknown> } | null)?.properties;
  return props?.[key] as T | undefined;
}
