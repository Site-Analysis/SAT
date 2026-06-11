'use client'

import { useMapStore } from '@/store'
import { usePolygonDrawing } from '@/hooks/usePolygonDrawing'
import type { DrawingMode } from '@/types'

const MODES: { mode: DrawingMode; label: string; icon: string }[] = [
  { mode: 'polygon', label: 'Polygon', icon: '⬡' },
  { mode: 'rectangle', label: 'Rectangle', icon: '▭' },
  { mode: 'circle', label: 'Circle', icon: '○' },
]

export function DrawingTool() {
  const { drawingMode, setDrawingMode } = useMapStore()
  const { isDrawing, startDrawing, completeDrawing, cancelDrawing, undoLastPoint, drawingPoints } = usePolygonDrawing()

  return (
    <div className="flex items-center gap-1">
      {!isDrawing ? (
        <>
          {MODES.map(({ mode, label, icon }) => (
            <button
              key={mode}
              onClick={() => { setDrawingMode(mode); startDrawing() }}
              title={label}
              className="px-2 py-1.5 text-sm bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded border border-zinc-700 transition-colors"
            >
              {icon}
            </button>
          ))}
        </>
      ) : (
        <>
          <span className="text-xs text-zinc-400 px-1">{drawingPoints.length} pts</span>
          <button
            onClick={undoLastPoint}
            title="Undo"
            className="px-2 py-1.5 text-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-300 rounded border border-zinc-700"
          >
            ↩
          </button>
          <button
            onClick={completeDrawing}
            title="Complete"
            disabled={drawingPoints.length < 3}
            className="px-2 py-1.5 text-xs bg-green-700 hover:bg-green-600 disabled:opacity-40 text-white rounded"
          >
            ✓ Done
          </button>
          <button
            onClick={cancelDrawing}
            title="Cancel"
            className="px-2 py-1.5 text-xs bg-red-900 hover:bg-red-800 text-white rounded"
          >
            ✕
          </button>
        </>
      )}
    </div>
  )
}
