'use client'

import { useMemo } from 'react'
import { useMapStore } from '@/store'
import { LAYER_MANIFEST } from '@/data/layerManifest'
import { calcPOIMetrics, calcBuildingDensity, calcGreenSpaceRatio, polygonAreaKm2 } from '@/utils/metrics'

export function MetricsPanel() {
  const { selectionPolygon, layerData, layerVisibility } = useMapStore()

  const metrics = useMemo(() => {
    if (!selectionPolygon) return null
    const coords = selectionPolygon.geometry.coordinates[0]
    const areaKm2 = polygonAreaKm2(coords)
    const visibleLayers = LAYER_MANIFEST.filter(l => layerVisibility[l.id] !== false)
    const poiMetrics = calcPOIMetrics(layerData, visibleLayers, areaKm2)
    const buildingDensity = calcBuildingDensity(layerData, areaKm2)
    const greenRatio = calcGreenSpaceRatio(layerData, coords)
    return { poiMetrics, buildingDensity, greenRatio, areaKm2 }
  }, [selectionPolygon, layerData, layerVisibility])

  if (!selectionPolygon) {
    return (
      <div className="p-4 text-zinc-500 text-sm">
        Draw a polygon on the map to analyze urban metrics.
      </div>
    )
  }

  if (!metrics) return null

  const { poiMetrics, buildingDensity, greenRatio, areaKm2 } = metrics

  return (
    <div className="p-3 space-y-3">
      <div className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Urban Metrics</div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 gap-2">
        <StatCard label="Area" value={`${areaKm2.toFixed(2)} km²`} />
        <StatCard label="POI Density" value={`${poiMetrics.density.toFixed(1)}/km²`} />
        <StatCard
          label="Buildings"
          value={`${buildingDensity.toFixed(0)}/km²`}
          sub={(layerData.get('buildings')?.features.length ?? 0).toString() + ' total'}
        />
        <StatCard
          label="Green Space"
          value={`${(greenRatio * 100).toFixed(1)}%`}
          color={greenRatio > 0.2 ? '#22c55e' : greenRatio > 0.1 ? '#eab308' : '#ef4444'}
        />
      </div>

      {/* POI diversity */}
      <div>
        <div className="flex justify-between text-xs mb-1">
          <span className="text-zinc-500">POI Diversity</span>
          <span className="text-zinc-300">{poiMetrics.diversityLabel} ({(poiMetrics.diversityIndex * 100).toFixed(0)}%)</span>
        </div>
        <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 transition-all"
            style={{ width: `${poiMetrics.diversityIndex * 100}%` }}
          />
        </div>
      </div>

      {/* Category breakdown */}
      {poiMetrics.categoryBreakdown.filter(c => c.count > 0).length > 0 && (
        <div className="space-y-1">
          <div className="text-xs text-zinc-500">POI Breakdown</div>
          {poiMetrics.categoryBreakdown
            .filter(c => c.count > 0)
            .sort((a, b) => b.count - a.count)
            .slice(0, 6)
            .map(cat => (
              <div key={cat.id} className="flex items-center gap-2 text-xs">
                <span className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ background: cat.color }} />
                <span className="flex-1 text-zinc-400 truncate">{cat.name}</span>
                <div className="w-16 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                  <div className="h-full rounded-full" style={{ width: `${cat.share * 100}%`, background: cat.color }} />
                </div>
                <span className="text-zinc-300 w-6 text-right">{cat.count}</span>
              </div>
            ))}
        </div>
      )}

      <div className="text-xs text-zinc-600">
        Updated {poiMetrics.timestamp.toLocaleTimeString()}
      </div>
    </div>
  )
}

function StatCard({ label, value, sub, color }: { label: string; value: string; sub?: string; color?: string }) {
  return (
    <div className="bg-zinc-800 rounded p-2">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="text-sm font-semibold text-white mt-0.5" style={color ? { color } : {}}>
        {value}
      </div>
      {sub && <div className="text-xs text-zinc-500">{sub}</div>}
    </div>
  )
}
