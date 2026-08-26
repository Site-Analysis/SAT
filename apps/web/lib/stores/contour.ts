// Copyright (c) 2026 Qnit. All rights reserved.
// SPDX-License-Identifier: LicenseRef-Proprietary

"use client";

import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";
import { ApiError, RequestCancelledError } from "../api/client";
import {
  CONTOUR_TIMEOUT_MS,
  DEFAULT_INTERVAL,
  HILLSHADE_OPACITY,
  LAYER_DEFAULTS,
  MAX_INTERVAL,
  MIN_INTERVAL,
} from "../contour/constants";
import { copy } from "../contour/copy";
import {
  clientMissingPolygonError,
  clientTransectShortError,
  mapContourError,
} from "../contour/errors";
import { transectLineGeoJSON } from "../contour/geometry";
import type {
  ContourErrorView,
  ContourLayerId,
  ContourResponse,
  ContourRunStatus,
  GeoJSONLike,
  ServiceStatus,
  TransectResponse,
  TransectStatus,
} from "../contour/types";
import { useDrawStore } from "./draw";

const INITIAL_LAYERS: Record<ContourLayerId, boolean> = { ...LAYER_DEFAULTS };

interface ContourState {
  interval: number;
  intervalError: string | null;
  resultInterval: number | null;
  serviceStatus: ServiceStatus;
  runStatus: ContourRunStatus;
  runStartedAt: number | null;
  abortController: AbortController | null;
  cancelRun: () => void;
  result: ContourResponse | null;
  error: ContourErrorView | null;
  cancelledNotice: boolean;
  resultNonce: number;
  layers: Record<ContourLayerId, boolean>;
  hillshadeOpacity: number;
  transectStatus: TransectStatus;
  transectDraft: [number, number][];
  transectSubmitted: [number, number][];
  transectResult: TransectResponse | null;
  transectError: ContourErrorView | null;
  transectStartedAt: number | null;
  activeProfileIndex: number | null;
  setInterval: (v: number) => void;
  toggleLayer: (id: ContourLayerId) => void;
  setLayers: (next: Partial<Record<ContourLayerId, boolean>>) => void;
  runAnalysis: (polygon: GeoJSONLike) => Promise<void>;
  canDrawTransect: () => boolean;
  startTransect: () => void;
  addTransectPoint: (pt: [number, number]) => void;
  undoTransectPoint: () => void;
  finishTransectDrawing: () => void;
  clearTransect: () => void;
  runTransect: (polygon: GeoJSONLike) => Promise<void>;
  setActiveProfileIndex: (i: number | null) => void;
  resetForProject: () => void;
}

function serviceFromError(err: unknown): ServiceStatus | null {
  if (err instanceof RequestCancelledError) return null;
  if (err instanceof ApiError) {
    if (err.status === 403) return "flag-disabled";
    if (err.status === 503) return "degraded";
    return null;
  }
  return "unreachable";
}

function errorViewFrom(err: unknown): ContourErrorView {
  if (err instanceof ApiError) return mapContourError(err.status, err.message);
  if (err instanceof Error) return mapContourError(null, err.message);
  return mapContourError(null);
}

