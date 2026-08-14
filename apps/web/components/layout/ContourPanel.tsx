// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import type { ContourResponse, ModuleResult, TransectResponse } from "@/lib/stores/analysis";

const SLOPE = [
  ["Flat", "flat_area_pct", "#2d6a4f"],
  ["Gentle", "gentle_area_pct", "#52b788"],
  ["Moderate", "moderate_area_pct", "#ffd166"],
  ["Steep", "steep_area_pct", "#f4a261"],
  ["Very steep", "very_steep_area_pct", "#e76f51"],
  ["Hazard", "hazard_area_pct", "#c1121f"],
] as const;

interface ContourPanelProps {
  result?: ModuleResult;
  contour?: ContourResponse | null;
  interval: number;
  loading: boolean;
  error?: string | null;
  polygonAvailable: boolean;
  transect?: TransectResponse | null;
  transectLoading?: boolean;
  onIntervalChange: (interval: number) => void;
  onRunAnalysis: () => void;
  onToggleTransect: () => void;
  transectActive: boolean;
}

function metric(value: number | undefined, suffix = "") {
  return Number.isFinite(value) ? `${Number(value).toFixed(1)}${suffix}` : "-";
}

export function ContourPanel({
  result,
  contour,
  interval,
  loading,
  error,
  polygonAvailable,
  transect,
  transectLoading = false,
  onIntervalChange,
  onRunAnalysis,
  onToggleTransect,
  transectActive,
}: ContourPanelProps) {
  const c = contour ?? result?.contour ?? null;
  const slope = c?.slope_stats;
  const aspect = c?.aspect_stats;
  const transectPoints = transect?.points?.map((p) => ({
    distance: Math.round(p.distance_m),
    elevation: p.elevation_m,
  })) ?? [];

  if (!polygonAvailable) {
    return (
      <div style={{ marginTop: 2, padding: 12, borderRadius: 8, background: "#F8EDE0", color: "#7A4B22", fontSize: 11, lineHeight: 1.5 }}>
        Contour analysis requires a drawn polygon boundary. Create the project with a polygon site boundary to run DEM analysis.
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 2 }}>
      <div style={{ background: "#F2EDE8", borderRadius: 8, padding: "10px 12px" }}>
        <label style={{ display: "flex", justifyContent: "space-between", fontSize: 10, fontWeight: 700, color: "#3A3F3B", marginBottom: 8 }}>
          <span>Contour Interval (m)</span>
          <span>{interval}m</span>
        </label>
        <input
          type="range"
          min={10}
          max={60}
          step={10}
          value={interval}
          onChange={(e) => onIntervalChange(Number(e.target.value))}
          style={{ width: "100%" }}
        />
        <Button size="sm" loading={loading} onClick={onRunAnalysis} style={{ width: "100%", marginTop: 10 }}>
          Run Analysis
        </Button>
        {error && <div style={{ fontSize: 10, color: "#C46A6A", marginTop: 8 }}>{error}</div>}
      </div>

      {c && (
        <>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
            <StatusBadge severity="none" label="Copernicus 30m" />
            {c.dem_metadata.warning && <StatusBadge severity="needs-review" label="10m minimum" />}
            {c.dem_metadata.vertical_rmse_m > 5 && <StatusBadge severity="moderate" label={`RMSE ${c.dem_metadata.vertical_rmse_m}m`} />}
          </div>

          {slope && (
            <div style={{ background: "#F2EDE8", borderRadius: 8, padding: "10px 12px" }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: "#7B8F83", textTransform: "uppercase", marginBottom: 8 }}>
                Slope Statistics
              </div>
              <div style={{ display: "flex", height: 14, borderRadius: 4, overflow: "hidden", marginBottom: 8 }}>
                {SLOPE.map(([label, key, color]) => (
                  <span
                    key={key}
                    title={label}
                    style={{ width: `${Math.max(0, Number(slope[key]) || 0)}%`, background: color }}
                  />
                ))}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
                <SmallMetric label="Mean slope" value={metric(slope.mean_slope_pct, "%")} />
                <SmallMetric label="Max slope" value={metric(slope.max_slope_pct, "%")} />
              </div>
            </div>
          )}

          {aspect && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 6 }}>
              <SmallMetric label="Aspect" value={`${aspect.dominant_aspect_label} ${Math.round(aspect.dominant_aspect_deg)}°`} />
              <SmallMetric label="North" value={metric(aspect.north_facing_pct, "%")} />
              <SmallMetric label="South" value={metric(aspect.south_facing_pct, "%")} />
            </div>
          )}

          <div style={{ background: "#F2EDE8", borderRadius: 8, padding: "10px 12px" }}>
            <Button size="sm" variant={transectActive ? "secondary" : "primary"} loading={transectLoading} onClick={onToggleTransect} style={{ width: "100%" }}>
              Draw Transect Line
            </Button>
            {transect && (
              <div style={{ marginTop: 10 }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 6, marginBottom: 10 }}>
                  <SmallMetric label="Length" value={`${Math.round(transect.total_length_m)}m`} />
                  <SmallMetric label="Relief" value={`${transect.relief_m.toFixed(1)}m`} />
                  <SmallMetric label="Max elev" value={`${transect.max_elevation_m.toFixed(1)}m`} />
                </div>
                <div style={{ height: 130 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={transectPoints} margin={{ top: 4, right: 8, left: -18, bottom: 0 }}>
                      <CartesianGrid stroke="#CFD6C4" vertical={false} />
                      <XAxis dataKey="distance" tick={{ fontSize: 9, fill: "#7B8F83" }} />
                      <YAxis tick={{ fontSize: 9, fill: "#7B8F83" }} width={36} />
                      <Tooltip />
                      <Line type="monotone" dataKey="elevation" stroke="#2d6a4f" dot={false} strokeWidth={2} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function SmallMetric({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ background: "#FDFCFB", borderRadius: 6, padding: "7px 8px" }}>
      <div style={{ fontSize: 11, fontWeight: 700, color: "#3A3F3B" }}>{value}</div>
      <div style={{ fontSize: 9, color: "#7B8F83", marginTop: 2, textTransform: "uppercase" }}>{label}</div>
    </div>
  );
}
