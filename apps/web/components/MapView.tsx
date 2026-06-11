'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import MapGL, { MapRef } from 'react-map-gl/maplibre'
import DeckGL from '@deck.gl/react'
import { GeoJsonLayer, ScatterplotLayer, LineLayer, PolygonLayer } from '@deck.gl/layers'
import type { MapViewState } from '@deck.gl/core'
import 'maplibre-gl/dist/maplibre-gl.css'
import { useMapStore } from '@/store'
import { LAYER_MANIFEST } from '@/data/layerManifest'
import { fetchMultipleLayers, getBboxFromPolygon, clearCache } from '@/utils/osmFetcher'
import { usePolygonDrawing } from '@/hooks/usePolygonDrawing'
import { useSatAnalysis } from '@/hooks/useSatAnalysis'

const MAP_STYLES: Record<string, string> = {
  dark: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
  light: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
  satellite: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
}

export function MapView() {
  const mapRef = useRef<MapRef>(null)
  const {
    viewState, setViewState,
    mapStyle,
    layerVisibility, layerOrder,
    selectionPolygon, setSelectionPolygon,
    globalOpacity, styleOverrides, isolatedLayerId,
    layerData, setLayerData,
    addArea, areas,
    setRightPanelOpen,
  } = useMapStore()

  const { isDrawing, drawingPoints, addPoint, completeDrawing, onPointerDown, onPointerMove, wasClick } = usePolygonDrawing()
  const { runAnalysis } = useSatAnalysis()
  const [loadingLayers, setLoadingLayers] = useState(false)
  const [loadProgress, setLoadProgress] = useState(0)
  const abortRef = useRef<AbortController | null>(null)

  // Fetch OSM layers when polygon is set
  useEffect(() => {
    if (!selectionPolygon) return

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

      // Trigger SAT backend analysis
      runAnalysis(selectionPolygon)
      setRightPanelOpen(true)
    }).catch(() => setLoadingLayers(false))
  }, [selectionPolygon])

  const handleMapClick = useCallback((e: { coordinate: number[] }) => {
    if (!wasClick()) return
    if (!isDrawing) return
    addPoint(e.coordinate[0], e.coordinate[1])
  }, [isDrawing, addPoint, wasClick])

  const handleMapDblClick = useCallback(() => {
    if (isDrawing && drawingPoints.length >= 3) {
      completeDrawing()
    }
  }, [isDrawing, drawingPoints, completeDrawing])

  // Build deck.gl layers
  const deckLayers = (() => {
    const layers = []

    // Selection polygon outline
    if (selectionPolygon) {
      layers.push(new PolygonLayer({
        id: 'selection-fill',
        data: [selectionPolygon.geometry.coordinates],
        getPolygon: d => d,
        filled: true,
        getFillColor: [59, 130, 246, 30],
        stroked: true,
        getLineColor: [59, 130, 246, 200],
        lineWidthMinPixels: 2,
      }))
    }

    // In-progress drawing
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

    // OSM data layers — render in order
    const activeIsolate = isolatedLayerId
    for (const layerId of [...layerOrder].reverse()) {
      const layerConfig = LAYER_MANIFEST.find(l => l.id === layerId)
      if (!layerConfig) continue
      if (activeIsolate && activeIsolate !== layerId) continue
      const visible = layerVisibility[layerId] !== false
      if (!visible) continue

      const fc = layerData.get(layerId)
      if (!fc || fc.features.length === 0) continue

      const opacity = (styleOverrides[layerId]?.opacity ?? globalOpacity)
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
  })()

  const saveArea = useCallback(() => {
    if (!selectionPolygon) return
    const name = `Area ${areas.length + 1}`
    addArea({
      id: `area-${Date.now()}`,
      name,
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
        viewState={viewState as MapViewState}
        controller={{ doubleClickZoom: false }}
        onViewStateChange={({ viewState: vs }) => setViewState(vs as typeof viewState)}
        layers={deckLayers}
        onClick={handleMapClick as never}
        style={{ position: 'absolute', inset: '0' }}
      >
        <MapGL
          ref={mapRef}
          mapStyle={MAP_STYLES[mapStyle]}
          style={{ width: '100%', height: '100%' }}
        />
      </DeckGL>

      {/* Loading indicator */}
      {loadingLayers && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-zinc-900/90 border border-zinc-700 rounded-full px-4 py-1.5 flex items-center gap-2 text-xs text-zinc-300">
          <div className="w-3 h-3 border border-blue-400 border-t-transparent rounded-full animate-spin" />
          Loading layers… {Math.round(loadProgress * 100)}%
        </div>
      )}

      {/* Save area button */}
      {selectionPolygon && !loadingLayers && (
        <button
          onClick={saveArea}
          className="absolute bottom-4 right-4 bg-zinc-800 hover:bg-zinc-700 border border-zinc-600 text-white text-xs px-3 py-1.5 rounded-full shadow"
        >
          + Save Area
        </button>
      )}
    </div>
  )
}
