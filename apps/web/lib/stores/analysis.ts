// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { create } from "zustand";

export type ModuleId = "flood" | "rainfall" | "sunpath" | "wind" | "windCyclone" | "temperature" | "zone" | "planning" | "zoning" | "infrastructure" | "soil" | "waterConstraints" | "growth" | "land" | "amenities";
export type Severity = "high" | "moderate" | "low" | "none";

export interface Indicator {
  label: string;
  value: string;
  unit: string;
  barFraction: number;
  citation: string;
}

export interface ChartDataPoint {
  label: string;
  value: number;
}

export interface ChartSeries {
  key: string;
  label: string;
  color: string;
}

// A self-describing chart. Single-series charts use one series with key "value";
// grouped/multi-line charts use several series, with each point carrying a value
// per series key.
export interface ModuleChart {
  title: string;
  kind: "bar" | "horizontal-bar" | "line" | "area" | "groupedBar" | "multiLine" | "dailyBar";
  unit?: string;
  series: ChartSeries[];
  points: Array<{ label: string } & Record<string, number | string>>;
}

export type QualitativeTone = "good" | "warn" | "bad" | "neutral";

export interface QualitativeStat {
  label: string;
  value: string;
  tone?: QualitativeTone;
}

export interface MetricGroup {
  group: string;
  rows: Array<{ label: string; value: string; unit?: string }>;
}

// Raw solar geometry for the sun-path diagram + shadow casting.
export interface SolarPoint { hour: number; az: number; el: number }
export interface SolarData {
  summer: SolarPoint[];
  equinox: SolarPoint[];
  winter: SolarPoint[];
  lat: number;
  lng: number;
}

// Raw wind climatology for the wind rose + seasonal toggle. Every field is
// measured by the wind service; the rose renders nothing without a distribution.
// Optional as a whole so a wind service still on the pre-2.0.0 contract (no
// `direction_distribution`, seasons as bare numbers) degrades instead of throwing.
export interface WindSeason {
  average_wind_speed: number;
  max_wind_speed: number;
  prevailing_direction: string;
  direction_distribution: Record<string, number>;
  gust_risk: string;
  recommended_orientation: string;
}
export type WindSeasonId = "annual" | "summer" | "monsoon" | "winter";
export interface WindData {
  average_wind_speed: number;
  direction_distribution: Record<string, number>;
  seasonal_analysis: Partial<Record<Exclude<WindSeasonId, "annual">, WindSeason>>;
}

// One nearby contextual item (feature / amenity / transit) used by the zoning
// site-context radar. `distanceM` is always present; `lat`/`lon` arrive in
// Phase 2 (backend coords) and stay optional until then.
export interface ZoningContextItem {
  label: string;
  category: string;            // "airport" | "metro" | feature type (e.g. "waterbody")
  distanceM: number;
  lat?: number;
  lon?: number;
}

// Authoritative administrative context from KGIS (flag-gated). `adminZone` is the
// BBMP administrative zone, NOT the RMP land-use zone.
export interface ZoningKgis {
  type: string | null;          // "Urban" | "Rural"
  district: string | null;
  town: string | null;
  adminZone: string | null;
  ward: string | null;
  taluk: string | null;
  hobli: string | null;
  village: string | null;
  surveyNumber: string | null;
}

// A located amenity for map markers (Amenities module → zoning overlay).
export interface AmenityPoint {
  name: string;
  type: string;
  category: string;            // "Healthcare" | "Education" | ...
  distanceM: number;
  lat: number;
  lon: number;
}

