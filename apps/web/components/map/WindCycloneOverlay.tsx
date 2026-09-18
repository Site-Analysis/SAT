// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import React, { useState, useEffect, useRef } from "react";
import type { ModuleResult } from "@/lib/stores/analysis";
import { Eye, Shield, Wind, ChevronDown, ChevronUp, X, Play, Square, Flame } from "lucide-react";
import { useWindCycloneUIStore } from "@/lib/stores/analysis";
import { checkStormGridAvailability, isStormAnimationUnavailable } from "@/lib/cycloneUtils";

interface WindCycloneOverlayProps {
  result: ModuleResult;
  layers?: {
    heatmap?: boolean;
    tracks: boolean;
    windZones: boolean;
    eyePoints: boolean;
  };
  onToggleLayer?: (layerKey: "heatmap" | "windZones" | "tracks" | "eyePoints", enabled: boolean) => void;
  windZoneMode?: "buffer" | "regional" | "all";
  onWindZoneModeChange?: (mode: "buffer" | "regional" | "all") => void;
}

const IMD_LEGEND = [
  { color: "#7E22CE", label: "Super Cyclonic Storm (≥ 62 m/s / ≥ 222 km/h)" },
  { color: "#EF4444", label: "Extremely Severe (47–61 m/s / 167–221 km/h)" },
  { color: "#F97316", label: "Very Severe (33–46 m/s / 119–166 km/h)" },
  { color: "#FBBF24", label: "Severe (25–32 m/s / 89–118 km/h)" },
  { color: "#34D399", label: "Cyclonic Storm (17–24 m/s / 62–88 km/h)" },
  { color: "#60A5FA", label: "Depression (< 17 m/s / < 62 km/h)" },
];

const IS875_LEGEND = [
  { color: "#7E22CE", label: "Zone VI: 55 m/s (Very High Wind Hazard)" },
  { color: "#EF4444", label: "Zone V: 50 m/s (Very High Wind Hazard)" },
  { color: "#F97316", label: "Zone IV: 47 m/s (High Wind Hazard)" },
  { color: "#FBBF24", label: "Zone III: 44 m/s (Moderate Wind Hazard)" },
  { color: "#34D399", label: "Zone II: 39 m/s (Moderate Wind Hazard)" },
  { color: "#60A5FA", label: "Zone I: 33 m/s (Low Wind Hazard)" },
];

