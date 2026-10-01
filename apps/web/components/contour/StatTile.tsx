// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import type { ReactNode } from "react";
import { C, microLabel, mono, tile } from "./theme";

interface StatTileProps {
  label: string;
  value: string;
  help?: string;
  info?: ReactNode;
}

export function StatTile({ label, value, help, info }: StatTileProps) {
  return (
    <div style={tile} title={help}>
      <div style={{ display: "flex", alignItems: "center", gap: 4, marginBottom: 4 }}>
        <span style={microLabel}>{label}</span>
        {info}
      </div>
      <div style={{ fontSize: 13, fontWeight: 700, color: C.ink, ...mono }}>{value}</div>
    </div>
  );
}
