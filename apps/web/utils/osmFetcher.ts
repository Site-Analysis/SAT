import type { LayerConfig } from '@/types'

const OVERPASS_ENDPOINTS = [
  'https://overpass-api.de/api/interpreter',
  'https://overpass.kumi.systems/api/interpreter',
  'https://maps.mail.ru/osm/tools/overpass/api/interpreter',
]

const MAX_CONCURRENT = 3
const QUERY_TIMEOUT = 90_000
const cache = new Map<string, GeoJSON.FeatureCollection>()

function buildOverpassQuery(layer: LayerConfig, bbox: string): string {
  const [south, west, north, east] = bbox.split(',')
  const bboxStr = `${south},${west},${north},${east}`
  const queries = layer.osmQuery.split('|').map(q => {
    const [k, v] = q.includes('=') ? q.split('=') : [q, '*']
    const val = v === '*' ? '' : `="${v}"`
    const geomTypes = layer.geometryType === 'point'
      ? [`node["${k}"${val}](${bboxStr});`]
      : layer.geometryType === 'line'
        ? [`way["${k}"${val}](${bboxStr});`]
        : [`way["${k}"${val}](${bboxStr});`, `relation["${k}"${val}](${bboxStr});`]
    return geomTypes.join('')
  })
  return `[out:json][timeout:90];(${queries.join('')});out body geom;`
}

function convertToGeoJSON(data: OverpassResponse, layer: LayerConfig): GeoJSON.FeatureCollection {
  const features: GeoJSON.Feature[] = []

  for (const el of data.elements) {
    try {
      if (el.type === 'node' && el.lat !== undefined && el.lon !== undefined) {
        features.push({
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [el.lon, el.lat] },
          properties: { ...el.tags, _osm_id: el.id, _layer: layer.id },
        })
      } else if (el.type === 'way' && el.geometry) {
        const coords = el.geometry.map((p: { lat: number; lon: number }) => [p.lon, p.lat])
        const isClosed = coords.length > 2 && coords[0][0] === coords[coords.length - 1][0] && coords[0][1] === coords[coords.length - 1][1]
        if (layer.geometryType === 'polygon' && isClosed) {
          features.push({
            type: 'Feature',
            geometry: { type: 'Polygon', coordinates: [coords] },
            properties: { ...el.tags, _osm_id: el.id, _layer: layer.id },
          })
        } else {
          features.push({
            type: 'Feature',
            geometry: { type: 'LineString', coordinates: coords },
            properties: { ...el.tags, _osm_id: el.id, _layer: layer.id },
          })
        }
      } else if (el.type === 'relation' && el.members) {
        const outerWays = el.members.filter((m: OverpassMember) => m.role === 'outer' && m.geometry)
        if (outerWays.length > 0) {
          const rings = outerWays.map((m: OverpassMember) =>
            m.geometry!.map((p: { lat: number; lon: number }) => [p.lon, p.lat])
          )
          features.push({
            type: 'Feature',
            geometry: { type: 'MultiPolygon', coordinates: rings.map(r => [r]) },
            properties: { ...el.tags, _osm_id: el.id, _layer: layer.id },
          })
        }
      }
    } catch {}
  }

  return { type: 'FeatureCollection', features }
}

export function getBboxFromPolygon(coords: number[][], bufferDeg = 0.001): string {
  const lons = coords.map(c => c[0])
  const lats = coords.map(c => c[1])
  const minLon = Math.min(...lons) - bufferDeg
  const minLat = Math.min(...lats) - bufferDeg
  const maxLon = Math.max(...lons) + bufferDeg
  const maxLat = Math.max(...lats) + bufferDeg
  return `${minLat},${minLon},${maxLat},${maxLon}`
}

export async function fetchLayerData(
  layer: LayerConfig,
  bbox: string,
  maxRetries = 3,
  signal?: AbortSignal
): Promise<GeoJSON.FeatureCollection> {
  const cacheKey = `${bbox}:${layer.id}`
  if (cache.has(cacheKey)) return cache.get(cacheKey)!

  const query = buildOverpassQuery(layer, bbox)
  let endpointIndex = 0

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    const endpoint = OVERPASS_ENDPOINTS[endpointIndex % OVERPASS_ENDPOINTS.length]
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), QUERY_TIMEOUT)
      const mergedSignal = signal
        ? (AbortSignal as unknown as { any: (signals: AbortSignal[]) => AbortSignal }).any([signal, controller.signal])
        : controller.signal

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded', 'User-Agent': 'SAT-Platform/1.0' },
        body: `data=${encodeURIComponent(query)}`,
        signal: mergedSignal,
      })
      clearTimeout(timeoutId)

      if (res.status === 429 || res.status >= 500) {
        endpointIndex++
        await new Promise(r => setTimeout(r, Math.min(1000 * 2 ** attempt, 8000)))
        continue
      }

      const data: OverpassResponse = await res.json()
      const fc = convertToGeoJSON(data, layer)
      cache.set(cacheKey, fc)
      return fc
    } catch (err) {
      if (signal?.aborted) return { type: 'FeatureCollection', features: [] }
      endpointIndex++
      if (attempt < maxRetries - 1) {
        await new Promise(r => setTimeout(r, Math.min(1000 * 2 ** attempt, 8000)))
      }
    }
  }

  return { type: 'FeatureCollection', features: [] }
}

export async function fetchMultipleLayers(
  layers: LayerConfig[],
  bbox: string,
  onProgress?: (done: number, total: number) => void,
  signal?: AbortSignal
): Promise<Map<string, GeoJSON.FeatureCollection>> {
  const result = new Map<string, GeoJSON.FeatureCollection>()
  let done = 0

  for (let i = 0; i < layers.length; i += MAX_CONCURRENT) {
    if (signal?.aborted) break
    const batch = layers.slice(i, i + MAX_CONCURRENT)
    const results = await Promise.all(batch.map(l => fetchLayerData(l, bbox, 3, signal)))
    batch.forEach((l, j) => { result.set(l.id, results[j]); done++ })
    onProgress?.(done, layers.length)
  }

  return result
}

export function clearCache() {
  cache.clear()
}

// Overpass API response types (internal)
interface OverpassMember {
  role: string
  geometry?: Array<{ lat: number; lon: number }>
}

interface OverpassElement {
  type: 'node' | 'way' | 'relation'
  id: number
  lat?: number
  lon?: number
  tags?: Record<string, string>
  geometry?: Array<{ lat: number; lon: number }>
  members?: OverpassMember[]
}

interface OverpassResponse {
  elements: OverpassElement[]
}
