// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Wind,
  ShieldAlert,
  AlertTriangle,
  Info,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Sliders,
  Layers,
  Activity,
  BarChart2,
} from "lucide-react";
import type {
  ModuleResult,
  Severity,
  SiteResilienceReportData,
  PrioritizedMitigationItem,
} from "@/lib/stores/analysis";
import { useAnalysisStore } from "@/lib/stores/analysis";
import { useConfigStore } from "@/lib/stores/config";
import { getWindCycloneRecommendations, getWindCycloneAnalysis } from "@/lib/api/analysis";

interface WindCyclonePanelProps {
  result?: ModuleResult;
  severity: Severity;
  lat?: number;
  lng?: number;
  startDate?: string;
  endDate?: string;
  onBufferChange?: (bufferKm: number) => void;
  onReRunAnalysis?: (bufferKm: number) => void;
}

const TOOLTIPS = {
  vb: "The 3-second peak gust wind speed at 10m height above ground in open terrain with a 50-year return period, as mandated by IS 875 (Part 3): 2015 for structural design calculations.",
  annualRate: "The average number of tropical cyclones passing within your selected buffer per year over the analyzed period. Used to evaluate empirical recurrence intervals.",
  maxGust: "The highest sustained 1-minute or 3-second wind speed recorded by meteorological reconnaissance (IBTrACS) inside this site's buffer zone.",
  closestDist: "Minimum distance a historical cyclone eye passed relative to the project site centroid.",
  coastalPenalty: "IS 875 Part 3 mandates that any site within 10 km of the coastline must not use a design wind speed less than the coastal threshold (Vb ≥ 39 m/s).",
  verticalProfile: "Shows how mean wind velocity accelerates with building height due to atmospheric boundary layer mechanics, assisting facade and high-rise structural engineers.",
};

const IMD_COLOR_MAP: Record<string, { color: string; abbrev: string }> = {
  "Super Cyclonic Storm (>=62 m/s)": { color: "#7E22CE", abbrev: "SuCS" },
  "Extremely Severe Cyclonic Storm (47-61 m/s)": { color: "#EF4444", abbrev: "ESCS" },
  "Very Severe Cyclonic Storm (33-46 m/s)": { color: "#F97316", abbrev: "VSCS" },
  "Severe Cyclonic Storm (25-32 m/s)": { color: "#FBBF24", abbrev: "SCS" },
  "Cyclonic Storm (17-24 m/s)": { color: "#34D399", abbrev: "CS" },
  "Depression / Deep Depression (<17 m/s)": { color: "#60A5FA", abbrev: "D/DD" },
};

function HelpTooltip({ text }: { text: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative inline-block ml-1">
      <button
        type="button"
        className="text-neutral-400 hover:text-neutral-600 focus:outline-none focus:text-neutral-700 align-middle"
        onClick={() => setOpen(!open)}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        aria-label="More information"
      >
        <Info size={12} />
      </button>
      {open && (
        <div className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-1.5 w-64 p-2.5 bg-neutral-900 text-white text-[11px] leading-snug rounded-lg shadow-xl pointer-events-none">
          {text}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-neutral-900" />
        </div>
      )}
    </div>
  );
}

type BufferRadius = 50 | 100 | 250;

