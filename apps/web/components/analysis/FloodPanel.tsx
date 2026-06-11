'use client'

import { useMapStore } from '@/store'

const RISK_COLORS: Record<string, string> = {
  'Very Low': '#22c55e',
  'Low': '#84cc16',
  'Moderate': '#eab308',
  'High': '#f97316',
  'Very High': '#ef4444',
}

const RISK_BG: Record<string, string> = {
  'Very Low': 'bg-green-900/30 border-green-700',
  'Low': 'bg-lime-900/30 border-lime-700',
  'Moderate': 'bg-yellow-900/30 border-yellow-700',
  'High': 'bg-orange-900/30 border-orange-700',
  'Very High': 'bg-red-900/30 border-red-700',
}

export function FloodPanel() {
  const { satResults } = useMapStore()
  const { flood, loading } = satResults

  if (loading) return <div className="p-4 text-zinc-400 text-sm animate-pulse">Loading flood analysis…</div>
  if (!flood) return <div className="p-4 text-zinc-500 text-sm">Draw a polygon to load flood risk data.</div>

  const color = RISK_COLORS[flood.risk_category] ?? '#94a3b8'
  const bg = RISK_BG[flood.risk_category] ?? 'bg-zinc-800 border-zinc-700'

  const components = [
    { label: 'Elevation Risk', value: flood.elevation_risk },
    { label: 'Hydrology Risk', value: flood.hydrology_risk },
    { label: 'Historical Risk', value: flood.historical_risk },
    { label: 'LLAI Risk', value: flood.llai_risk },
  ]

  return (
    <div className="p-3 space-y-3">
      <div className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Flood Risk Analysis</div>

      <div className={`rounded p-3 border ${bg} flex items-center gap-3`}>
        <div className="text-2xl font-bold" style={{ color }}>
          {flood.risk_category}
        </div>
        <div>
          <div className="text-xs text-zinc-400">Overall Score</div>
          <div className="text-lg font-semibold text-white">{(flood.overall_score * 100).toFixed(0)}%</div>
        </div>
      </div>

      <div className="space-y-1.5">
        {components.map(({ label, value }) => (
          <div key={label}>
            <div className="flex justify-between text-xs mb-0.5">
              <span className="text-zinc-400">{label}</span>
              <span className="text-zinc-300">{(value * 100).toFixed(0)}%</span>
            </div>
            <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{ width: `${value * 100}%`, background: color }}
              />
            </div>
          </div>
        ))}
      </div>

      {flood.notes && <div className="text-xs text-zinc-500">{flood.notes}</div>}
    </div>
  )
}
