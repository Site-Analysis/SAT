'use client'

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import MapGL, { MapRef } from 'react-map-gl/maplibre'
import DeckGL from '@deck.gl/react'
import { GeoJsonLayer, ScatterplotLayer, LineLayer, PolygonLayer } from '@deck.gl/layers'
import { FlyToInterpolator } from '@deck.gl/core'
import type { MapViewState } from '@deck.gl/core'
import 'maplibre-gl/dist/maplibre-gl.css'
import { useMapStore } from '@/store'
import { LAYER_MANIFEST } from '@/data/layerManifest'
import { fetchMultipleLayers, getBboxFromPolygon, clearCache } from '@/utils/osmFetcher'
import { usePolygonDrawing } from '@/hooks/usePolygonDrawing'
import { useSatAnalysis } from '@/hooks/useSatAnalysis'

function hexToRgb(hex: string): [number, number, number] {
  const n = parseInt(hex.replace('#', ''), 16)
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
}

const MAP_STYLES: Record<string, string> = {
  dark: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
  light: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
  satellite: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
}

const INITIAL_VIEW_STATE: MapViewState = {
  longitude: 77.5946,
  latitude: 12.9716,
  zoom: 13,
  pitch: 0,
  bearing: 0,
}

// Stable controller object — new object ref on every render causes controller reinit
const CONTROLLER = { doubleClickZoom: false }

