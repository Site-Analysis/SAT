'use client'

import { useMapStore } from '@/store'

const COMFORT_COLORS: Record<string, string> = {
  'Excellent': '#22c55e',
  'Good': '#84cc16',
  'Fair': '#eab308',
  'Poor': '#ef4444',
}

const DIRECTIONS = ['N','NE','E','SE','S','SW','W','NW']

export function WindPanel() {
  const { satResults } = useMapStore()
  const { wind, loading } = satResults

  if (loading) return <div className="p-4 text-zinc-400 text-sm animate-pulse">Loading wind analysis…</div>
  if (!wind) return <div className="p-4 text-zinc-500 text-sm">Draw a polygon to load wind data.</div>

  const comfortColor = COMFORT_COLORS[wind.comfort_level] ?? '#94a3b8'
  const dirIndex = DIRECTIONS.indexOf(wind.dominant_orientation.replace('orth','').replace('ast','').replace('outh','').replace('est','').slice(0, 2).toUpperCase())
  const angleDeg = (DIRECTIONS.indexOf(wind.dominant_orientation.toUpperCase().slice(0, 2)) * 45) || 0

  return (
    <div className="p-3 space-y-3">
      <div className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Wind Analysis</div>

      <div className="grid grid-cols-2 gap-2">
        <div className="bg-zinc-800 rounded p-2 text-center">
          <div className="text-2xl" style={{ transform: `rotate(${angleDeg}deg)`, display: 'inline-block' }}>↑</div>
          <div className="text-xs text-zinc-300 font-medium">{wind.dominant_orientation}</div>
          <div className="text-xs text-zinc-500">Dominant Direction</div>
        </div>
        <div className="bg-zinc-800 rounded p-2 text-center">
          <div className="text-xl font-bold" style={{ color: comfortColor }}>{wind.comfort_level}</div>
          <div className="text-xs text-zinc-500">Comfort Level</div>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-zinc-800 rounded p-2">
          <div className="text-zinc-500">Avg Speed</div>
          <div className="text-white font-medium">{wind.avg_speed_ms?.toFixed(1) ?? '—'} m/s</div>
        </div>
        <div className="bg-zinc-800 rounded p-2">
          <div className="text-zinc-500">Load Risk</div>
          <div className="text-white font-medium">{wind.wind_load_risk ?? '—'}</div>
        </div>
      </div>

      {wind.notes && <div className="text-xs text-zinc-500">{wind.notes}</div>}
    </div>
  )
}
