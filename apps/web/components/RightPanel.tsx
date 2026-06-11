'use client'

import { useMapStore } from '@/store'
import { MetricsPanel } from './MetricsPanel'
import { ComparisonTable } from './ComparisonTable'
import { ClimatePanel } from './analysis/ClimatePanel'
import { SunPathPanel } from './analysis/SunPathPanel'
import { FloodPanel } from './analysis/FloodPanel'
import { WindPanel } from './analysis/WindPanel'
import { RainfallPanel } from './analysis/RainfallPanel'
import type { AnalysisTab } from '@/types'

const TABS: { id: AnalysisTab; label: string; icon: string }[] = [
  { id: 'metrics', label: 'Metrics', icon: '📊' },
  { id: 'climate', label: 'Climate', icon: '🌡' },
  { id: 'sun', label: 'Sun', icon: '☀️' },
  { id: 'flood', label: 'Flood', icon: '🌊' },
  { id: 'wind', label: 'Wind', icon: '💨' },
  { id: 'rainfall', label: 'Rain', icon: '🌧' },
]

export function RightPanel() {
  const { rightPanelOpen, setRightPanelOpen, activeTab, setActiveTab, areas, satResults } = useMapStore()

  if (!rightPanelOpen) {
    return (
      <button
        onClick={() => setRightPanelOpen(true)}
        className="absolute top-1/2 right-2 -translate-y-1/2 z-10 bg-zinc-900 border border-zinc-700 rounded p-1 text-zinc-400 hover:text-white"
      >
        ‹
      </button>
    )
  }

  return (
    <div className="w-72 bg-zinc-900 border-l border-zinc-800 flex flex-col h-full overflow-hidden">
      {/* Tab bar */}
      <div className="flex items-center border-b border-zinc-800 overflow-x-auto shrink-0">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex flex-col items-center px-2.5 py-2 text-xs shrink-0 border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-blue-500 text-white'
                : 'border-transparent text-zinc-500 hover:text-zinc-300'
            }`}
          >
            <span>{tab.icon}</span>
            <span>{tab.label}</span>
          </button>
        ))}
        <div className="flex-1" />
        <button onClick={() => setRightPanelOpen(false)} className="p-2 text-zinc-600 hover:text-white shrink-0">›</button>
      </div>

      {/* Loading bar */}
      {satResults.loading && (
        <div className="h-0.5 bg-zinc-800">
          <div className="h-full bg-blue-500 animate-pulse" style={{ width: '60%' }} />
        </div>
      )}

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'metrics' && (
          <div>
            <MetricsPanel />
            {areas.length > 0 && <ComparisonTable />}
          </div>
        )}
        {activeTab === 'climate' && <ClimatePanel />}
        {activeTab === 'sun' && <SunPathPanel />}
        {activeTab === 'flood' && <FloodPanel />}
        {activeTab === 'wind' && <WindPanel />}
        {activeTab === 'rainfall' && <RainfallPanel />}
      </div>
    </div>
  )
}