// Structured, raw zoning fields the floating HUD visuals consume directly —
// avoids re-parsing the formatted indicator/qualitative strings. Populated by
// getZoningAnalysis from the combined geo /zone + planning /analyze responses.
export interface ZoningData {
  // Site location (for provenance deep-links)
  siteLat: number;
  siteLon: number;
  // Land use & classification
  zoneClass: string;
  zoneIsBuildable: boolean;     // false for Green Belt/Water Body/Agricultural/etc.
  zoneCode: string | null;
  primaryLanduse: string;
  permittedUses: string[];
  lulcClass: string | null;
  lulcVintage: string | null;
  sourceConfidence: string;    // "authoritative" | "community"
  // Compliance flags
  naRequired: boolean;
  forestRequired: boolean;
  dgcaNocRequired: boolean;
  roadWidthSource: string;     // "user_input" | "osm_detected" | "default_9m"
  roadWidthM: number;
  // Development capacity
  farApplicable: number;
  baseFar: number | null;
  todApplicable: boolean;
  todFarMax: number;           // TOD ceiling, 4.0
  buildableAreaSqm: number;
  plotAreaSqm: number;
  groundCoverageMax: number;
  maxHeightM: number;
  heightLimitingFactor: string;
  olsHeightM: number | null;   // airport OLS height limit, if restrictive
  setbackFrontM: number | null;
  setbackRearM: number | null;
  setbackSideM: number | null;
  // Context (airport + metro + nearby features by distance)
  airportName: string;
  airportDistanceKm: number;
  airportSurface: string;
  airportLat: number | null;
  airportLon: number | null;
  metroName: string | null;
  metroDistanceM: number | null;
  metroLat: number | null;
  metroLon: number | null;
  context: ZoningContextItem[];
  // Authoritative admin context (KGIS, flag-gated; null otherwise)
  kgis: ZoningKgis | null;
  // Headline
  score: number;
  severity: Severity;
}

export interface WindCycloneTrackFeature {
  type: "Feature";
  geometry: { type: "LineString"; coordinates: [number, number][] };
  properties: {
    sid: string;
    name: string;
    season: number;
    max_wind_ms: number;
    max_wind_kmh: number;
    min_pressure_hpa: number;
    closest_distance_km: number;
    category: string;
    stroke: string;
    stroke_width: number;
  };
}

export interface WindCycloneMetrics {
  total_historical_events: number;
  annual_rate_50yr: number;
  max_recorded_wind_speed_ms: number;
  max_recorded_wind_speed_kmh: number;
  closest_recorded_distance_km: number;
}

export interface PrioritizedMitigationItem {
  priority: "CRITICAL" | "HIGH" | "ADVISORY";
  category: string;
  standard_reference: string;
  recommendation_text: string;
}

export interface SiteResilienceReportData {
  recommended_design_wind_speed_ms: number;
  statutory_wind_speed_ms: number;
  is_design_speed_elevated: boolean;
  elevation_reason: string;
  prioritized_mitigations: PrioritizedMitigationItem[];
  early_warning_checklist: string[];
}

export interface WindCycloneZoneFeature {
  type: "Feature";
  geometry: { type: "Polygon"; coordinates: [number, number][][] };
  properties: {
    zone_id: string;
    zone_speed?: number;
    v_b_ms: number;
    name: string;
    color: string;
    stroke: string;
  };
}

export interface WindCycloneEyePointFeature {
  type: "Feature";
  geometry: { type: "Point"; coordinates: [number, number] };
  properties: {
    sid: string;
    name: string;
    season: number;
    wind_ms: number;
    category: string;
    stroke: string;
    color: string;
    point_index: number;
  };
}

export interface WindCycloneData {
  is_within_india: boolean;
  statutory_v_b_ms: number;
  damage_risk_category: string;
  is_coastal_buffer: boolean;
  coastal_penalty_applied: boolean;
  terrain_wind_profile: Record<string, number>;
  metrics: WindCycloneMetrics;
  decadal_trend: Record<string, number>;
  intensity_distribution: Record<string, number>;
  tracks: { type: "FeatureCollection"; features: WindCycloneTrackFeature[] };
  wind_zones?: { type: "FeatureCollection"; features: WindCycloneZoneFeature[] };
  eye_points?: { type: "FeatureCollection"; features: WindCycloneEyePointFeature[] };
  recommendationsReport?: SiteResilienceReportData;
  recommendationsLoading?: boolean;
  recommendationsError?: string | null;
}