export const useContourStore = create<ContourState>()(
  subscribeWithSelector((set, get) => ({
    interval: DEFAULT_INTERVAL,
    intervalError: null,
    resultInterval: null,
    serviceStatus: "unknown",
    runStatus: "idle",
    runStartedAt: null,
    abortController: null,
    result: null,
    error: null,
    cancelledNotice: false,
    resultNonce: 0,
    layers: { ...INITIAL_LAYERS },
    hillshadeOpacity: HILLSHADE_OPACITY,
    transectStatus: "idle",
    transectDraft: [],
    transectSubmitted: [],
    transectResult: null,
    transectError: null,
    transectStartedAt: null,
    activeProfileIndex: null,

    setInterval: (v) => {
      if (!Number.isFinite(v) || v < MIN_INTERVAL || v > MAX_INTERVAL) {
        set({ interval: v, intervalError: copy.interval.invalid });
        return;
      }
      set({ interval: Math.round(v), intervalError: null });
    },

    toggleLayer: (id) =>
      set((s) => ({ layers: { ...s.layers, [id]: !s.layers[id] } })),

    setLayers: (next) =>
      set((s) => ({ layers: { ...s.layers, ...next } })),

    cancelRun: () => {
      get().abortController?.abort();
      set({ abortController: null, runStatus: "cancelled", error: null, cancelledNotice: true });
    },

    runAnalysis: async (polygon) => {
      if (get().runStatus === "running") return;
      if (!polygon) {
        set({ error: clientMissingPolygonError(), runStatus: "failed" });
        return;
      }
      const { interval, intervalError } = get();
      if (intervalError || interval < MIN_INTERVAL || interval > MAX_INTERVAL) {
        set({ intervalError: copy.interval.invalid, error: mapContourError(422, "contour_interval") });
        return;
      }
      get().abortController?.abort();
      const controller = new AbortController();
      set({
        runStatus: "running",
        runStartedAt: Date.now(),
        abortController: controller,
        error: null,
        cancelledNotice: false,
      });
      try {
        const { getContourAnalysis } = await import("../api/analysis");
        const moduleResult = await getContourAnalysis(polygon, interval, controller.signal);
        const { useAnalysisStore } = await import("./analysis");
        useAnalysisStore.getState().setModuleResult("contour", moduleResult);
        const contour = moduleResult.contour ?? null;
        set((s) => ({
          result: contour,
          resultInterval: interval,
          runStatus: "succeeded",
          abortController: null,
          error: null,
          serviceStatus: "ready",
          resultNonce: s.resultNonce + 1,
          layers: { ...INITIAL_LAYERS },
        }));
      } catch (err) {
        if (err instanceof RequestCancelledError || get().runStatus === "cancelled") {
          set({ abortController: null, error: null, cancelledNotice: true, runStatus: get().result ? "succeeded" : "cancelled" });
          return;
        }
        const service = serviceFromError(err);
        set({
          runStatus: "failed",
          abortController: null,
          error: errorViewFrom(err),
          ...(service ? { serviceStatus: service } : {}),
        });
      }
    },

    canDrawTransect: () => get().runStatus === "succeeded" && !!get().result,

    startTransect: () => {
      if (!get().canDrawTransect()) return;
      useDrawStore.getState().setMode("transect");
      set({
        transectStatus: "drawing",
        transectDraft: [],
        transectResult: null,
        transectError: null,
        activeProfileIndex: null,
      });
    },

    addTransectPoint: (pt) => {
      if (!Number.isFinite(pt[0]) || !Number.isFinite(pt[1])) return;
      set((s) => ({ transectDraft: [...s.transectDraft, pt] }));
    },

    undoTransectPoint: () =>
      set((s) => ({ transectDraft: s.transectDraft.slice(0, -1) })),

    finishTransectDrawing: () => {
      const draft = get().transectDraft;
      if (draft.length < 2) {
        set({ transectError: clientTransectShortError() });
        return;
      }
      useDrawStore.getState().setMode(null);
      set({ transectStatus: "ready", transectSubmitted: draft });
    },

    clearTransect: () => {
      if (useDrawStore.getState().mode === "transect") {
        useDrawStore.getState().setMode(null);
      }
      set({
        transectStatus: "idle",
        transectDraft: [],
        transectSubmitted: [],
        transectResult: null,
        transectError: null,
        activeProfileIndex: null,
        transectStartedAt: null,
      });
    },

    runTransect: async (polygon) => {
      const line = get().transectDraft.length >= 2 ? get().transectDraft : get().transectSubmitted;
      if (line.length < 2) {
        set({ transectError: clientTransectShortError(), transectStatus: "failed" });
        return;
      }
      get().abortController?.abort();
      const controller = new AbortController();
      useDrawStore.getState().setMode(null);
      set({
        transectStatus: "running",
        transectStartedAt: Date.now(),
        transectSubmitted: line,
        abortController: controller,
        transectError: null,
        cancelledNotice: false,
        activeProfileIndex: null,
      });
      try {
        const { analyzeTransect } = await import("../api/analysis");
        const transectResult = await analyzeTransect(
          polygon,
          transectLineGeoJSON(line),
          controller.signal,
        );
        set({
          transectResult,
          transectStatus: "succeeded",
          abortController: null,
          serviceStatus: "ready",
        });
      } catch (err) {
        if (err instanceof RequestCancelledError || get().runStatus === "cancelled") {
          set({
            abortController: null,
            transectStatus: get().transectResult ? "succeeded" : "ready",
            cancelledNotice: true,
            error: null,
          });
          return;
        }
        const service = serviceFromError(err);
        set({
          transectStatus: "failed",
          abortController: null,
          transectError: errorViewFrom(err),
          ...(service ? { serviceStatus: service } : {}),
        });
      }
    },

    setActiveProfileIndex: (i) => set({ activeProfileIndex: i }),

    resetForProject: () => {
      get().abortController?.abort();
      if (useDrawStore.getState().mode === "transect") {
        useDrawStore.getState().setMode(null);
      }
      set({
        interval: DEFAULT_INTERVAL,
        intervalError: null,
        resultInterval: null,
        serviceStatus: "unknown",
        runStatus: "idle",
        runStartedAt: null,
        abortController: null,
        result: null,
        error: null,
        cancelledNotice: false,
        resultNonce: 0,
        layers: { ...INITIAL_LAYERS },
        hillshadeOpacity: HILLSHADE_OPACITY,
        transectStatus: "idle",
        transectDraft: [],
        transectSubmitted: [],
        transectResult: null,
        transectError: null,
        transectStartedAt: null,
        activeProfileIndex: null,
      });
    },
  })),
);

declare global {
  interface Window {
    useContourStore?: typeof useContourStore;
  }
}

if (process.env.NODE_ENV !== "production" && typeof window !== "undefined") {
  window.useContourStore = useContourStore;
}
