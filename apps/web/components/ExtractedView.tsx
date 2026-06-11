'use client'

import DeckGL from '@deck.gl/react'
import { OrbitView } from '@deck.gl/core'
import { GeoJsonLayer, ScatterplotLayer } from '@deck.gl/layers'
import { useState } from 'react'
import { useMapStore } from '@/store'
import { LAYER_MANIFEST, LAYER_GROUPS } from '@/data/layerManifest'

const GROUP_ORDER = ['environment', 'landUse', 'infrastructure', 'access', 'traffic', 'amenities']
const BASE_LAYER_HEIGHT = 200
const GROUP_GAP = 800

export function ExtractedView() {
  const {
    layerOrder, layerVisibility, layerData, globalOpacity, styleOverrides, isolatedLayerId,
    explodedGroupRatio, explodedIntraGroupRatio,
  } = useMapStore()

  const [orbitState, setOrbitState] = useState({
    target: [0, 0, 0] as [number, number, number],
    zoom: 1,
    rotationX: 45,
    rotationOrbit: -30,
  })

  // Calculate z-offset per layer based on group + intra-group position
  function getLayerZ(layerId: string): number {
    const layerConfig = LAYER_MANIFEST.find(l => l.id === layerId)
    if (!layerConfig) return 0
    const groupIndex = GROUP_ORDER.indexOf(layerConfig.group)
    const layersInGroup = LAYER_MANIFEST.filter(l => l.group === layerConfig.group)
    const intraIndex = layersInGroup.findIndex(l => l.id === layerId)
    return (
      groupIndex * GROUP_GAP * explodedGroupRatio +
      intraIndex * BASE_LAYER_HEIGHT * explodedIntraGroupRatio
    )
  }

  const deckLayers = []
  const activeIsolate = isolatedLayerId

  for (const layerId of [...layerOrder].reverse()) {
    const layerConfig = LAYER_MANIFEST.find(l => l.id === layerId)
    if (!layerConfig) continue
    if (activeIsolate && activeIsolate !== layerId) continue
    const visible = layerVisibility[layerId] !== false
    if (!visible) continue

    const fc = layerData.get(layerId)
    if (!fc || fc.features.length === 0) continue

    const z = getLayerZ(layerId)
    const opacity = styleOverrides[layerId]?.opacity ?? globalOpacity
    const [r, g, b] = layerConfig.color

    // Normalize coordinates to center around 0,0 for orbit view
    const normalizedData = {
      ...fc,
      features: fc.features.map(f => ({
        ...f,
        geometry: normalizeGeometry(f.geometry, z),
      })),
    }

    deckLayers.push(new GeoJsonLayer({
      id: `3d-${layerId}`,
      data: normalizedData,
      filled: true,
      stroked: true,
      getFillColor: [r, g, b, Math.round(opacity * 160)],
      getLineColor: [r, g, b, Math.round(opacity * 255)],
      getLineWidth: layerConfig.strokeWidth,
      lineWidthMinPixels: 1,
      extruded: layerConfig.extrusionHeight > 0,
      getElevation: layerConfig.extrusionHeight,
      pickable: true,
      material: { ambient: 0.2, diffuse: 0.8, shininess: 32, specularColor: [60, 64, 70] },
    }))
  }

  return (
    <div className="flex-1 relative bg-zinc-950">
      <DeckGL
        views={new OrbitView({ id: 'orbit' })}
        viewState={orbitState}
        controller
        onViewStateChange={({ viewState: vs }) => setOrbitState(vs as typeof orbitState)}
        layers={deckLayers}
        style={{ position: 'absolute', inset: '0' }}
      />

      {/* Legend */}
      <div className="absolute top-2 right-2 bg-zinc-900/80 border border-zinc-700 rounded-lg p-2 text-xs space-y-1">
        {GROUP_ORDER.map(group => {
          const info = LAYER_GROUPS[group as keyof typeof LAYER_GROUPS]
          const hasData = LAYER_MANIFEST.filter(l => l.group === group).some(l => (layerData.get(l.id)?.features.length ?? 0) > 0)
          if (!hasData) return null
          return (
            <div key={group} className="flex items-center gap-1.5 text-zinc-300">
              <span className="w-2 h-2 rounded-sm" style={{ background: info.color }} />
              {info.label}
            </div>
          )
        })}
      </div>

      <div className="absolute bottom-2 left-1/2 -translate-x-1/2 text-xs text-zinc-600">
        Drag to rotate · Scroll to zoom · Shift+drag to pan
      </div>
    </div>
  )
}

// Normalize geo coordinates to orbit-friendly meters-ish scale
function normalizeGeometry(geom: GeoJSON.Geometry, zOffset: number): GeoJSON.Geometry {
  const scale = 111320
  const transformCoord = (c: number[]) => [
    (c[0] - 77.5946) * scale * Math.cos(12.9716 * Math.PI / 180),
    (c[1] - 12.9716) * scale,
    (c[2] ?? 0) + zOffset,
  ]

  switch (geom.type) {
    case 'Point':
      return { ...geom, coordinates: transformCoord(geom.coordinates) }
    case 'LineString':
      return { ...geom, coordinates: geom.coordinates.map(transformCoord) }
    case 'Polygon':
      return { ...geom, coordinates: geom.coordinates.map(ring => ring.map(transformCoord)) }
    case 'MultiPolygon':
      return { ...geom, coordinates: geom.coordinates.map(poly => poly.map(ring => ring.map(transformCoord))) }
    default:
      return geom
  }
}
