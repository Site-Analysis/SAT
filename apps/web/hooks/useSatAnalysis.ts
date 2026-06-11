'use client'

import { useCallback, useRef } from 'react'
import { useMapStore } from '@/store'
import {
  fetchClimateArchive,
  fetchThermalGrid,
  fetchSunPath,
  fetchSolarEvents,
  fetchSunOrientation,
  fetchFloodAnalysis,
  fetchWindAnalysis,
  fetchRainfallArchive,
} from '@/utils/satApi'
import type { SelectionPolygon } from '@/types'

export function useSatAnalysis() {
  const { setSatResults } = useMapStore()
  const abortRef = useRef<AbortController | null>(null)

  const runAnalysis = useCallback(async (polygon: SelectionPolygon) => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    const signal = controller.signal

    // Centroid of polygon
    const coords = polygon.geometry.coordinates[0]
    const lat = coords.reduce((s, c) => s + c[1], 0) / coords.length
    const lon = coords.reduce((s, c) => s + c[0], 0) / coords.length

    setSatResults({ loading: true, error: null })

    const settled = await Promise.allSettled([
      fetchClimateArchive(lat, lon, signal),
      fetchThermalGrid(polygon.geometry, signal),
      fetchSunPath(lat, lon, signal),
      fetchSolarEvents(lat, lon, signal),
      fetchSunOrientation(lat, lon, signal),
      fetchFloodAnalysis(lat, lon, 1000, signal),
      fetchWindAnalysis(lat, lon, 1000, signal),
      fetchRainfallArchive(lat, lon, signal),
    ])

    if (signal.aborted) return

    const [climate, thermalGrid, sunPath, solarEvents, sunOrientation, flood, wind, rainfall] = settled

    setSatResults({
      loading: false,
      error: null,
      climate: climate.status === 'fulfilled' ? climate.value : null,
      thermalGrid: thermalGrid.status === 'fulfilled' ? thermalGrid.value : null,
      sunPath: sunPath.status === 'fulfilled' ? sunPath.value : null,
      solarEvents: solarEvents.status === 'fulfilled' ? solarEvents.value : null,
      sunOrientation: sunOrientation.status === 'fulfilled' ? sunOrientation.value : null,
      flood: flood.status === 'fulfilled' ? flood.value : null,
      wind: wind.status === 'fulfilled' ? wind.value : null,
      rainfall: rainfall.status === 'fulfilled' ? rainfall.value : null,
    })
  }, [setSatResults])

  const cancelAnalysis = useCallback(() => {
    abortRef.current?.abort()
    setSatResults({ loading: false })
  }, [setSatResults])

  return { runAnalysis, cancelAnalysis }
}
