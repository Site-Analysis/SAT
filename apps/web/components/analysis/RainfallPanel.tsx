'use client'

import { useMapStore } from '@/store'

export function RainfallPanel() {
  const { satResults } = useMapStore()
  const { rainfall, loading } = satResults

  if (loading) return <div className="p-4 text-zinc-400 text-sm animate-pulse">Loading rainfall data…</div>
  if (!rainfall || !rainfall.monthly) return <div className="p-4 text-zinc-500 text-sm">Draw a polygon to load rainfall data.</div>

  const maxMm = Math.max(...rainfall.monthly.map(m => m.total_mm), 1)

  return (
    <div className="p-3 space-y-3">
      <div className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Rainfall Archive</div>

      <div className="space-y-1.5">
        {rainfall.monthly.map(m => (
          <div key={m.month} className="flex items-center gap-2 text-xs">
            <span className="w-8 text-zinc-500 shrink-0">{m.month}</span>
            <div className="flex-1 h-3 bg-zinc-800 rounded overflow-hidden">
              <div
                className="h-full rounded bg-blue-500 transition-all"
                style={{ width: `${(m.total_mm / maxMm) * 100}%` }}
              />
            </div>
            <span className="text-zinc-300 w-14 text-right">{m.total_mm.toFixed(1)} mm</span>
            <span className="text-zinc-500 w-12 text-right">{m.rainy_days}d</span>
          </div>
        ))}
      </div>

      <div className="text-xs text-zinc-600">Source: Open-Meteo / GEE ERA5-Land</div>
    </div>
  )
}
