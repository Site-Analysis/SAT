'use client'

import { useCallback, useRef } from 'react'
import { useMapStore } from '@/store'

const DRAG_THRESHOLD_PX = 5

export function usePolygonDrawing() {
  const {
    isDrawing, setIsDrawing,
    drawingMode,
    drawingPoints, setDrawingPoints,
    setSelectionPolygon,
  } = useMapStore()

  const pointerDownPos = useRef<[number, number] | null>(null)
  const isDragging = useRef(false)

  const startDrawing = useCallback(() => {
    setIsDrawing(true)
    setDrawingPoints([])
    setSelectionPolygon(null)
  }, [setIsDrawing, setDrawingPoints, setSelectionPolygon])

  const addPoint = useCallback((lng: number, lat: number) => {
    setDrawingPoints([...drawingPoints, [lng, lat]])
  }, [drawingPoints, setDrawingPoints])

  const completeDrawing = useCallback(() => {
    if (drawingPoints.length < 3) {
      cancelDrawing()
      return
    }
    const closed = [...drawingPoints, drawingPoints[0]]
    const area = calcPolygonArea(closed)
    setSelectionPolygon({
      id: `area-${Date.now()}`,
      geometry: { type: 'Polygon', coordinates: [closed] },
      area,
    })
    setIsDrawing(false)
    setDrawingPoints([])
  }, [drawingPoints, setSelectionPolygon, setIsDrawing, setDrawingPoints])

  const cancelDrawing = useCallback(() => {
    setIsDrawing(false)
    setDrawingPoints([])
  }, [setIsDrawing, setDrawingPoints])

  const undoLastPoint = useCallback(() => {
    if (drawingPoints.length > 0) {
      setDrawingPoints(drawingPoints.slice(0, -1))
    }
  }, [drawingPoints, setDrawingPoints])

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    pointerDownPos.current = [e.clientX, e.clientY]
    isDragging.current = false
  }, [])

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    if (!pointerDownPos.current) return
    const dx = e.clientX - pointerDownPos.current[0]
    const dy = e.clientY - pointerDownPos.current[1]
    if (Math.sqrt(dx * dx + dy * dy) > DRAG_THRESHOLD_PX) {
      isDragging.current = true
    }
  }, [])

  const wasClick = useCallback(() => !isDragging.current, [])

  return {
    isDrawing,
    drawingMode,
    drawingPoints,
    startDrawing,
    addPoint,
    completeDrawing,
    cancelDrawing,
    undoLastPoint,
    onPointerDown,
    onPointerMove,
    wasClick,
  }
}

function calcPolygonArea(coords: [number, number][]): number {
  let area = 0
  const n = coords.length
  for (let i = 0; i < n - 1; i++) {
    area += coords[i][0] * coords[i + 1][1]
    area -= coords[i + 1][0] * coords[i][1]
  }
  const meanLat = coords.reduce((s, c) => s + c[1], 0) / coords.length
  const latScale = Math.cos((meanLat * Math.PI) / 180)
  return Math.abs(area / 2) * 111320 * 111320 * latScale / 1e6
}
