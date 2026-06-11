'use client'

import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { LAYER_MANIFEST } from '@/data/layerManifest'
import type {
  MapStyle,
  DrawingMode,
  ViewState,
  ComparisonArea,
  SelectionPolygon,
  SatAnalysisResults,
  AnalysisTab,
} from '@/types'

export interface StyleOverride {
  opacity?: number
  extrusionMultiplier?: number
}

interface MapStore {
  // Map state
  viewState: ViewState
  setViewState: (vs: ViewState) => void
  mapStyle: MapStyle
  setMapStyle: (s: MapStyle) => void

  // Layer management
  layerOrder: string[]
  setLayerOrder: (order: string[]) => void
  layerVisibility: Record<string, boolean>
  toggleLayerVisibility: (id: string) => void
  isolatedLayerId: string | null
  setIsolatedLayerId: (id: string | null) => void
  globalOpacity: number
  setGlobalOpacity: (v: number) => void
  styleOverrides: Record<string, StyleOverride>
  setStyleOverride: (id: string, override: StyleOverride) => void

  // Drawing
  drawingMode: DrawingMode
  setDrawingMode: (m: DrawingMode) => void
  isDrawing: boolean
  setIsDrawing: (v: boolean) => void
  drawingPoints: [number, number][]
  setDrawingPoints: (pts: [number, number][]) => void

  // Selection & areas
  selectionPolygon: SelectionPolygon | null
  setSelectionPolygon: (p: SelectionPolygon | null) => void
  areas: ComparisonArea[]
  addArea: (area: ComparisonArea) => void
  removeArea: (id: string) => void
  activeAreaId: string | null
  setActiveAreaId: (id: string | null) => void
  layerData: Map<string, GeoJSON.FeatureCollection>
  setLayerData: (id: string, data: GeoJSON.FeatureCollection) => void

  // 3D view
  show3D: boolean
  setShow3D: (v: boolean) => void
  explodedGroupRatio: number
  setExplodedGroupRatio: (v: number) => void
  explodedIntraGroupRatio: number
  setExplodedIntraGroupRatio: (v: number) => void

  // Analysis panel
  activeTab: AnalysisTab
  setActiveTab: (t: AnalysisTab) => void
  satResults: SatAnalysisResults
  setSatResults: (r: Partial<SatAnalysisResults>) => void

  // UI
  rightPanelOpen: boolean
  setRightPanelOpen: (v: boolean) => void
  leftPanelOpen: boolean
  setLeftPanelOpen: (v: boolean) => void

  // Custom layers
  customLayers: Array<{ id: string; name: string; data: GeoJSON.FeatureCollection }>
  addCustomLayer: (layer: { id: string; name: string; data: GeoJSON.FeatureCollection }) => void
  removeCustomLayer: (id: string) => void

  // Favorites
  favoriteLocations: Array<{ name: string; lat: number; lon: number }>
  addFavoriteLocation: (loc: { name: string; lat: number; lon: number }) => void
}

const DEFAULT_SAT_RESULTS: SatAnalysisResults = {
  climate: null,
  thermalGrid: null,
  sunPath: null,
  solarEvents: null,
  sunOrientation: null,
  flood: null,
  wind: null,
  rainfall: null,
  loading: false,
  error: null,
}

export const useMapStore = create<MapStore>()(
  persist(
    (set, get) => ({
      viewState: { longitude: 77.5946, latitude: 12.9716, zoom: 13, pitch: 0, bearing: 0 },
      setViewState: (viewState) => set({ viewState }),
      mapStyle: 'dark',
      setMapStyle: (mapStyle) => set({ mapStyle }),

      layerOrder: LAYER_MANIFEST.map(l => l.id),
      setLayerOrder: (layerOrder) => set({ layerOrder }),
      layerVisibility: Object.fromEntries(LAYER_MANIFEST.map(l => [l.id, l.visible])),
      toggleLayerVisibility: (id) => set(s => ({
        layerVisibility: { ...s.layerVisibility, [id]: !s.layerVisibility[id] }
      })),
      isolatedLayerId: null,
      setIsolatedLayerId: (isolatedLayerId) => set({ isolatedLayerId }),
      globalOpacity: 0.8,
      setGlobalOpacity: (globalOpacity) => set({ globalOpacity }),
      styleOverrides: {},
      setStyleOverride: (id, override) => set(s => ({
        styleOverrides: { ...s.styleOverrides, [id]: { ...s.styleOverrides[id], ...override } }
      })),

      drawingMode: 'polygon',
      setDrawingMode: (drawingMode) => set({ drawingMode }),
      isDrawing: false,
      setIsDrawing: (isDrawing) => set({ isDrawing }),
      drawingPoints: [],
      setDrawingPoints: (drawingPoints) => set({ drawingPoints }),

      selectionPolygon: null,
      setSelectionPolygon: (selectionPolygon) => set({ selectionPolygon }),
      areas: [],
      addArea: (area) => set(s => ({ areas: [...s.areas, area] })),
      removeArea: (id) => set(s => ({ areas: s.areas.filter(a => a.id !== id) })),
      activeAreaId: null,
      setActiveAreaId: (activeAreaId) => set({ activeAreaId }),
      layerData: new Map(),
      setLayerData: (id, data) => set(s => {
        const next = new Map(s.layerData)
        next.set(id, data)
        return { layerData: next }
      }),

      show3D: false,
      setShow3D: (show3D) => set({ show3D }),
      explodedGroupRatio: 2.0,
      setExplodedGroupRatio: (explodedGroupRatio) => set({ explodedGroupRatio }),
      explodedIntraGroupRatio: 0.5,
      setExplodedIntraGroupRatio: (explodedIntraGroupRatio) => set({ explodedIntraGroupRatio }),

      activeTab: 'metrics',
      setActiveTab: (activeTab) => set({ activeTab }),
      satResults: DEFAULT_SAT_RESULTS,
      setSatResults: (r) => set(s => ({ satResults: { ...s.satResults, ...r } })),

      rightPanelOpen: true,
      setRightPanelOpen: (rightPanelOpen) => set({ rightPanelOpen }),
      leftPanelOpen: true,
      setLeftPanelOpen: (leftPanelOpen) => set({ leftPanelOpen }),

      customLayers: [],
      addCustomLayer: (layer) => set(s => ({ customLayers: [...s.customLayers, layer] })),
      removeCustomLayer: (id) => set(s => ({ customLayers: s.customLayers.filter(l => l.id !== id) })),

      favoriteLocations: [],
      addFavoriteLocation: (loc) => set(s => ({ favoriteLocations: [...s.favoriteLocations, loc] })),
    }),
    {
      name: 'sat-map-store',
      partialize: (s) => ({
        mapStyle: s.mapStyle,
        layerVisibility: s.layerVisibility,
        globalOpacity: s.globalOpacity,
        favoriteLocations: s.favoriteLocations,
        viewState: s.viewState,
      }),
    }
  )
)