export function MapView() {
  const mapRef = useRef<MapRef>(null)

  // Granular selectors — only re-render when these specific fields change
  const mapStyle    = useMapStore(s => s.mapStyle)
  const layerOrder  = useMapStore(s => s.layerOrder)
  const layerVisibility = useMapStore(s => s.layerVisibility)
  const selectionPolygon = useMapStore(s => s.selectionPolygon)
  const globalOpacity    = useMapStore(s => s.globalOpacity)
  const styleOverrides   = useMapStore(s => s.styleOverrides)
  const isolatedLayerId  = useMapStore(s => s.isolatedLayerId)
  const layerData  = useMapStore(s => s.layerData)
  const areas      = useMapStore(s => s.areas)
  const viewState  = useMapStore(s => s.viewState)

  const drawings         = useMapStore(s => s.drawings)
  const selectedDrawingId = useMapStore(s => s.selectedDrawingId)

  const setViewState     = useMapStore(s => s.setViewState)
  const setLayerData     = useMapStore(s => s.setLayerData)
  const addArea          = useMapStore(s => s.addArea)
  const setRightPanelOpen = useMapStore(s => s.setRightPanelOpen)

  const { isDrawing, drawingPoints, addPoint, completeDrawing, onPointerDown, onPointerMove, wasClick } = usePolygonDrawing()
  const { runAnalysis } = useSatAnalysis()

  // Local state — DeckGL always controlled from this, never snaps back
  const [localViewState, setLocalViewState] = useState<MapViewState>(
    viewState as MapViewState ?? INITIAL_VIEW_STATE
  )

  const [loadingLayers, setLoadingLayers] = useState(false)
  const [loadProgress, setLoadProgress]   = useState(0)

  const abortRef    = useRef<AbortController | null>(null)
  const persistTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)

  // One-shot fly command from SearchBar — apply transition to local state, then clear
  const flyTo    = useMapStore(s => s.flyTo)
  const setFlyTo = useMapStore(s => s.setFlyTo)
  useEffect(() => {
    if (!flyTo) return
    setLocalViewState({
      ...(flyTo as MapViewState),
      transitionDuration: 800,
      transitionInterpolator: new FlyToInterpolator({ speed: 1.5 }),
    })
    setFlyTo(null)
  }, [flyTo])

  // Fetch OSM layers + run SAT analysis when polygon changes
  useEffect(() => {
    if (!selectionPolygon) return

    // Open panel and start SAT analysis immediately — don't wait for Overpass
    setRightPanelOpen(true)
    runAnalysis(selectionPolygon)

    // OSM layer fetch is independent — updates layerData when it completes
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    clearCache()
    const coords = selectionPolygon.geometry.coordinates[0]
    const bbox = getBboxFromPolygon(coords)
    const visibleLayers = LAYER_MANIFEST.filter(l => layerVisibility[l.id] !== false)

    setLoadingLayers(true)
    setLoadProgress(0)

    fetchMultipleLayers(
      visibleLayers, bbox,
      (done, total) => setLoadProgress(done / total),
      controller.signal
    ).then(dataMap => {
      if (controller.signal.aborted) return
      dataMap.forEach((fc, id) => setLayerData(id, fc))
      setLoadingLayers(false)
    }).catch(() => setLoadingLayers(false))
  }, [selectionPolygon])

  // Click: add drawing point
  const handleMapClick = useCallback((e: { coordinate: number[] }) => {
    if (!wasClick() || !isDrawing) return
    addPoint(e.coordinate[0], e.coordinate[1])
  }, [isDrawing, addPoint, wasClick])

  // Double-click: complete polygon
  const handleMapDblClick = useCallback(() => {
    if (isDrawing && drawingPoints.length >= 3) completeDrawing()
  }, [isDrawing, drawingPoints, completeDrawing])

  // View state change: update local state immediately (no snap), debounce Zustand persist
  const handleViewStateChange = useCallback(
    ({ viewState: vs }: { viewState: unknown }) => {
      // Immediate — keeps DeckGL tracking user input at 60fps without Zustand re-renders
      setLocalViewState(vs as MapViewState)
      // Debounced — persist for restore-on-reload only, not navigation
      clearTimeout(persistTimer.current)
      persistTimer.current = setTimeout(() => {
        const { longitude, latitude, zoom, pitch = 0, bearing = 0 } = vs as MapViewState
        setViewState({ longitude, latitude, zoom, pitch, bearing })
      }, 1000)
    },
    [setViewState]
  )

  // Deck.gl layers — memoized so they don't rebuild on every frame
  const deckLayers = useMemo(() => {
    const layers = []

    // Render all saved drawings; highlight the selected one
    const visibleDrawings = drawings.filter(d => d.visible)
    if (visibleDrawings.length > 0) {
      layers.push(new PolygonLayer({
        id: 'drawings-fill',
        data: visibleDrawings,
        getPolygon: (d: { geometry: { coordinates: number[][][] } }) => d.geometry.coordinates,
        filled: true,
        getFillColor: (d: { id: string; style: { color: string; opacity: number } }) => {
          const [r, g, b] = hexToRgb(d.style.color)
          const alpha = d.id === selectedDrawingId ? 60 : 25
          return [r, g, b, alpha]
        },
        stroked: true,
        getLineColor: (d: { id: string; style: { color: string } }) => {
          const [r, g, b] = hexToRgb(d.style.color)
          const alpha = d.id === selectedDrawingId ? 255 : 160
          return [r, g, b, alpha]
        },
        lineWidthMinPixels: 2,
        updateTriggers: { getFillColor: selectedDrawingId, getLineColor: selectedDrawingId },
      }))
    }

    if (isDrawing && drawingPoints.length > 0) {
      layers.push(new ScatterplotLayer({
        id: 'drawing-points',
        data: drawingPoints,
        getPosition: d => d,
        getRadius: 4,
        getFillColor: [59, 130, 246, 255],
        radiusUnits: 'pixels',
      }))
      if (drawingPoints.length > 1) {
        layers.push(new LineLayer({
          id: 'drawing-lines',
          data: drawingPoints.slice(1).map((pt, i) => ({ from: drawingPoints[i], to: pt })),
          getSourcePosition: d => d.from,
          getTargetPosition: d => d.to,
          getColor: [59, 130, 246, 200],
          getWidth: 2,
          widthUnits: 'pixels',
        }))
      }
    }

    for (const layerId of [...layerOrder].reverse()) {
      const layerConfig = LAYER_MANIFEST.find(l => l.id === layerId)
      if (!layerConfig) continue
      if (isolatedLayerId && isolatedLayerId !== layerId) continue
      if (layerVisibility[layerId] === false) continue

      const fc = layerData.get(layerId)
      if (!fc || fc.features.length === 0) continue

      const opacity = styleOverrides[layerId]?.opacity ?? globalOpacity
      const [r, g, b] = layerConfig.color

      if (layerConfig.geometryType === 'point') {
        layers.push(new ScatterplotLayer({
          id: `layer-${layerId}`,
          data: fc.features.filter(f => f.geometry.type === 'Point'),
          getPosition: (f: GeoJSON.Feature) => (f.geometry as GeoJSON.Point).coordinates as [number, number],
          getRadius: layerConfig.strokeWidth * 2,
          getFillColor: [r, g, b, Math.round(opacity * 200)],
          radiusUnits: 'pixels',
          pickable: true,
        }))
      } else if (layerConfig.geometryType === 'line') {
        layers.push(new GeoJsonLayer({
          id: `layer-${layerId}`,
          data: fc,
          stroked: true,
          filled: false,
          getLineColor: [r, g, b, Math.round(opacity * 220)],
          getLineWidth: layerConfig.strokeWidth,
          lineWidthMinPixels: 1,
          pickable: true,
        }))
      } else {
        layers.push(new GeoJsonLayer({
          id: `layer-${layerId}`,
          data: fc,
          filled: true,
          stroked: true,
          getFillColor: [r, g, b, Math.round(opacity * 120)],
          getLineColor: [r, g, b, Math.round(opacity * 200)],
          getLineWidth: layerConfig.strokeWidth,
          lineWidthMinPixels: 1,
          extruded: layerConfig.extrusionHeight > 0,
          getElevation: layerConfig.extrusionHeight,
          pickable: true,
        }))
      }
    }

    return layers
  }, [drawings, selectedDrawingId, isDrawing, drawingPoints, layerOrder, layerVisibility, isolatedLayerId, layerData, styleOverrides, globalOpacity])

  const saveArea = useCallback(() => {
    if (!selectionPolygon) return
    addArea({
      id: `area-${Date.now()}`,
      name: `Area ${areas.length + 1}`,
      polygon: selectionPolygon,
      layerData: new globalThis.Map(layerData),
      bbox: [0, 0, 0, 0],
    })
  }, [selectionPolygon, areas, addArea, layerData])

  return (
    <div
      className="flex-1 relative"
      onPointerDown={onPointerDown}
      onPointerMove={onPointerMove}
      onDoubleClick={handleMapDblClick}
      style={{ cursor: isDrawing ? 'crosshair' : 'default' }}
    >
      <DeckGL
        viewState={localViewState}
        controller={CONTROLLER}
        layers={deckLayers}
        onViewStateChange={handleViewStateChange as never}
        onClick={handleMapClick as never}
        style={{ position: 'absolute', inset: '0' }}
      >
        <MapGL
          ref={mapRef}
          mapStyle={MAP_STYLES[mapStyle]}
          style={{ width: '100%', height: '100%' }}
        />
      </DeckGL>

      {loadingLayers && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-zinc-900/90 border border-zinc-700 rounded-full px-4 py-1.5 flex items-center gap-2 text-xs text-zinc-300">
          <div className="w-3 h-3 border border-blue-400 border-t-transparent rounded-full animate-spin" />
          Loading layers… {Math.round(loadProgress * 100)}%
        </div>
      )}

      {selectionPolygon && !loadingLayers && (
        <button
          onClick={saveArea}
          className="absolute bottom-4 right-4 bg-zinc-800 hover:bg-zinc-700 border border-zinc-600 text-white text-xs px-3 py-1.5 rounded-full shadow"
        >
          + Compare Area
        </button>
      )}
    </div>
  )
}
