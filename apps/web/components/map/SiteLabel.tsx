// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

import { cn } from "@/lib/utils";

export interface SiteLabelProps {
  projectName: string;
  coordinates: string;
  area: string;
  date: string;
  className?: string;
  areaHa?: number;
}

export function SiteLabel({
  projectName,
  coordinates,
  area,
  date,
  className,
  areaHa,
}: SiteLabelProps) {
  const numericAreaHa =
    typeof areaHa === "number"
      ? areaHa
      : (() => {
          const match = area?.match(/([\d.]+)\s*ha/i);
          return match ? parseFloat(match[1]) : 0;
        })();
  const isLargeSite = numericAreaHa > 100;

  return (
    <div
      className={cn(
        "absolute bottom-4 left-4 z-[400]",
        "rounded border border-neutral-border bg-neutral-surface/90 px-3 py-2",
        "backdrop-blur-sm shadow-sm max-w-[280px]",
        className
      )}
      aria-label={`${projectName} — ${coordinates} — ${area} — ${date}`}
    >
      <p className="text-sm font-semibold text-text-primary leading-tight">
        {projectName}
      </p>
      <p className="text-xs text-text-secondary mt-0.5">{coordinates}</p>
      {isLargeSite && (
        <p className="text-[10px] text-text-secondary/80 italic mt-0.5 leading-tight">
          Note: Analysis for large sites is calculated based on the site centroid.
        </p>
      )}
      <p className="text-xs text-text-secondary mt-0.5">{area} · {date}</p>
    </div>
  );
}
