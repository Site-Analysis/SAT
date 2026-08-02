// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import type { ModuleResult, Severity, WindSeasonId } from "@/lib/stores/analysis";

interface WindPanelProps {
  result?: ModuleResult;
  severity: Severity;
  activeSeason: WindSeasonId;
  onSeasonChange: (season: WindSeasonId) => void;
}

// The wind service emits full 8-point names ("Southwest"); the abbreviations are
// kept because older cached results and the report export still use them.
const DIR_BEARING: Record<string, number> = {
  N: 0, NNE: 22.5, NE: 45, ENE: 67.5, E: 90, ESE: 112.5, SE: 135, SSE: 157.5,
  S: 180, SSW: 202.5, SW: 225, WSW: 247.5, W: 270, WNW: 292.5, NW: 315, NNW: 337.5,
  NORTH: 0, NORTHEAST: 45, EAST: 90, SOUTHEAST: 135,
  SOUTH: 180, SOUTHWEST: 225, WEST: 270, NORTHWEST: 315,
};

function indVal(result: ModuleResult | undefined, label: string, unit = ""): string {
  const ind = result?.indicators?.find((i) => i.label === label);
  if (!ind) return "—";
  return `${ind.value}${unit && ind.value !== "—" ? " " + unit : ""}`;
}
function metVal(result: ModuleResult | undefined, group: string, label: string): string {
  const row = result?.detailMetrics?.find((g) => g.group === group)?.rows.find((r) => r.label === label);
  if (!row) return "—";
  return row.unit ? `${row.value} ${row.unit}` : row.value;
}
function qualVal(result: ModuleResult | undefined, label: string): string {
  return result?.qualitative?.find((q) => q.label === label)?.value ?? "—";
}

