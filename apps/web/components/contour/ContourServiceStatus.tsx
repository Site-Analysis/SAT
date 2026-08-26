// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { copy } from "@/lib/contour/copy";
import { useContourStore } from "@/lib/stores/contour";
import { warnCard } from "./theme";

export function ContourServiceStatus() {
  const status = useContourStore((s) => s.serviceStatus);
  if (status === "ready" || status === "unknown") return null;
  const text =
    status === "flag-disabled"
      ? copy.service.flagDisabled
      : status === "degraded"
        ? copy.service.degraded
        : copy.service.unreachable;
  return (
    <div role="status" style={warnCard}>
      {text}
    </div>
  );
}