export function WindCycloneOverlay({
  result,
  layers: controlledLayers,
  onToggleLayer,
  windZoneMode: controlledWindZoneMode,
  onWindZoneModeChange,
}: WindCycloneOverlayProps) {
  const data = result.windCyclone;
  const [internalLayers, setInternalLayers] = useState({
    heatmap: true,
    tracks: false,
    windZones: false,
    eyePoints: false,
  });

  const layers = controlledLayers || internalLayers;

  // Store connection for docked storm widget and wind zone mode
  const {
    selectedStorm,
    activeStormSid,
    loadingSid,
    fetchError,
    windZoneMode: storeWindZoneMode,
    isDockedMinimized,
    animationAvailability,
    setSelectedStorm,
    setWindZoneMode: setStoreWindZoneMode,
    toggleDockedMinimized,
    setAnimationAvailability,
  } = useWindCycloneUIStore();

  useEffect(() => {
    if (!selectedStorm?.sid) return;
    const sid = selectedStorm.sid;
    if (animationAvailability[sid] !== undefined) return;

    checkStormGridAvailability(selectedStorm).then((avail) => {
      setAnimationAvailability(sid, avail);
    });
  }, [selectedStorm, animationAvailability, setAnimationAvailability]);

  const isAnimUnavailable = selectedStorm
    ? isStormAnimationUnavailable(selectedStorm, animationAvailability)
    : false;

  const windZoneMode = controlledWindZoneMode || storeWindZoneMode;

  const handleWindZoneModeChange = (mode: "buffer" | "regional" | "all") => {
    setStoreWindZoneMode(mode);
    if (onWindZoneModeChange) onWindZoneModeChange(mode);
  };

  const toggle = (key: "heatmap" | "windZones" | "tracks" | "eyePoints") => {
    const next = !layers[key];
    setInternalLayers((prev) => ({ ...prev, [key]: next }));
    if (onToggleLayer) onToggleLayer(key, next);
  };

  const handleAnimateFromDocked = (sid: string, name: string) => {
    if (typeof window !== "undefined") {
      window.dispatchEvent(
        new CustomEvent("sat:animate-storm", { detail: { sid, name } })
      );
    }
  };

  const handleStopAnimationFromDocked = () => {
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("sat:stop-animation"));
    }
  };

  if (!data) return null;

  const vb = data.statutory_v_b_ms;
  const metrics = data.metrics;

  return (
    <div style={{ position: "absolute", inset: 0, pointerEvents: "none", zIndex: 400 }}>
      {/* Top-left Stack: Statutory Vb Badge + Docked Storm Summary Widget */}
      <div
        style={{
          position: "absolute",
          top: 14,
          left: 14,
          display: "flex",
          flexDirection: "column",
          gap: 10,
          pointerEvents: "none",
          maxWidth: 250,
        }}
      >
        {/* Statutory Wind & Cyclone Summary Badge */}
        <div
          style={{
            background: "rgba(253,252,251,0.97)",
            borderRadius: 10,
            padding: "10px 14px",
            boxShadow: "0 4px 18px rgba(0,0,0,0.12)",
            pointerEvents: "auto",
            width: "100%",
          }}
        >
          <div
            style={{
              fontSize: 9,
              color: "#0284C7",
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: "0.5px",
              marginBottom: 2,
            }}
          >
            Vb (Basic Design Wind Speed)
          </div>
          <div
            style={{
              fontSize: 22,
              fontWeight: 800,
              lineHeight: 1,
              color: "#0F172A",
              fontFamily: "var(--font-geist-mono), monospace",
            }}
          >
            {vb.toFixed(1)} m/s
          </div>
          <div style={{ fontSize: 9.5, color: "#64748B", marginTop: 3, fontWeight: 500 }}>
            {data.damage_risk_category?.replace(/Damage Risk/gi, "Wind Hazard")}
          </div>
          <div style={{ fontSize: 9, color: "#0284C7", marginTop: 4, fontWeight: 600 }}>
            {metrics.total_historical_events} storms in buffer · {metrics.annual_rate_50yr.toFixed(2)}/yr
          </div>
          {data.is_coastal_buffer && (
            <div
              style={{
                fontSize: 8.5,
                color: "#B45309",
                marginTop: 4,
                fontWeight: 600,
                background: "#FEF3C7",
                padding: "2px 6px",
                borderRadius: 4,
              }}
            >
              {data.coastal_penalty_applied ? "10 km Coastal Penalty Active (≥ 39 m/s)" : "Coastal Zone (≤ 10 km)"}
            </div>
          )}
        </div>

        {/* Docked Storm Summary Widget (Anchored directly beneath top-left summary card) */}
        {selectedStorm && (
          <div
            style={{
              background: "rgba(253,252,251,0.98)",
              borderRadius: 10,
              padding: isDockedMinimized ? "8px 12px" : "10px 14px",
              boxShadow: "0 4px 18px rgba(0,0,0,0.15)",
              pointerEvents: "auto",
              border: "1px solid rgba(2,132,199,0.25)",
              width: "100%",
              transition: "all 0.2s ease-in-out",
            }}
          >
            {/* Widget Header */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 6 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, minWidth: 0 }}>
                <Wind size={13} className="text-sky-600 shrink-0" />
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    color: "#0F172A",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {selectedStorm.name}
                </span>
                <span
                  style={{
                    fontSize: 9,
                    fontWeight: 600,
                    color: "#64748B",
                    background: "#F1F5F9",
                    padding: "1px 5px",
                    borderRadius: 4,
                  }}
                >
                  {selectedStorm.season}
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 2, flexShrink: 0 }}>
                <button
                  type="button"
                  onClick={toggleDockedMinimized}
                  title={isDockedMinimized ? "Expand card" : "Minimize card"}
                  style={{
                    background: "transparent",
                    border: "none",
                    cursor: "pointer",
                    padding: 3,
                    borderRadius: 4,
                    color: "#64748B",
                    display: "flex",
                    alignItems: "center",
                  }}
                >
                  {isDockedMinimized ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
                </button>
                <button
                  type="button"
                  onClick={() => setSelectedStorm(null)}
                  title="Close active storm view"
                  style={{
                    background: "transparent",
                    border: "none",
                    cursor: "pointer",
                    padding: 3,
                    borderRadius: 4,
                    color: "#64748B",
                    display: "flex",
                    alignItems: "center",
                  }}
                >
                  <X size={14} />
                </button>
              </div>
            </div>

            {/* Expanded Content */}
            {!isDockedMinimized ? (
              <div style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 6 }}>
                {selectedStorm.category && (
                  <div
                    style={{
                      fontSize: 9.5,
                      fontWeight: 600,
                      color: "#0369A1",
                      background: "#E0F2FE",
                      padding: "2px 6px",
                      borderRadius: 4,
                      display: "inline-block",
                      alignSelf: "flex-start",
                    }}
                  >
                    {selectedStorm.category.split(" (")[0]}
                  </div>
                )}
                <div style={{ display: "flex", flexDirection: "column", gap: 3, fontSize: 10 }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748B" }}>Max Wind Speed:</span>
                    {selectedStorm.max_wind_ms && selectedStorm.max_wind_ms > 0 ? (
                      <span style={{ fontWeight: 700, color: "#E11D48" }}>
                        {selectedStorm.max_wind_ms} m/s ({selectedStorm.max_wind_kmh ?? Math.round(selectedStorm.max_wind_ms * 3.6)} km/h)
                      </span>
                    ) : (
                      <span style={{ fontWeight: 500, color: "#64748B" }}>
                        No data available
                      </span>
                    )}
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748B" }}>Min Pressure:</span>
                    <span style={{ fontWeight: 600, color: "#334155" }}>
                      {selectedStorm.min_pressure_hpa} hPa
                    </span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={{ color: "#64748B" }}>Closest to Site:</span>
                    <span style={{ fontWeight: 700, color: "#0F172A" }}>
                      {selectedStorm.closest_distance_km} km
                    </span>
                  </div>
                </div>

                {/* Action Button: Animate / Stop */}
                <div style={{ marginTop: 4, paddingTop: 6, borderTop: "1px solid #E2E8F0" }}>
                  {activeStormSid === selectedStorm.sid ? (
                    <button
                      type="button"
                      onClick={handleStopAnimationFromDocked}
                      style={{
                        width: "100%",
                        padding: "5px 8px",
                        background: "#E11D48",
                        color: "#FFFFFF",
                        border: "none",
                        borderRadius: 6,
                        fontSize: 10.5,
                        fontWeight: 600,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: 6,
                        cursor: "pointer",
                        boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
                      }}
                    >
                      <Square size={12} fill="currentColor" />
                      <span>Stop Wind Animation</span>
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={() => handleAnimateFromDocked(selectedStorm.sid, selectedStorm.name)}
                      disabled={loadingSid === selectedStorm.sid || isAnimUnavailable}
                      style={{
                        width: "100%",
                        padding: "5px 8px",
                        background:
                          loadingSid === selectedStorm.sid
                            ? "#94A3B8"
                            : isAnimUnavailable
                            ? "#CBD5E1"
                            : "#0284C7",
                        color: isAnimUnavailable ? "#64748B" : "#FFFFFF",
                        border: "none",
                        borderRadius: 6,
                        fontSize: 10.5,
                        fontWeight: 600,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        gap: 6,
                        cursor:
                          loadingSid === selectedStorm.sid || isAnimUnavailable
                            ? "not-allowed"
                            : "pointer",
                        boxShadow: isAnimUnavailable ? "none" : "0 1px 3px rgba(0,0,0,0.1)",
                        opacity: isAnimUnavailable ? 0.8 : 1,
                      }}
                    >
                      {loadingSid === selectedStorm.sid ? (
                        <>
                          <span className="animate-spin inline-block w-3 h-3 border-2 border-white border-t-transparent rounded-full" />
                          <span>Loading Grid...</span>
                        </>
                      ) : (
                        <>
                          <Play size={12} fill="currentColor" />
                          <span>▶ Animate Storm Peak</span>
                        </>
                      )}
                    </button>
                  )}
                  {isAnimUnavailable && (
                    <div
                      style={{
                        marginTop: 5,
                        fontSize: 9.5,
                        color: "#475569",
                        background: "#F1F5F9",
                        border: "1px solid #E2E8F0",
                        padding: "5px 8px",
                        borderRadius: 6,
                        lineHeight: 1.3,
                        textAlign: "center",
                        fontWeight: 500,
                      }}
                    >
                      No storm animation available for this historical track
                    </div>
                  )}
                  {fetchError && !isAnimUnavailable && (
                    <div
                      style={{
                        marginTop: 4,
                        fontSize: 9.5,
                        color: "#475569",
                        background: "#F1F5F9",
                        border: "1px solid #E2E8F0",
                        padding: "4px 6px",
                        borderRadius: 4,
                        lineHeight: 1.2,
                        textAlign: "center",
                        fontWeight: 500,
                      }}
                    >
                      No storm animation available for this historical track
                    </div>
                  )}
                </div>
              </div>
            ) : (
              /* Minimized compact row */
              <div
                style={{
                  marginTop: 4,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  fontSize: 9.5,
                }}
              >
                {selectedStorm.max_wind_ms && selectedStorm.max_wind_ms > 0 ? (
                  <span style={{ color: "#E11D48", fontWeight: 700 }}>
                    {selectedStorm.max_wind_ms} m/s
                  </span>
                ) : (
                  <span style={{ color: "#64748B", fontWeight: 500 }}>
                    N/A
                  </span>
                )}
                <span style={{ color: "#64748B" }}>
                  {selectedStorm.closest_distance_km} km to site
                </span>
                {activeStormSid === selectedStorm.sid && (
                  <span
                    style={{
                      color: "#16A34A",
                      fontWeight: 600,
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 3,
                    }}
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    Animating
                  </span>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Top-right Independent Layer Toggles */}
      <div
        style={{
          position: "absolute",
          top: 60,
          right: 14,
          background: "rgba(253,252,251,0.97)",
          borderRadius: 9,
          padding: "8px 10px",
          boxShadow: "0 2px 12px rgba(0,0,0,0.12)",
          pointerEvents: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 6,
        }}
      >
        <div
          style={{
            fontSize: 9,
            fontWeight: 700,
            color: "#64748B",
            textTransform: "uppercase",
            letterSpacing: "0.4px",
          }}
        >
          Map Layers
        </div>
        <button
          type="button"
          onClick={() => toggle("heatmap")}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            fontSize: 10,
            fontWeight: 600,
            color: layers.heatmap ? "#0284C7" : "#64748B",
            background: layers.heatmap ? "#E0F2FE" : "transparent",
            border: "none",
            borderRadius: 5,
            padding: "3px 7px",
            cursor: "pointer",
          }}
        >
          <Flame size={12} />
          <span>Cyclone Heatmap ({layers.heatmap ? "ON" : "OFF"})</span>
        </button>

        <button
          type="button"
          onClick={() => toggle("tracks")}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            fontSize: 10,
            fontWeight: 600,
            color: layers.tracks ? "#0284C7" : "#64748B",
            background: layers.tracks ? "#E0F2FE" : "transparent",
            border: "none",
            borderRadius: 5,
            padding: "3px 7px",
            cursor: "pointer",
          }}
        >
          <Wind size={12} />
          <span>Cyclone Tracks ({layers.tracks ? "ON" : "OFF"})</span>
        </button>

        <div>
          <button
            type="button"
            onClick={() => toggle("windZones")}
            style={{
              width: "100%",
              display: "flex",
              alignItems: "center",
              gap: 6,
              fontSize: 10,
              fontWeight: 600,
              color: layers.windZones ? "#0284C7" : "#64748B",
              background: layers.windZones ? "#E0F2FE" : "transparent",
              border: "none",
              borderRadius: 5,
              padding: "3px 7px",
              cursor: "pointer",
            }}
          >
            <Shield size={12} />
            <span>IS 875 Wind Zones ({layers.windZones ? "ON" : "OFF"})</span>
          </button>

          {/* 3-Way Segmented Control for Wind Zones when ON */}
          {layers.windZones && (
            <div
              style={{
                marginLeft: 18,
                marginTop: 4,
                display: "flex",
                background: "#F1F5F9",
                borderRadius: 5,
                padding: 2,
                gap: 2,
              }}
            >
              {(
                [
                  { id: "buffer", label: "Buffer Focus" },
                  { id: "regional", label: "Regional" },
                  { id: "all", label: "All Zones" },
                ] as const
              ).map((tab) => {
                const active = windZoneMode === tab.id;
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => handleWindZoneModeChange(tab.id)}
                    style={{
                      flex: 1,
                      fontSize: 8.5,
                      fontWeight: 700,
                      padding: "2.5px 4px",
                      borderRadius: 3,
                      border: "none",
                      cursor: "pointer",
                      whiteSpace: "nowrap",
                      background: active ? "#FFFFFF" : "transparent",
                      color: active ? "#0284C7" : "#64748B",
                      boxShadow: active ? "0 1px 2px rgba(0,0,0,0.08)" : "none",
                      transition: "all 0.15s ease",
                    }}
                  >
                    {tab.label}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <button
          type="button"
          onClick={() => toggle("eyePoints")}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            fontSize: 10,
            fontWeight: 600,
            color: layers.eyePoints ? "#0284C7" : "#64748B",
            background: layers.eyePoints ? "#E0F2FE" : "transparent",
            border: "none",
            borderRadius: 5,
            padding: "3px 7px",
            cursor: "pointer",
          }}
        >
          <Eye size={12} />
          <span>Storm Eye Points ({layers.eyePoints ? "ON" : "OFF"})</span>
        </button>
      </div>


      {/* Bottom-right Stacked Map Legends (Cyclone Heatmap, Cyclone Tracks & IS 875 Wind Zones) */}
      {(layers.heatmap || layers.tracks || layers.windZones) && (
        <div
          style={{
            position: "absolute",
            bottom: 20,
            right: 14,
            display: "flex",
            flexDirection: "column",
            gap: 10,
            pointerEvents: "auto",
            maxWidth: 260,
            width: 260,
            zIndex: 400,
          }}
        >
          {/* Cyclone Heatmap Density Legend */}
          {layers.heatmap && (
            <div
              style={{
                background: "#FFFFFF",
                borderRadius: 10,
                padding: "9px 12px",
                boxShadow: "0 3px 14px rgba(0,0,0,0.09)",
                border: "1px solid #E2E8F0",
                transition: "all 0.2s ease-in-out",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: 6,
                  borderBottom: "1px solid #F1F5F9",
                  paddingBottom: 4,
                }}
              >
                <span
                  style={{
                    fontSize: 9.5,
                    fontWeight: 700,
                    color: "#0F172A",
                    textTransform: "uppercase",
                    letterSpacing: "0.3px",
                    display: "flex",
                    alignItems: "center",
                    gap: 5,
                  }}
                >
                  <Flame size={11} className="text-sky-600" />
                  Cyclone Heatmap
                </span>
                <span
                  style={{
                    fontSize: 8.5,
                    color: "#64748B",
                    fontWeight: 600,
                  }}
                >
                  Windy Density
                </span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 3.5 }}>
                <div
                  style={{
                    height: 8,
                    borderRadius: 4,
                    background: "linear-gradient(to right, #0000ff, #00ff00, #ffff00, #ff8800, #ff0000)",
                    width: "100%",
                  }}
                />
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: 8.5,
                    color: "#64748B",
                    fontWeight: 500,
                  }}
                >
                  <span>Low Risk</span>
                  <span>Moderate</span>
                  <span>Extreme</span>
                </div>
              </div>
            </div>
          )}

          {/* 1. Cyclone Tracks Legend (Pure White Card) */}
          {layers.tracks && (
            <div
              style={{
                background: "#FFFFFF",
                borderRadius: 10,
                padding: "9px 12px",
                boxShadow: "0 3px 14px rgba(0,0,0,0.09)",
                border: "1px solid #E2E8F0",
                transition: "all 0.2s ease-in-out",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: 6,
                  borderBottom: "1px solid #F1F5F9",
                  paddingBottom: 4,
                }}
              >
                <span
                  style={{
                    fontSize: 9.5,
                    fontWeight: 700,
                    color: "#0F172A",
                    textTransform: "uppercase",
                    letterSpacing: "0.3px",
                    display: "flex",
                    alignItems: "center",
                    gap: 5,
                  }}
                >
                  <Wind size={11} className="text-sky-600" />
                  Cyclone Tracks
                </span>
                <span
                  style={{
                    fontSize: 8.5,
                    color: "#64748B",
                    fontWeight: 600,
                  }}
                >
                  IMD Tiers
                </span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 3.5 }}>
                {IMD_LEGEND.map(({ color, label }) => (
                  <div key={label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span
                      style={{
                        width: 14,
                        height: 3.5,
                        borderRadius: 2,
                        background: color,
                        flexShrink: 0,
                        display: "inline-block",
                      }}
                    />
                    <span style={{ fontSize: 8.5, color: "#334155", fontWeight: 500, lineHeight: 1.2 }}>
                      {label}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 2. IS 875 Wind Zones Legend (Faint Slate/Tinted Card) */}
          {layers.windZones && (
            <div
              style={{
                background: "rgba(248, 250, 252, 0.98)", // Slate-50 background for distinct color delineation
                borderRadius: 10,
                padding: "9px 12px",
                boxShadow: "0 3px 14px rgba(0,0,0,0.09)",
                border: "1px solid #CBD5E1", // Distinct border treatment
                transition: "all 0.2s ease-in-out",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: 6,
                  borderBottom: "1px solid #E2E8F0",
                  paddingBottom: 4,
                }}
              >
                <span
                  style={{
                    fontSize: 9.5,
                    fontWeight: 700,
                    color: "#0F172A",
                    textTransform: "uppercase",
                    letterSpacing: "0.3px",
                    display: "flex",
                    alignItems: "center",
                    gap: 5,
                  }}
                >
                  <Shield size={11} className="text-slate-700" />
                  IS 875 Wind Zones
                </span>
                <span
                  style={{
                    fontSize: 8.5,
                    color: "#64748B",
                    fontWeight: 600,
                  }}
                >
                  Vb Baseline
                </span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 3.5 }}>
                {IS875_LEGEND.map(({ color, label }) => (
                  <div key={label} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <span
                      style={{
                        width: 10,
                        height: 10,
                        borderRadius: 2,
                        background: color,
                        opacity: 0.85,
                        border: "1px solid rgba(0,0,0,0.2)",
                        flexShrink: 0,
                        display: "inline-block",
                      }}
                    />
                    <span style={{ fontSize: 8.5, color: "#334155", fontWeight: 500, lineHeight: 1.2 }}>
                      {label}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default WindCycloneOverlay;
