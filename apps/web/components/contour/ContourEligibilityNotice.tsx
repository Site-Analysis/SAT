// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { copy } from "@/lib/contour/copy";
import { areaHaLabel } from "@/lib/contour/format";
import type { ContourEligibility } from "@/lib/contour/types";
import { C, caption, warnCard } from "./theme";

export function ContourEligibilityNotice({ eligibility }: { eligibility: ContourEligibility }) {
  if (eligibility.eligible) {
    return (
      <div style={{ ...caption, color: C.good }}>{copy.eligibility.ok}</div>
    );
  }
  const body =
    eligibility.reason === "point"
      ? copy.eligibility.point
      : eligibility.reason === "too-small"
        ? `${copy.eligibility.tooSmall} ${copy.eligibility.tooSmallDetail(areaHaLabel(eligibility.areaHa))}`
        : copy.eligibility.noBoundary;
  return (
    <div role="status" style={warnCard}>
      {body}
    </div>
  );
}
