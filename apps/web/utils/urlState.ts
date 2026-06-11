import type { ViewState, MapStyle } from '@/types'

interface UrlState {
  lat: number
  lon: number
  zoom: number
  style: MapStyle
  layers: string[]
}

export function encodeUrlState(state: UrlState): string {
  const params = new URLSearchParams({
    lat: state.lat.toFixed(5),
    lon: state.lon.toFixed(5),
    z: state.zoom.toFixed(1),
    style: state.style,
    layers: state.layers.join(','),
  })
  return `#${params.toString()}`
}

export function decodeUrlState(): Partial<UrlState> | null {
  if (typeof window === 'undefined') return null
  const hash = window.location.hash.slice(1)
  if (!hash) return null
  try {
    const params = new URLSearchParams(hash)
    const lat = parseFloat(params.get('lat') ?? '')
    const lon = parseFloat(params.get('lon') ?? '')
    const zoom = parseFloat(params.get('z') ?? '')
    const style = (params.get('style') ?? 'dark') as MapStyle
    const layersStr = params.get('layers') ?? ''
    const layers = layersStr ? layersStr.split(',') : []
    if (isNaN(lat) || isNaN(lon) || isNaN(zoom)) return null
    return { lat, lon, zoom, style, layers }
  } catch {
    return null
  }
}

export function viewStateToUrlState(vs: ViewState, style: MapStyle, visibleLayers: string[]): UrlState {
  return { lat: vs.latitude, lon: vs.longitude, zoom: vs.zoom, style, layers: visibleLayers }
}
