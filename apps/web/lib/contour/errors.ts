// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

import { copy } from "./copy";
import type { ContourErrorView } from "./types";

function detailText(detail: unknown): string | undefined {
  if (detail == null) return undefined;
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const parts = detail.map((d) => {
      if (typeof d === "string") return d;
      if (d && typeof d === "object" && "msg" in d) return String((d as { msg: unknown }).msg);
      return JSON.stringify(d);
    });
    return parts.join("; ") || undefined;
  }
  return String(detail);
}

export function mapContourError(status: number | null, detail?: unknown): ContourErrorView {
  const text = detailText(detail);
  const lower = (text ?? "").toLowerCase();

  if (status === 403) {
    return { title: copy.errors.flagDisabled, detail: text, recoverable: false, action: "contact-ops" };
  }
  if (status === 422 && lower.includes("too small")) {
    return { title: copy.errors.tooSmall, detail: text, recoverable: false, action: "draw-polygon" };
  }
  if (status === 422 && (lower.includes("contour_interval") || lower.includes("contour interval"))) {
    return { title: copy.errors.interval, detail: text, recoverable: true, action: "adjust-interval" };
  }
  if (status === 422) {
    return { title: copy.errors.inputs, detail: text, recoverable: true, action: "retry" };
  }
  if (status === 503) {
    return { title: copy.errors.demFetch, detail: text, recoverable: true, action: "retry" };
  }
  if (status === 0 || status == null) {
    if (lower.includes("transect") && (lower.includes("start") || lower.includes("end") || lower.includes("point"))) {
      return { title: copy.errors.transectShort, detail: text, recoverable: true, action: "retry" };
    }
    if (lower.includes("polygon") || lower.includes("boundary")) {
      return { title: copy.errors.missingPolygon, detail: text, recoverable: false, action: "draw-polygon" };
    }
    return { title: copy.errors.unreachable, detail: text, recoverable: true, action: "retry" };
  }
  return { title: copy.errors.generic, detail: text, recoverable: true, action: "retry" };
}

export function clientMissingPolygonError(): ContourErrorView {
  return { title: copy.errors.missingPolygon, recoverable: false, action: "draw-polygon" };
}

export function clientTransectShortError(): ContourErrorView {
  return { title: copy.errors.transectShort, recoverable: true, action: "retry" };
}

/** Exhaustive mapping check covering every §7.4 row. Throws on mismatch. */
export function assertContourErrorMapping(): void {
  const cases: Array<{
    status: number | null;
    detail?: string;
    title: string;
    recoverable: boolean;
    action: ContourErrorView["action"];
  }> = [
    { status: 403, title: copy.errors.flagDisabled, recoverable: false, action: "contact-ops" },
    {
      status: 422,
      detail: "Site polygon too small for DEM analysis at 30m resolution",
      title: copy.errors.tooSmall,
      recoverable: false,
      action: "draw-polygon",
    },
    {
      status: 422,
      detail: "Input should be greater than or equal to 10 [type=greater_than_equal, loc=contour_interval]",
      title: copy.errors.interval,
      recoverable: true,
      action: "adjust-interval",
    },
    { status: 422, detail: "validation error", title: copy.errors.inputs, recoverable: true, action: "retry" },
    { status: 503, detail: "DEM fetch failed: gee", title: copy.errors.demFetch, recoverable: true, action: "retry" },
    { status: null, detail: "Failed to fetch", title: copy.errors.unreachable, recoverable: true, action: "retry" },
    { status: 0, title: copy.errors.unreachable, recoverable: true, action: "retry" },
    {
      status: null,
      detail: "Contour analysis requires a polygon site boundary.",
      title: copy.errors.missingPolygon,
      recoverable: false,
      action: "draw-polygon",
    },
    {
      status: null,
      detail: "Draw a transect line with at least a start and end point.",
      title: copy.errors.transectShort,
      recoverable: true,
      action: "retry",
    },
    { status: 500, title: copy.errors.generic, recoverable: true, action: "retry" },
  ];
  for (const c of cases) {
    const got = mapContourError(c.status, c.detail);
    if (got.title !== c.title || got.recoverable !== c.recoverable || got.action !== c.action) {
      throw new Error(
        `mapContourError(${c.status}, ${JSON.stringify(c.detail)}) → ${JSON.stringify(got)}, expected title=${c.title}`
      );
    }
  }
}
