'use client'

import { useMapStore } from '@/store'
import { calcBuildingDensity, calcGreenSpaceRatio, polygonAreaKm2 } from '@/utils/metrics'

export function ComparisonTable() {
  const { areas, removeArea, activeAreaId, setActiveAreaId } = useMapStore()

  if (areas.length === 0) {
    return (
      <div className="p-4 text-zinc-500 text-sm">
        Save multiple areas to compare them side by side.
      </div>
    )
  }

  return (
    <div className="p-3 space-y-2 overflow-x-auto">
      <div className="text-xs text-zinc-500 font-semibold uppercase tracking-wider mb-2">Area Comparison</div>
      <table className="w-full text-xs">
        <thead>
          <tr className="text-zinc-500">
            <th className="text-left pb-2">Area</th>
            <th className="text-right pb-2">km²</th>
            <th className="text-right pb-2">Bldgs/km²</th>
            <th className="text-right pb-2">Green %</th>
            <th className="pb-2" />
          </tr>
        </thead>
        <tbody>
          {areas.map(area => {
            const coords = area.polygon.geometry.coordinates[0]
            const areaKm2 = polygonAreaKm2(coords)
            const buildings = calcBuildingDensity(area.layerData, areaKm2)
            const green = calcGreenSpaceRatio(area.layerData, coords)
            const isActive = activeAreaId === area.id

            return (
              <tr
                key={area.id}
                onClick={() => setActiveAreaId(isActive ? null : area.id)}
                className={`cursor-pointer ${isActive ? 'text-white' : 'text-zinc-400 hover:text-zinc-200'}`}
              >
                <td className="py-1 font-medium truncate max-w-24">{area.name}</td>
                <td className="text-right py-1">{areaKm2.toFixed(2)}</td>
                <td className="text-right py-1">{buildings.toFixed(0)}</td>
                <td className="text-right py-1" style={{ color: green > 0.2 ? '#22c55e' : green > 0.1 ? '#eab308' : '#94a3b8' }}>
                  {(green * 100).toFixed(1)}%
                </td>
                <td className="py-1 pl-1">
                  <button
                    onClick={e => { e.stopPropagation(); removeArea(area.id) }}
                    className="text-zinc-600 hover:text-red-400"
                  >
                    ×
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
