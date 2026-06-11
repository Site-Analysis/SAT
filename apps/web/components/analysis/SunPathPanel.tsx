'use client'

import { useEffect, useState } from 'react'
import { useMapStore } from '@/store'
import { fetchSunPathSvg } from '@/utils/satApi'

export function SunPathPanel() {
  const { satResults, selectionPolygon, viewState } = useMapStore()
  const { sunPath, solarEvents, sunOrientation, loading } = satResults
  const [svgContent, setSvgContent] = useState<string>('')

  // Centroid
  const coords = selectionPolygon?.geometry.coordinates[0]
  const lat = coords ? coords.reduce((s, c) => s + c[1], 0) / coords.length : viewState.latitude
  const lon = coords ? coords.reduce((s, c) => s + c[0], 0) / coords.length : viewState.longitude

  useEffect(() => {
    fetchSunPathSvg(lat, lon)
      .then(setSvgContent)
      .catch(() => setSvgContent(''))
  }, [lat, lon])

  if (loading) return <div className="p-4 text-zinc-400 text-sm animate-pulse">Loading sun path…</div>

  return (
    <div className="p-3 space-y-3">
      <div className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Sun Path Analysis</div>

      {svgContent && (
        <div
          className="rounded bg-zinc-800 p-1 overflow-hidden"
          dangerouslySetInnerHTML={{ __html: svgContent }}
          style={{ maxHeight: 200 }}
        />
      )}

      {solarEvents && (
        <div className="grid grid-cols-3 gap-2 text-center">
          {[
            { label: 'Sunrise', value: solarEvents.sunrise, icon: '🌅' },
            { label: 'Solar Noon', value: solarEvents.solar_noon, icon: '☀️' },
            { label: 'Sunset', value: solarEvents.sunset, icon: '🌇' },
          ].map(({ label, value, icon }) => (
            <div key={label} className="bg-zinc-800 rounded p-2">
              <div className="text-base">{icon}</div>
              <div className="text-xs text-zinc-300 font-medium">{value?.slice(11, 16) ?? '—'}</div>
              <div className="text-xs text-zinc-500">{label}</div>
            </div>
          ))}
        </div>
      )}

      {sunOrientation && (
        <div className="bg-zinc-800 rounded p-2 space-y-1">
          <div className="text-xs text-zinc-400">
            <span className="text-zinc-300 font-medium">Orientation:</span> {sunOrientation.recommended_orientation}
          </div>
          <div className="text-xs text-zinc-400">
            <span className="text-zinc-300 font-medium">Shading:</span> {sunOrientation.shading_strategy}
          </div>
          {sunOrientation.notes && (
            <div className="text-xs text-zinc-500">{sunOrientation.notes}</div>
          )}
        </div>
      )}

      {!solarEvents && !sunOrientation && (
        <div className="text-zinc-500 text-sm">Draw a polygon to load sun path data.</div>
      )}
    </div>
  )
}
