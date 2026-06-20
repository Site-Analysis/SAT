"use client";

import { create } from "zustand";

export type RectBounds = [[number, number], [number, number]];
export type DrawMode = "rect" | "circle" | "poly" | null;

export interface DrawnBoundary {
  kind: "rect" | "poly";
  positions: [number, number][];
}

export interface SiteMeasurements {
  area: number;       // m²
  perimeter: number;  // m
  angles: number[];   // interior degrees at each vertex
}

interface DrawState {
  rectBounds: RectBounds | null;
  setRectBounds: (b: RectBounds | null) => void;
  mode: DrawMode;
  setMode: (m: DrawMode) => void;
  boundary: DrawnBoundary | null;
  setBoundary: (b: DrawnBoundary | null) => void;
  siteMeasurements: SiteMeasurements | null;
  setSiteMeasurements: (m: SiteMeasurements | null) => void;
  showDimensions: boolean;
  setShowDimensions: (v: boolean) => void;
}

export const useDrawStore = create<DrawState>((set) => ({
  rectBounds: null,
  setRectBounds: (b) => set({ rectBounds: b }),
  mode: null,
  setMode: (m) => set({ mode: m }),
  boundary: null,
  setBoundary: (b) => set({ boundary: b }),
  siteMeasurements: null,
  setSiteMeasurements: (m) => set({ siteMeasurements: m }),
  showDimensions: true,
  setShowDimensions: (v) => set({ showDimensions: v }),
}));
