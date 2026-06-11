'use client'

import { useState } from 'react'
import { useMapStore } from '@/store'
import { DraggableLayerList } from './DraggableLayerList'
import type { ViewState } from '@/types'

const CAMERA_PRESETS: Array<{ label: string; pitch: number; bearing: number; zoom?: number }> = [
  { label: 'Top', pitch: 0, bearing: 0 },
  { label: 'Axono', pitch: 45, bearing: -30 },
  { label: 'Horizon', pitch: 75, bearing: 0 },
  { label: 'Street', pitch: 85, bearing: 0 },
]

export function ControlPanel() {
  const {
    leftPanelOpen, setLeftPanelOpen,
    show3D, setShow3D,
    globalOpacity, setGlobalOpacity,
    explodedGroupRatio, setExplodedGroupRatio,
    explodedIntraGroupRatio, setExplodedIntraGroupRatio,
    viewState, setViewState,
  } = useMapStore()

  const [activeSection, setActiveSection] = useState<'layers' | '3d'>('layers')

  const applyPreset = (preset: typeof CAMERA_PRESETS[0]) => {
    setViewState({ ...viewState, pitch: preset.pitch, bearing: preset.bearing } as ViewState)
  }

  if (!leftPanelOpen) {
    return (
      <button
        onClick={() => setLeftPanelOpen(true)}
        className="absolute top-1/2 left-2 -translate-y-1/2 z-10 bg-zinc-900 border border-zinc-700 rounded p-1 text-zinc-400 hover:text-white"
      >
        ›
      </button>
    )
  }

  return (
    <div className="w-64 bg-zinc-900 border-r border-zinc-800 flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-zinc-800">
        <div className="flex gap-1">
          <button
            onClick={() => setActiveSection('layers')}
            className={`px-2.5 py-1 text-xs rounded ${activeSection === 'layers' ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-white'}`}
          >
            Layers
          </button>
          <button
            onClick={() => setActiveSection('3d')}
            className={`px-2.5 py-1 text-xs rounded ${activeSection === '3d' ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-white'}`}
          >
            3D
          </button>
        </div>
        <button onClick={() => setLeftPanelOpen(false)} className="text-zinc-500 hover:text-white text-xs">‹</button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-2">
        {activeSection === 'layers' && (
          <div>
            <div className="flex items-center justify-between mb-2 px-1">
              <span className="text-xs text-zinc-500">Global opacity</span>
              <span className="text-xs text-zinc-400">{Math.round(globalOpacity * 100)}%</span>
            </div>
            <input
              type="range" min={0} max={1} step={0.05}
              value={globalOpacity}
              onChange={e => setGlobalOpacity(parseFloat(e.target.value))}
              className="w-full accent-blue-500 mb-3"
            />
            <DraggableLayerList />
          </div>
        )}

        {activeSection === '3d' && (
          <div className="space-y-4">
            <div>
              <div className="text-xs text-zinc-500 mb-1">Camera presets</div>
              <div className="grid grid-cols-2 gap-1">
                {CAMERA_PRESETS.map(p => (
                  <button
                    key={p.label}
                    onClick={() => applyPreset(p)}
                    className="px-2 py-1.5 text-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded border border-zinc-700"
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-zinc-500">Group spacing</span>
                <span className="text-zinc-400">{explodedGroupRatio.toFixed(1)}×</span>
              </div>
              <input
                type="range" min={0} max={5} step={0.1}
                value={explodedGroupRatio}
                onChange={e => setExplodedGroupRatio(parseFloat(e.target.value))}
                className="w-full accent-blue-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-zinc-500">Layer spacing</span>
                <span className="text-zinc-400">{explodedIntraGroupRatio.toFixed(1)}×</span>
              </div>
              <input
                type="range" min={0} max={2} step={0.05}
                value={explodedIntraGroupRatio}
                onChange={e => setExplodedIntraGroupRatio(parseFloat(e.target.value))}
                className="w-full accent-blue-500"
              />
            </div>

            <div className="flex items-center gap-2">
              <label className="flex items-center gap-2 cursor-pointer">
                <div
                  onClick={() => setShow3D(!show3D)}
                  className={`w-8 h-4 rounded-full transition-colors ${show3D ? 'bg-blue-600' : 'bg-zinc-700'} relative`}
                >
                  <span className={`absolute top-0.5 w-3 h-3 bg-white rounded-full transition-transform ${show3D ? 'left-4' : 'left-0.5'}`} />
                </div>
                <span className="text-xs text-zinc-400">3D Exploded View</span>
              </label>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