export interface ModuleResult {
  score: number;
  severity: Severity;
  summary: string;
  indicators: Indicator[];
  chart_data: ChartDataPoint[];
  charts?: ModuleChart[];
  qualitative?: QualitativeStat[];
  detailMetrics?: MetricGroup[];
  recommendations?: string[];
  data_source?: string;
  solar?: SolarData;
  wind?: WindData;
  windCyclone?: WindCycloneData;
  zoning?: ZoningData;
  amenityPoints?: AmenityPoint[];
  loading: boolean;
  error: string | null;
}

export interface SiteScore {
  overall_score: number;
  overall_severity: Severity;
  verdict_text: string;
  desc_text?: string;
  module_progress: { complete: number; total: number };
}

interface AnalysisState {
  modules: Partial<Record<ModuleId, ModuleResult>>;
  siteScore: SiteScore | null;
  setModuleResult: (id: ModuleId, result: ModuleResult) => void;
  setModuleLoading: (id: ModuleId) => void;
  setModuleError: (id: ModuleId, error: string) => void;
  setSiteScore: (score: SiteScore) => void;
  resetAnalysis: () => void;
}

export const useAnalysisStore = create<AnalysisState>((set) => ({
  modules: {},
  siteScore: null,
  setModuleResult: (id, result) =>
    set((s) => ({ modules: { ...s.modules, [id]: result } })),
  setModuleLoading: (id) =>
    set((s) => ({
      modules: {
        ...s.modules,
        [id]: { ...(s.modules[id] ?? {}), loading: true, error: null } as ModuleResult,
      },
    })),
  setModuleError: (id, error) =>
    set((s) => ({
      modules: {
        ...s.modules,
        [id]: { ...(s.modules[id] ?? {}), loading: false, error } as ModuleResult,
      },
    })),
  setSiteScore: (score) => set({ siteScore: score }),
  resetAnalysis: () => set({ modules: {}, siteScore: null }),
}));

export interface SelectedStormInfo {
  sid: string;
  name: string;
  season: number;
  category?: string;
  max_wind_ms: number | null;
  max_wind_kmh: number | null;
  min_pressure_hpa: number;
  closest_distance_km: number;
  has_animation?: boolean;
}

interface WindCycloneUIState {
  selectedStorm: SelectedStormInfo | null;
  activeStormSid: string | null;
  loadingSid: string | null;
  fetchError: string | null;
  windZoneMode: "buffer" | "regional" | "all";
  isDockedMinimized: boolean;
  animationAvailability: Record<string, boolean>;

  setSelectedStorm: (storm: SelectedStormInfo | null) => void;
  setActiveStormSid: (sid: string | null) => void;
  setLoadingSid: (sid: string | null) => void;
  setFetchError: (error: string | null) => void;
  setWindZoneMode: (mode: "buffer" | "regional" | "all") => void;
  setIsDockedMinimized: (minimized: boolean | ((prev: boolean) => boolean)) => void;
  toggleDockedMinimized: () => void;
  setAnimationAvailability: (sid: string, available: boolean) => void;
}

export const useWindCycloneUIStore = create<WindCycloneUIState>((set) => ({
  selectedStorm: null,
  activeStormSid: null,
  loadingSid: null,
  fetchError: null,
  windZoneMode: "buffer",
  isDockedMinimized: false,
  animationAvailability: {},

  setSelectedStorm: (storm) => set({ selectedStorm: storm, fetchError: null }),
  setActiveStormSid: (sid) => set({ activeStormSid: sid }),
  setLoadingSid: (sid) => set({ loadingSid: sid }),
  setFetchError: (error) => set({ fetchError: error }),
  setWindZoneMode: (mode) => set({ windZoneMode: mode }),
  setIsDockedMinimized: (minimized) =>
    set((s) => ({
      isDockedMinimized: typeof minimized === "function" ? minimized(s.isDockedMinimized) : minimized,
    })),
  toggleDockedMinimized: () => set((s) => ({ isDockedMinimized: !s.isDockedMinimized })),
  setAnimationAvailability: (sid, available) =>
    set((s) => ({
      animationAvailability: { ...s.animationAvailability, [sid]: available },
    })),
}));

