'use client'

import dynamic from 'next/dynamic'
import { useState, Suspense } from 'react'
import { SearchBar } from '@/components/SearchBar'
import { DrawingTool } from '@/components/DrawingTool'
import { ControlPanel } from '@/components/ControlPanel'
import { RightPanel } from '@/components/RightPanel'
import { ExportDialog } from '@/components/ExportDialog'
import { useMapStore } from '@/store'

// Prevent SSR for map/deck.gl components
const MapView = dynamic(() => import('@/components/MapView').then(m => ({ default: m.MapView })), { ssr: false })
const ExtractedView = dynamic(() => import('@/components/ExtractedView').then(m => ({ default: m.ExtractedView })), { ssr: false })

const MAP_STYLES = ['dark', 'light', 'satellite'] as const

export default function MapPage() {
  const { mapStyle, setMapStyle, show3D, setShow3D } = useMapStore()
  const [exportOpen, setExportOpen] = useState(false)

  return (
    <div className="flex flex-col h-screen bg-zinc-950 text-white overflow-hidden">
      {/* Top Bar */}
      <div className="flex items-center gap-3 px-3 py-1.5 bg-zinc-900 border-b border-zinc-800 shrink-0 flex-wrap">
        {/* Brand */}
        <div className="text-sm font-semibold text-white shrink-0">
          <span className="text-blue-400">SAT</span> Urban
        </div>

        <SearchBar />
        <DrawingTool />

        <div className="flex-1" />

        {/* Map style toggle */}
        <div className="flex gap-0.5">
          {MAP_STYLES.map(s => (
            <button
              key={s}
              onClick={() => setMapStyle(s)}
              className={`px-2 py-1 text-xs rounded capitalize ${mapStyle === s ? 'bg-zinc-600 text-white' : 'text-zinc-400 hover:text-white hover:bg-zinc-800'}`}
            >
              {s}
            </button>
          ))}
        </div>

        {/* 3D toggle */}
        <button
          onClick={() => setShow3D(!show3D)}
          className={`px-2.5 py-1 text-xs rounded border transition-colors ${show3D ? 'border-blue-500 bg-blue-900/30 text-blue-300' : 'border-zinc-700 text-zinc-400 hover:text-white'}`}
        >
          3D
        </button>

        {/* Export */}
        <button
          onClick={() => setExportOpen(true)}
          className="px-2.5 py-1 text-xs rounded border border-zinc-700 text-zinc-400 hover:text-white hover:border-zinc-500"
        >
          ↓ Export
        </button>
      </div>

      {/* Main area */}
      <div className="flex flex-1 overflow-hidden">
        <ControlPanel />

        <Suspense fallback={<div className="flex-1 bg-zinc-950 flex items-center justify-center text-zinc-600">Loading map…</div>}>
          {show3D ? <ExtractedView /> : <MapView />}
        </Suspense>

        <RightPanel />
      </div>

      {exportOpen && <ExportDialog onClose={() => setExportOpen(false)} />}
    </div>
  )
}
