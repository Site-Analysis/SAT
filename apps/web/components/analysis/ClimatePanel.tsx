'use client'

import { useMapStore } from '@/store'

const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

export function ClimatePanel() {
  const { satResults } = useMapStore()
  const { climate, loading } = satResults

  if (loading) return <div className="p-4 text-zinc-400 text-sm animate-pulse">Loading climate data…</div>
  if (!climate) return <div className="p-4 text-zinc-500 text-sm">Draw a polygon to load climate data.</div>

  const temps = climate.daily?.temperature_2m_max ?? []
  const precips = climate.daily?.precipitation_sum ?? []

  // Aggregate by month
  const monthly = Array.from({ length: 12 }, (_, m) => ({
    month: m,
    maxTemp: [] as number[],
    minTemp: [] as number[],
    precip: [] as number[],
  }))

  climate.daily?.time.forEach((t, i) => {
    const m = new Date(t).getMonth()
    if (temps[i] != null) monthly[m].maxTemp.push(temps[i])
    if (climate.daily.temperature_2m_min?.[i] != null) monthly[m].minTemp.push(climate.daily.temperature_2m_min[i])
    if (precips[i] != null) monthly[m].precip.push(precips[i])
  })

  const avg = (arr: number[]) => arr.length ? arr.reduce((s, v) => s + v, 0) / arr.length : 0
  const sum = (arr: number[]) => arr.reduce((s, v) => s + v, 0)

  const rows = monthly.map(m => ({
    label: MONTHS[m.month],
    maxT: avg(m.maxTemp),
    minT: avg(m.minTemp),
    precip: sum(m.precip),
  }))

  const maxPrec = Math.max(...rows.map(r => r.precip), 1)
  const maxTemp = Math.max(...rows.map(r => r.maxT))
  const minTemp = Math.min(...rows.map(r => r.minT))

  return (
    <div className="p-3 space-y-3">
      <div className="text-xs text-zinc-500 font-semibold uppercase tracking-wider">Temperature & Rainfall</div>
      <div className="space-y-1">
        {rows.map(r => (
          <div key={r.label} className="flex items-center gap-2 text-xs">
            <span className="w-6 text-zinc-500">{r.label}</span>
            <div className="flex-1 flex items-center gap-1">
              <span className="text-blue-400 w-10 text-right">{r.minT.toFixed(0)}°</span>
              <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full"
                  style={{
                    marginLeft: `${((r.minT - minTemp) / (maxTemp - minTemp + 1)) * 50}%`,
                    width: `${((r.maxT - r.minT) / (maxTemp - minTemp + 1)) * 50}%`,
                    background: 'linear-gradient(to right, #3b82f6, #ef4444)',
                  }}
                />
              </div>
              <span className="text-red-400 w-10">{r.maxT.toFixed(0)}°C</span>
            </div>
            <div className="w-16 flex items-center gap-1">
              <div className="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-600 rounded-full"
                  style={{ width: `${(r.precip / maxPrec) * 100}%` }}
                />
              </div>
              <span className="text-zinc-400 w-8">{r.precip.toFixed(0)}mm</span>
            </div>
          </div>
        ))}
      </div>
      <div className="text-xs text-zinc-600">Source: Open-Meteo ERA5 reanalysis</div>
    </div>
  )
}