export default function WindPanel({ result, severity, activeSeason, onSeasonChange }: WindPanelProps) {
  // Undefined for "annual", and also whenever the wind service predates contract
  // 2.0.0 — either way the annual indicators below are the fallback.
  const season = activeSeason === "annual" ? undefined : result?.wind?.seasonal_analysis?.[activeSeason];

  const prevailing  = season?.prevailing_direction ?? metVal(result, "Wind profile", "Prevailing direction");
  const bearing     = DIR_BEARING[String(prevailing).trim().toUpperCase()] ?? null;
  const meanSpeed   = season ? `${season.average_wind_speed} m/s` : indVal(result, "Mean wind speed", "m/s");
  const gust        = season ? `${season.max_wind_speed} m/s` : indVal(result, "Peak gust", "m/s");
  const gustRisk    = season?.gust_risk ?? qualVal(result, "Gust risk");
  // Recommended axis stays annual on purpose — a building can't be reoriented per
  // season, so the year-round prevailing wind is the one that should drive it.
  const orientation = indVal(result, "Recommended orientation");

  const seasonal = result?.charts?.find((c) => c.title === "Seasonal wind speed")?.points ?? [];
  const seasMax  = Math.max(1, ...seasonal.map((p) => Number(p.value) || 0));

  const comfort = [
    { label: "Pedestrian comfort", value: qualVal(result, "Pedestrian comfort") },
    { label: "Natural ventilation", value: qualVal(result, "Natural ventilation") },
    { label: "Outdoor usability",  value: qualVal(result, "Outdoor usability") },
  ];

  const calm = severity === "none" || severity === "low";

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 2 }}>
      <div style={{ display: "flex", gap: 6, marginBottom: 4 }}>
        {(["annual", "summer", "monsoon", "winter"] as const).map((season) => (
          <button
            key={season}
            onClick={() => onSeasonChange(season)}
            style={{
              flex: 1, padding: "6px 0", fontSize: 10, fontWeight: 600,
              borderRadius: 6, border: "1px solid", cursor: "pointer",
              textTransform: "capitalize", fontFamily: "inherit",
              background: activeSeason === season ? "#0E7490" : "transparent",
              color: activeSeason === season ? "#FDFCFB" : "#7B8F83",
              borderColor: activeSeason === season ? "#0E7490" : "rgba(207,214,196,0.6)",
              transition: "all 0.15s ease"
            }}
          >
            {season}
          </button>
        ))}
      </div>
      {/* ── Prevailing direction banner with compass arrow ─────── */}
      <div style={{
        background: "rgba(6,182,212,0.07)", border: "1.5px solid rgba(6,182,212,0.22)",
        borderRadius: 9, padding: "10px 12px", display: "flex", alignItems: "center", gap: 12,
      }}>
        <div style={{
          width: 44, height: 44, borderRadius: "50%", flexShrink: 0,
          border: "2px solid rgba(6,182,212,0.30)", position: "relative",
          display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          {/* compass ticks */}
          <span style={{ position: "absolute", top: 2, fontSize: 6, color: "#7B8F83", fontWeight: 700 }}>N</span>
          {bearing !== null ? (
            <svg width="44" height="44" viewBox="0 0 44 44" style={{ transform: `rotate(${bearing}deg)` }} aria-hidden>
              <path d="M22 7 L26 24 L22 20 L18 24 Z" fill="#0E7490" />
            </svg>
          ) : (
            <span style={{ fontSize: 14, color: "#0E7490", fontWeight: 700 }}>?</span>
          )}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: 12, fontWeight: 700, color: "#0E7490", lineHeight: 1.3 }}>
            Prevailing {prevailing}
          </div>
          <div style={{ fontSize: 10, color: "#7B8F83", marginTop: 2, lineHeight: 1.4 }}>
            {meanSpeed} mean · gusting {gust}
          </div>
        </div>
      </div>

      {/* ── Metrics grid 2×3 ───────────────────────────────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
        {[
          { label: "Mean speed",        value: meanSpeed,    icon: "≈" },
          { label: "Peak gust",         value: gust,         icon: "↟" },
          { label: "Recommended axis",  value: orientation,  icon: "∠" },
          { label: "Wind category",     value: qualVal(result, "Wind category"), icon: "≋" },
          { label: "Gust risk",         value: gustRisk,     icon: "!" },
        ].map(({ label, value, icon }) => (
          <div key={label} style={{ background: "#F2EDE8", borderRadius: 7, padding: "8px 10px" }}>
            <div style={{
              fontSize: 11, fontFamily: "var(--font-geist-mono), monospace",
              fontWeight: 700, color: "#3A3F3B", lineHeight: 1.2,
              display: "flex", alignItems: "baseline", gap: 4,
            }}>
              <span style={{ fontSize: 9, color: "#7B8F83" }}>{icon}</span>
              <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{value}</span>
            </div>
            <div style={{
              fontSize: 9, color: "#7B8F83", marginTop: 4,
              fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.3px",
            }}>
              {label}
            </div>
          </div>
        ))}
      </div>

      {/* ── Seasonal wind speed ────────────────────────────────── */}
      {seasonal.length > 0 && (
        <div style={{ background: "#F2EDE8", borderRadius: 9, padding: "10px 12px" }}>
          <div style={{
            fontSize: 9, fontWeight: 700, textTransform: "uppercase",
            letterSpacing: "0.5px", color: "#7B8F83", marginBottom: 9,
          }}>
            Seasonal Wind Speed
          </div>
          {seasonal.map((p) => {
            const v = Number(p.value) || 0;
            return (
              <div key={String(p.label)} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 7 }}>
                <div style={{ width: 56, fontSize: 10, fontWeight: 600, color: "#7B8F83", flexShrink: 0 }}>
                  {String(p.label)}
                </div>
                <div style={{ flex: 1, height: 6, background: "#CFD6C4", borderRadius: 3, overflow: "hidden" }}>
                  <div style={{
                    height: "100%", borderRadius: 3, width: `${(v / seasMax) * 100}%`,
                    background: "#06B6D4", transition: "width 0.5s ease",
                  }} />
                </div>
                <div style={{
                  width: 48, fontSize: 10, textAlign: "right", color: "#3A3F3B",
                  fontFamily: "var(--font-geist-mono), monospace", flexShrink: 0,
                }}>
                  {v.toFixed(1)} m/s
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Comfort chips ──────────────────────────────────────── */}
      <div style={{ background: "#F2EDE8", borderRadius: 9, padding: "10px 12px" }}>
        <div style={{
          fontSize: 9, fontWeight: 700, textTransform: "uppercase",
          letterSpacing: "0.5px", color: "#7B8F83", marginBottom: 8,
        }}>
          Comfort & Ventilation
        </div>
        {comfort.map(({ label, value }) => (
          <div key={label} style={{
            display: "flex", justifyContent: "space-between", alignItems: "center",
            fontSize: 10, marginBottom: 6,
          }}>
            <span style={{ color: "#7B8F83" }}>{label}</span>
            <span style={{ color: "#3A3F3B", fontWeight: 600 }}>{value}</span>
          </div>
        ))}
      </div>

      {/* ── IS 875 wind-load compliance strip ──────────────────── */}
      <div style={{
        background: calm ? "rgba(90,143,106,0.08)" : "rgba(196,133,90,0.10)",
        border: `1px solid ${calm ? "rgba(90,143,106,0.25)" : "rgba(196,133,90,0.30)"}`,
        borderRadius: 8, padding: "9px 11px", display: "flex", alignItems: "flex-start", gap: 8,
      }}>
        <span style={{ fontSize: 13, marginTop: 1, flexShrink: 0, color: calm ? "#5A8F6A" : "#C4865A" }}>
          {calm ? "✓" : "⚠"}
        </span>
        <div>
          <div style={{ fontSize: 10, fontWeight: 700, color: calm ? "#5A8F6A" : "#C4865A", marginBottom: 2 }}>
            IS 875 (Part 3) : 2015 — Wind Load
          </div>
          <div style={{ fontSize: 10, color: "#7B8F83", lineHeight: 1.5 }}>
            {severity === "high"
              ? "High sustained wind. Design for the basic wind speed of the zone; verify cladding and parapet pressures."
              : severity === "moderate"
              ? "Moderate wind exposure. Standard wind-load provisions apply; confirm terrain category."
              : "Low wind exposure. Favourable for natural ventilation; orient openings to the prevailing direction."}
          </div>
        </div>
      </div>
    </div>
  );
}