export function WindCyclonePanel({
  result,
  severity,
  lat = 13.0827,
  lng = 80.2707,
  startDate: propStartDate,
  endDate: propEndDate,
  onBufferChange,
  onReRunAnalysis,
}: WindCyclonePanelProps) {
  const config = useConfigStore();
  const startDate = propStartDate || config.startDate;
  const endDate = propEndDate || config.endDate;

  const [selectedBuffer, setSelectedBuffer] = useState<BufferRadius>(100);

  // 1. Local Cache keyed by buffer radius: { 50: null, 100: null, 250: null }
  const cacheRef = useRef<Record<BufferRadius, ModuleResult | null>>({
    50: null,
    100: null,
    250: null,
  });
  const [, setCacheState] = useState<Record<BufferRadius, ModuleResult | null>>({
    50: null,
    100: null,
    250: null,
  });

  // Clear cache if analysis date range changes
  useEffect(() => {
    cacheRef.current = { 50: null, 100: null, 250: null };
    setCacheState({ 50: null, 100: null, 250: null });
  }, [startDate, endDate]);

  // Track background in-flight API requests to avoid duplicate fetches
  const fetchingRef = useRef<Record<BufferRadius, boolean>>({
    50: false,
    100: false,
    250: false,
  });

  // Localized loading spinner state for button when a requested radius is still loading
  const [loadingRadius, setLoadingRadius] = useState<BufferRadius | null>(null);
  const pendingRadiusRef = useRef<BufferRadius | null>(null);

  const [report, setReport] = useState<SiteResilienceReportData | null>(null);
  const [reportLoading, setReportLoading] = useState<boolean>(false);
  const [reportError, setReportError] = useState<string | null>(null);
  const [openMitigations, setOpenMitigations] = useState<Record<number, boolean>>({
    0: true,
    1: true,
  });

  // Active result derived from cache or incoming props
  const activeResult = cacheRef.current[selectedBuffer] ?? result;
  const data = activeResult?.windCyclone;
  const hasData = Boolean(data);

  // 2. Background Pre-fetching:
  // When user initiates analysis, default 100km radius is fetched first and rendered immediately.
  // Once 100km data is successfully received and the UI is unblocked, silently trigger 50km and 250km in background.
  useEffect(() => {
    if (!hasData || !lat || !lng) return;

    // Cache initial 100km data if not already cached
    if (result && !cacheRef.current[100]) {
      cacheRef.current[100] = result;
      setCacheState((prev) => ({ ...prev, 100: result }));
    }

    const prefetchRadii: (50 | 250)[] = [50, 250];
    prefetchRadii.forEach((radius) => {
      if (!cacheRef.current[radius] && !fetchingRef.current[radius]) {
        fetchingRef.current[radius] = true;
        getWindCycloneAnalysis({ lat, lng, startDate, endDate }, radius)
          .then((res) => {
            cacheRef.current[radius] = res;
            setCacheState((prev) => ({ ...prev, [radius]: res }));
            // If user clicked this radius while background fetch was in progress:
            if (pendingRadiusRef.current === radius) {
              pendingRadiusRef.current = null;
              setLoadingRadius(null);
              applyBufferSelection(radius, res);
            }
          })
          .catch((err) => {
            console.warn(`[WindCyclone] Background pre-fetch failed for ${radius}km:`, err);
            if (pendingRadiusRef.current === radius) {
              pendingRadiusRef.current = null;
              setLoadingRadius(null);
            }
          })
          .finally(() => {
            fetchingRef.current[radius] = false;
          });
      }
    });
  }, [hasData, lat, lng, result]);

  // Recommendations report fetch for selected buffer
  useEffect(() => {
    if (!hasData || !lat || !lng) return;
    setReportLoading(true);
    setReportError(null);
    getWindCycloneRecommendations({ lat, lng }, selectedBuffer)
      .then((res) => {
        setReport(res);
        setReportLoading(false);
      })
      .catch((err) => {
        setReportError(err instanceof Error ? err.message : "Failed to load recommendations");
        setReportLoading(false);
      });
  }, [hasData, lat, lng, selectedBuffer]);

  // Apply buffer data to local state, global analysis store (map), and callbacks
  const applyBufferSelection = (radiusKm: BufferRadius, bufferData: ModuleResult) => {
    setSelectedBuffer(radiusKm);
    useAnalysisStore.getState().setModuleResult("windCyclone", bufferData);
    if (onBufferChange) onBufferChange(radiusKm);
    if (onReRunAnalysis) onReRunAnalysis(radiusKm);
  };

  // 3. Instant Cache Retrieval:
  // Check if requested radius data already exists in cache.
  // - If exists: instantly update map and UI state with cached data.
  // - If does not exist: show localized loading spinner on button until background fetch completes.
  const handleBufferSelect = (radiusKm: BufferRadius) => {
    if (selectedBuffer === radiusKm) return;

    const cachedData = cacheRef.current[radiusKm];
    if (cachedData) {
      // Instant cache retrieval: no loading spinner, immediate state & map update
      setLoadingRadius(null);
      pendingRadiusRef.current = null;
      applyBufferSelection(radiusKm, cachedData);
      return;
    }

    // Cache miss or still in-flight: show localized loading spinner on button
    setLoadingRadius(radiusKm);
    pendingRadiusRef.current = radiusKm;

    if (!fetchingRef.current[radiusKm] && lat && lng) {
      fetchingRef.current[radiusKm] = true;
      getWindCycloneAnalysis({ lat, lng, startDate, endDate }, radiusKm)
        .then((res) => {
          cacheRef.current[radiusKm] = res;
          setCacheState((prev) => ({ ...prev, [radiusKm]: res }));
          if (pendingRadiusRef.current === radiusKm) {
            pendingRadiusRef.current = null;
            setLoadingRadius(null);
            applyBufferSelection(radiusKm, res);
          }
        })
        .catch((err) => {
          console.error(`[WindCyclone] Failed to load ${radiusKm}km analysis:`, err);
          setLoadingRadius(null);
          pendingRadiusRef.current = null;
        })
        .finally(() => {
          fetchingRef.current[radiusKm] = false;
        });
    }
  };

  const toggleMitigation = (idx: number) => {
    setOpenMitigations((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  if (!data) {
    return (
      <div className="p-4 text-xs text-neutral-500 italic">
        Wind hazard and cyclone data unavailable. Select a site within India.
      </div>
    );
  }

  const statutoryVb = data.statutory_v_b_ms;
  const vbKmh = Math.round(statutoryVb * 3.6);
  const metrics = data.metrics;

  // Decadal chart max count & integer Y-axis ticks
  const decadalEntries = Object.entries(data.decadal_trend);
  const maxDecadalCount = Math.max(...decadalEntries.map(([, c]) => c), 1);
  const yTicks = Array.from({ length: Math.min(maxDecadalCount + 1, 6) }, (_, i) =>
    Math.round((i * maxDecadalCount) / Math.min(maxDecadalCount, 5))
  ).filter((v, i, a) => a.indexOf(v) === i);

  return (
    <div className="space-y-3.5 pt-1">
      {/* Control Panel: Buffer Selector */}
      <div className="p-3 rounded-lg bg-neutral-50 border border-neutral-200 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-neutral-700 flex items-center gap-1.5">
            <Sliders size={13} className="text-sky-600" />
            Cyclone Search Buffer Radius
          </span>
          <span className="text-[10px] font-medium text-neutral-500">
            {selectedBuffer} km radius
          </span>
        </div>
        <div className="grid grid-cols-3 gap-1.5">
          {([50, 100, 250] as const).map((r) => {
            const active = selectedBuffer === r;
            const isLoading = loadingRadius === r;
            return (
              <button
                key={r}
                type="button"
                onClick={() => handleBufferSelect(r)}
                disabled={isLoading}
                className={`py-1.5 px-2 text-xs font-medium rounded-md border transition-all flex items-center justify-center gap-1.5 ${
                  active
                    ? "bg-sky-600 text-white border-sky-600 shadow-sm font-semibold"
                    : "bg-white text-neutral-600 border-neutral-200 hover:bg-neutral-100"
                } ${isLoading ? "opacity-80 cursor-wait" : ""}`}
              >
                {isLoading ? (
                  <>
                    <span
                      className={`animate-spin inline-block w-3 h-3 border-2 rounded-full border-t-transparent ${
                        active ? "border-white" : "border-sky-600"
                      }`}
                    />
                    <span>{r} km</span>
                  </>
                ) : (
                  <>
                    <span>{r} km</span>
                    {r === 100 && <span className="text-[10px] opacity-80">(Default)</span>}
                  </>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Statutory Baseline & Risk Badges */}
      <div className="p-3.5 rounded-xl bg-sky-950/5 border border-sky-200 space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-sky-800 flex items-center gap-1">
            Vb (Basic Design Wind Speed)
            <HelpTooltip text={TOOLTIPS.vb} />
          </span>
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-100 text-sky-800 border border-sky-300">
            {data.damage_risk_category?.replace(/Damage Risk/gi, "Wind Hazard")}
          </span>
        </div>

        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-black text-neutral-900 tracking-tight">
            {statutoryVb.toFixed(1)}{" "}
            <span className="text-sm font-medium text-neutral-500">m/s</span>
          </span>
          <span className="text-xs font-medium text-neutral-500">
            ({vbKmh} km/h 3-sec peak gust)
          </span>
        </div>

        {data.is_coastal_buffer && (
          <div className="flex items-center gap-1.5 pt-1 text-[11px] font-medium text-amber-800 bg-amber-50 border border-amber-200 p-2 rounded-md">
            <AlertTriangle size={13} className="shrink-0 text-amber-600" />
            <span>
              {data.coastal_penalty_applied
                ? "Mandatory 10 km Coastal Penalty applied: Vb elevated to 39.0 m/s minimum floor."
                : "Site in coastal belt (≤ 10 km). Coastal high-wind provisions active."}
            </span>
            <HelpTooltip text={TOOLTIPS.coastalPenalty} />
          </div>
        )}
      </div>

      {/* 4 Summary KPI Metric Cards */}
      <div className="grid grid-cols-2 gap-2">
        <div className="p-3 rounded-lg bg-neutral-50 border border-neutral-200 space-y-1">
          <div className="flex items-center justify-between text-[10px] font-medium text-neutral-500">
            <span>Total Storms ({selectedBuffer}km, {metrics.period_years ?? 50} Years)</span>
          </div>
          <div className="text-lg font-bold text-neutral-900">
            {metrics.total_historical_events}{" "}
            <span className="text-[10px] font-normal text-neutral-500">events</span>
          </div>
        </div>

        <div className="p-3 rounded-lg bg-neutral-50 border border-neutral-200 space-y-1">
          <div className="flex items-center justify-between text-[10px] font-medium text-neutral-500">
            <span>Annual Rate ({metrics.period_years ?? 50} Yrs)</span>
            <HelpTooltip text={TOOLTIPS.annualRate} />
          </div>
          <div className="text-lg font-bold text-neutral-900">
            {metrics.annual_rate_50yr.toFixed(2)}{" "}
            <span className="text-[10px] font-normal text-neutral-500">/yr</span>
          </div>
        </div>

        <div className="p-3 rounded-lg bg-neutral-50 border border-neutral-200 space-y-1">
          <div className="flex items-center justify-between text-[10px] font-medium text-neutral-500">
            <span>Max Historical Gust</span>
            <HelpTooltip text={TOOLTIPS.maxGust} />
          </div>
          <div className="text-lg font-bold text-rose-600">
            {metrics.total_historical_events > 0 && metrics.max_recorded_wind_speed_ms > 0
              ? `${metrics.max_recorded_wind_speed_ms.toFixed(1)} m/s`
              : "N/A"}
          </div>
          {metrics.total_historical_events > 0 && metrics.max_recorded_wind_speed_ms > 0 ? (
            <div className="text-[9px] text-neutral-400">
              ({metrics.max_recorded_wind_speed_kmh.toFixed(0)} km/h)
            </div>
          ) : (
            <div className="text-[9px] text-neutral-400">No recorded storms</div>
          )}
        </div>

        <div className="p-3 rounded-lg bg-neutral-50 border border-neutral-200 space-y-1">
          <div className="flex items-center justify-between text-[10px] font-medium text-neutral-500">
            <span>Closest Landfall</span>
            <HelpTooltip text={TOOLTIPS.closestDist} />
          </div>
          <div className="text-lg font-bold text-neutral-900">
            {metrics.closest_recorded_distance_km > 0
              ? `${metrics.closest_recorded_distance_km.toFixed(1)} km`
              : "—"}
          </div>
        </div>
      </div>

      {/* Decadal Frequency Trend Bar Chart with Integer Y-Axis Ticks */}
      <div className="p-3.5 rounded-lg border border-neutral-200 bg-white space-y-2">
        <div className="flex items-center justify-between text-xs font-semibold text-neutral-800">
          <span>Decadal Storm Frequency (1970s–2020s)</span>
          <span className="text-[10px] font-normal text-neutral-400">Integer counts</span>
        </div>

        {metrics.total_historical_events === 0 ? (
          <div className="py-4 text-center px-3 bg-neutral-50 rounded border border-dashed border-neutral-200">
            <p className="text-[11px] font-medium text-neutral-600 leading-snug">
              No historical cyclone tracks recorded within this {selectedBuffer} km buffer zone. Expand search radius to inspect regional paths.
            </p>
          </div>
        ) : (
          <div className="relative pt-4 pb-1">
            {/* Y-axis grid lines with integer step ticks */}
            <div className="absolute inset-x-0 top-4 bottom-6 flex flex-col justify-between pointer-events-none">
              {[...yTicks].reverse().map((tick) => (
                <div key={tick} className="border-b border-neutral-100 w-full flex justify-between">
                  <span className="text-[8px] font-mono text-neutral-300 -mt-2">{tick}</span>
                </div>
              ))}
            </div>

            <div className="h-28 flex items-end gap-2 px-3 relative z-10">
              {decadalEntries.map(([decade, count]) => {
                const heightPct = (count / maxDecadalCount) * 100;
                return (
                  <div key={decade} className="flex-1 flex flex-col items-center gap-1 group">
                    <span className="text-[9.5px] font-bold font-mono text-neutral-700">
                      {count}
                    </span>
                    <div className="w-full bg-neutral-100 rounded-t h-20 flex items-end overflow-hidden">
                      <div
                        className="w-full bg-sky-600 group-hover:bg-sky-700 transition-all rounded-t"
                        style={{ height: `${Math.max(heightPct, 4)}%` }}
                      />
                    </div>
                    <span className="text-[9.5px] font-medium text-neutral-500">{decade}s</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* IMD Intensity Distribution - Clean Horizontal Bar Chart (No X-Axis Overlap) */}
      <div className="p-3.5 rounded-lg border border-neutral-200 bg-white space-y-2.5">
        <div className="flex items-center justify-between text-xs font-semibold text-neutral-800">
          <span>IMD Storm Intensity Breakdown</span>
          <span className="text-[10px] font-normal text-neutral-400">IMD Classification</span>
        </div>

        {metrics.total_historical_events === 0 ? (
          <div className="py-4 text-center px-3 bg-neutral-50 rounded border border-dashed border-neutral-200">
            <p className="text-[11px] font-medium text-neutral-600 leading-snug">
              No historical cyclone tracks recorded within this {selectedBuffer} km buffer zone. Expand search radius to inspect regional paths.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {[
              { key: "Super Cyclonic Storm (>=62 m/s)", label: "Super Cyclonic", abbrev: "SuCS", color: "#7E22CE" },
              { key: "Extremely Severe Cyclonic Storm (47-61 m/s)", label: "Extremely Severe", abbrev: "ESCS", color: "#EF4444" },
              { key: "Very Severe Cyclonic Storm (33-46 m/s)", label: "Very Severe", abbrev: "VSCS", color: "#F97316" },
              { key: "Severe Cyclonic Storm (25-32 m/s)", label: "Severe Cyclonic", abbrev: "SCS", color: "#FBBF24" },
              { key: "Cyclonic Storm (17-24 m/s)", label: "Cyclonic Storm", abbrev: "CS", color: "#34D399" },
              { key: "Depression / Deep Depression (<17 m/s)", label: "Depression", abbrev: "D/DD", color: "#60A5FA" },
            ].map((row) => {
              const count = Number(data.intensity_distribution[row.key] ?? 0);
              const total = metrics.total_historical_events || 1;
              const pct = Math.round((count / total) * 100);

              return (
                <div key={row.key} className="space-y-1">
                  <div className="flex items-center justify-between text-[10.5px]">
                    <div className="flex items-center gap-1.5 min-w-0 pr-2">
                      <span
                        className="w-2.5 h-2.5 rounded-full shrink-0"
                        style={{ backgroundColor: row.color }}
                      />
                      <span className="font-semibold text-neutral-800 truncate" title={row.key}>
                        {row.label}
                      </span>
                      <span className="text-[9px] font-mono text-neutral-400 shrink-0">
                        ({row.abbrev})
                      </span>
                    </div>
                    <span className="font-bold text-neutral-900 shrink-0">
                      {count} <span className="text-[9.5px] font-normal text-neutral-500">({pct}%)</span>
                    </span>
                  </div>

                  <div className="h-2 w-full bg-neutral-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{
                        width: `${Math.max(pct, count > 0 ? 4 : 0)}%`,
                        backgroundColor: row.color,
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Multi-Height Terrain Vertical Wind Profile */}
      <div className="p-3.5 rounded-lg border border-neutral-200 bg-white space-y-2">
        <div className="flex items-center justify-between text-xs font-semibold text-neutral-800">
          <span className="flex items-center gap-1">
            Multi-Height Wind Speed Profile
            <HelpTooltip text={TOOLTIPS.verticalProfile} />
          </span>
          <span className="text-[10px] font-normal text-neutral-400">Global Wind Atlas 250m</span>
        </div>
        <div className="grid grid-cols-5 gap-1.5 text-center">
          {Object.entries(data.terrain_wind_profile).map(([height, speed]) => (
            <div key={height} className="p-2 rounded bg-neutral-50 border border-neutral-100">
              <div className="text-[9.5px] text-neutral-500 font-medium">{height}</div>
              <div className="text-xs font-bold text-neutral-900">{speed.toFixed(1)} m/s</div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Structural Safety & Mitigation Recommendations Panel (Asynchronous) */}
      <div className="p-3.5 rounded-xl border border-neutral-300 bg-neutral-900 text-white space-y-3">
        <div className="flex items-center justify-between border-b border-neutral-800 pb-2">
          <span className="text-xs font-bold tracking-wide flex items-center gap-1.5 text-sky-400">
            <ShieldAlert size={15} />
            AI Structural Safety & Mitigation Report
          </span>
          <span className="text-[9px] font-mono uppercase bg-neutral-800 text-sky-300 px-2 py-0.5 rounded border border-neutral-700">
            IS 875 / NBC 2016
          </span>
        </div>

        {reportLoading && (
          <div className="py-6 space-y-3 animate-pulse">
            <div className="h-4 bg-neutral-800 rounded w-3/4" />
            <div className="h-3 bg-neutral-800 rounded w-1/2" />
            <div className="space-y-2 pt-2">
              <div className="h-12 bg-neutral-800 rounded-lg" />
              <div className="h-12 bg-neutral-800 rounded-lg" />
            </div>
            <div className="text-[10px] text-center text-neutral-400 italic pt-2">
              Synthesizing structural resilience recommendations...
            </div>
          </div>
        )}

        {reportError && (
          <div className="p-2.5 rounded-lg bg-rose-950/40 border border-rose-800 text-rose-300 text-xs">
            {reportError}
          </div>
        )}

        {!reportLoading && report && (
          <div className="space-y-3">
            {/* Design Speed Uplift Warning Banner */}
            {report.is_design_speed_elevated && (
              <div className="p-2.5 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-200 text-[11px] leading-relaxed">
                <div className="font-bold text-amber-400 flex items-center gap-1 mb-0.5">
                  <AlertTriangle size={13} />
                  Engineering Advisory: Elevated Wind Baseline
                </div>
                {report.elevation_reason}
              </div>
            )}

            {/* Recommended Design Speed Metric */}
            <div className="p-2.5 rounded-lg bg-neutral-800/80 border border-neutral-700 flex items-center justify-between">
              <div>
                <div className="text-[10px] text-neutral-400 font-medium">
                  Recommended Engineering Baseline (Vb)
                </div>
                <div className="text-lg font-bold text-sky-300">
                  {report.recommended_design_wind_speed_ms.toFixed(1)} m/s
                </div>
              </div>
              <div className="text-right">
                <div className="text-[10px] text-neutral-400 font-medium">Statutory Minimum</div>
                <div className="text-sm font-semibold text-neutral-300">
                  {report.statutory_wind_speed_ms.toFixed(1)} m/s
                </div>
              </div>
            </div>

            {/* Prioritized Mitigation Cards */}
            <div className="space-y-2 pt-1">
              <div className="text-[11px] font-semibold text-neutral-300">
                Prioritized Structural Mitigations
              </div>
              {report.prioritized_mitigations.map((item, idx) => {
                const isOpen = Boolean(openMitigations[idx]);
                const badgeColor =
                  item.priority === "CRITICAL"
                    ? "bg-rose-500/20 text-rose-300 border-rose-500/40"
                    : item.priority === "HIGH"
                    ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                    : "bg-sky-500/20 text-sky-300 border-sky-500/40";

                return (
                  <div
                    key={idx}
                    className="rounded-lg border border-neutral-800 bg-neutral-950/60 overflow-hidden"
                  >
                    <button
                      type="button"
                      onClick={() => toggleMitigation(idx)}
                      className="w-full p-2.5 text-left flex items-center justify-between text-xs hover:bg-neutral-800/50 transition-colors"
                    >
                      <div className="flex items-center gap-2 pr-2 min-w-0">
                        <span
                          className={`text-[9px] font-bold px-1.5 py-0.5 rounded border shrink-0 ${badgeColor}`}
                        >
                          [{item.priority}]
                        </span>
                        <span className="font-semibold text-neutral-200 truncate">
                          {item.category}
                        </span>
                      </div>
                      {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>
                    {isOpen && (
                      <div className="p-2.5 pt-0 text-[11px] text-neutral-300 space-y-1 border-t border-neutral-800/50 mt-1">
                        <div className="text-[10px] font-mono text-neutral-400">
                          Ref: {item.standard_reference}
                        </div>
                        <div className="leading-relaxed text-neutral-200">
                          {item.recommendation_text}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Operational Early Warning Checklist */}
            <div className="space-y-1.5 pt-2 border-t border-neutral-800">
              <div className="text-[11px] font-semibold text-neutral-300">
                Operational Early-Warning Checklist
              </div>
              <ul className="space-y-1">
                {report.early_warning_checklist.map((check, i) => (
                  <li key={i} className="flex items-start gap-1.5 text-[10px] text-neutral-300">
                    <CheckCircle2 size={12} className="text-emerald-400 shrink-0 mt-0.5" />
                    <span>{check}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default WindCyclonePanel;
