// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

// Contour-scoped style constants. Hex literals — Leaflet overlays sit outside Tailwind.
// Mirrors components/zoning/theme.ts. Values from SAT-19 plan §5.

import type { CSSProperties } from "react";

export const C = {
  accent: "#2D6A4F",
  start: "#306223",
  end: "#B45309",
  primary: "#306223",
  secondary: "#99CDD8",
  secondaryTint: "#DAEBE3",
  bg: "#F2EDE8",
  surface: "#FDFCFB",
  border: "#CFD6C4",
  ink: "#3A3F3B",
  inkSoft: "#7B8F83",
  inkFaint: "#B8C4BB",
  good: "#5A8F6A",
  goodBg: "#E4F0E8",
  warn: "#C4865A",
  warnBg: "#F8EDE0",
  bad: "#C46A6A",
  badBg: "#F5E4E4",
  info: "#5B93C9",
  profileFill: "rgba(45,106,79,0.10)",
} as const;

export const tile: CSSProperties = {
  background: C.surface,
  border: `1px solid ${C.border}`,
  borderRadius: 6,
  padding: "8px 10px",
};

export const innerCard: CSSProperties = {
  background: C.bg,
  borderRadius: 8,
  padding: "10px 12px",
};

export const sectionLabel: CSSProperties = {
  fontSize: 10,
  fontWeight: 700,
  letterSpacing: "0.5px",
  textTransform: "uppercase",
  color: C.inkSoft,
};

export const caption: CSSProperties = {
  fontSize: 10,
  fontWeight: 500,
  color: C.inkSoft,
  lineHeight: 1.45,
};

export const bodySm: CSSProperties = {
  fontSize: 11,
  fontWeight: 400,
  lineHeight: 1.55,
  color: C.inkSoft,
};

export const valueSm: CSSProperties = {
  fontSize: 11,
  fontWeight: 700,
  color: C.ink,
};

export const valueMd: CSSProperties = {
  fontSize: 12,
  fontWeight: 600,
  color: C.ink,
};

export const microLabel: CSSProperties = {
  fontSize: 9,
  fontWeight: 600,
  letterSpacing: "0.5px",
  textTransform: "uppercase",
  color: C.inkSoft,
};

export const hairline = `1px solid ${C.border}`;

export const hudCard: CSSProperties = {
  background: "rgba(253,252,251,0.97)",
  borderRadius: 10,
  padding: "11px 13px",
  boxShadow: "0 4px 18px rgba(0,0,0,0.12)",
};

export const hudBadge: CSSProperties = {
  background: "rgba(253,252,251,0.97)",
  borderRadius: 9,
  padding: "9px 13px",
  boxShadow: "0 2px 12px rgba(0,0,0,0.14)",
};

export const glassPill: CSSProperties = {
  background: "rgba(253,252,251,0.78)",
  backdropFilter: "blur(16px) saturate(160%)",
  WebkitBackdropFilter: "blur(16px) saturate(160%)",
  border: "1px solid rgba(255,255,255,0.6)",
  boxShadow: "0 6px 22px rgba(58,63,59,0.16), inset 0 1px 0 rgba(255,255,255,0.45)",
  borderRadius: 11,
};

export const warnCard: CSSProperties = {
  background: C.warnBg,
  color: C.warn,
  borderRadius: 8,
  padding: "10px 12px",
  fontSize: 11,
  lineHeight: 1.55,
};

export const mono: CSSProperties = {
  fontFamily: "var(--font-geist-mono), monospace",
};
