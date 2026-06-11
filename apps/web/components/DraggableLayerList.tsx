'use client'

import { DndContext, closestCenter, DragEndEvent } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy, useSortable, arrayMove } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { useMapStore } from '@/store'
import { LAYER_MANIFEST, LAYER_GROUPS } from '@/data/layerManifest'
import type { LayerConfig } from '@/types'

function LayerRow({ layer }: { layer: LayerConfig }) {
  const { layerVisibility, toggleLayerVisibility, isolatedLayerId, setIsolatedLayerId, globalOpacity, setStyleOverride, styleOverrides } = useMapStore()
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id: layer.id })

  const visible = layerVisibility[layer.id] ?? layer.visible
  const isIsolated = isolatedLayerId === layer.id
  const opacity = styleOverrides[layer.id]?.opacity ?? globalOpacity

  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition, opacity: isDragging ? 0.5 : 1 }}
      className={`flex items-center gap-2 px-2 py-1.5 rounded text-xs ${isIsolated ? 'bg-zinc-600' : 'hover:bg-zinc-800'} group`}
    >
      <span {...attributes} {...listeners} className="cursor-grab text-zinc-600 hover:text-zinc-400 shrink-0">⋮⋮</span>
      <span
        className="w-2.5 h-2.5 rounded-sm shrink-0"
        style={{ background: `rgb(${layer.color.join(',')})` }}
      />
      <span
        className={`flex-1 truncate cursor-pointer ${visible ? 'text-zinc-200' : 'text-zinc-500 line-through'}`}
        onClick={() => toggleLayerVisibility(layer.id)}
      >
        {layer.name}
      </span>
      <button
        onClick={() => setIsolatedLayerId(isIsolated ? null : layer.id)}
        title={isIsolated ? 'Exit solo' : 'Solo'}
        className="opacity-0 group-hover:opacity-100 text-zinc-400 hover:text-yellow-400 px-0.5"
      >
        ◎
      </button>
      <input
        type="range" min={0} max={1} step={0.05}
        value={opacity}
        onChange={e => setStyleOverride(layer.id, { opacity: parseFloat(e.target.value) })}
        className="w-12 opacity-0 group-hover:opacity-100 accent-zinc-400"
      />
    </div>
  )
}

export function DraggableLayerList() {
  const { layerOrder, setLayerOrder } = useMapStore()

  const orderedLayers = layerOrder
    .map(id => LAYER_MANIFEST.find(l => l.id === id))
    .filter(Boolean) as LayerConfig[]

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (over && active.id !== over.id) {
      const oldIdx = layerOrder.indexOf(active.id as string)
      const newIdx = layerOrder.indexOf(over.id as string)
      setLayerOrder(arrayMove(layerOrder, oldIdx, newIdx))
    }
  }

  const groups = Object.keys(LAYER_GROUPS) as Array<keyof typeof LAYER_GROUPS>

  return (
    <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={layerOrder} strategy={verticalListSortingStrategy}>
        <div className="space-y-3">
          {groups.map(group => {
            const groupLayers = orderedLayers.filter(l => l.group === group)
            if (groupLayers.length === 0) return null
            const groupInfo = LAYER_GROUPS[group]
            return (
              <div key={group}>
                <div className="flex items-center gap-1.5 px-2 py-1 text-xs font-semibold text-zinc-500 uppercase tracking-wider">
                  <span className="w-1.5 h-1.5 rounded-full" style={{ background: groupInfo.color }} />
                  {groupInfo.label}
                </div>
                {groupLayers.map(layer => <LayerRow key={layer.id} layer={layer} />)}
              </div>
            )
          })}
        </div>
      </SortableContext>
    </DndContext>
  )
}
