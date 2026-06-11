import type { LayerConfig } from '@/types'

const OVERPASS_ENDPOINTS = [
  'https://overpass-api.de/api/interpreter',
  'https://overpass.kumi.systems/api/interpreter',
  'https://maps.mail.ru/osm/tools/overpass/api/interpreter',
]

const QUERY_TIMEOUT_MS = 120_000
const cache = new Map<string, Map<string, GeoJSON.FeatureCollection>>()
let endpointIndex = 0

// ── Bbox helpers ──────────────────────────────────────────────────────────────

export function getBboxFromPolygon(coords: number[][], bufferDeg = 0.001): string {
  const lons = coords.map(c => c[0])
  const lats = coords.map(c => c[1])
  return [
    Math.min(...lats) - bufferDeg,
    Math.min(...lons) - bufferDeg,
    Math.max(...lats) + bufferDeg,
    Math.max(...lons) + bufferDeg,
  ].join(',')
}

// ── Query builder ─────────────────────────────────────────────────────────────

function buildBatchQuery(layers: LayerConfig[], bbox: string): string {
  const parts: string[] = []

  for (const layer of layers) {
    for (const q of layer.osmQuery.split('|')) {
      const [k, v] = q.includes('=') ? q.split('=') : [q, null]
      const tag = v ? `["${k}"="${v}"]` : `["${k}"]`

      if (layer.geometryType === 'point') {
        parts.push(`node${tag}(${bbox});`)
      } else if (layer.geometryType === 'line') {
        parts.push(`way${tag}(${bbox});`)
      } else {
        parts.push(`way${tag}(${bbox});`)
        parts.push(`relation${tag}(${bbox});`)
      }
    }
  }

  return `[out:json][timeout:120][maxsize:536870912];(${parts.join('')});out body geom qt;`
}

// ── Tag → layer attribution ───────────────────────────────────────────────────

function attributeToLayer(tags: Record<string, string>, layers: LayerConfig[]): string | null {
  for (const layer of layers) {
    for (const q of layer.osmQuery.split('|')) {
      if (q.includes('=')) {
        const [k, v] = q.split('=')
        if (tags[k] === v) return layer.id
      } else {
        if (tags[q] !== undefined) return layer.id
      }
    }
  }
  return null
}

// ── GeoJSON conversion ────────────────────────────────────────────────────────

function convertToGeoJSON(
  elements: OverpassElement[],
  layers: LayerConfig[]
): Map<string, GeoJSON.FeatureCollection> {
  const result = new Map<string, GeoJSON.FeatureCollection>(
    layers.map(l => [l.id, { type: 'FeatureCollection', features: [] }])
  )

  for (const el of elements) {
    try {
      const tags = el.tags ?? {}
      const layerId = attributeToLayer(tags, layers)
      if (!layerId) continue

      const fc = result.get(layerId)
      if (!fc) continue

      let feature: GeoJSON.Feature | null = null

      if (el.type === 'node' && el.lat !== undefined && el.lon !== undefined) {
        feature = {
          type: 'Feature',
          geometry: { type: 'Point', coordinates: [el.lon, el.lat] },
          properties: { ...tags, _osm_id: el.id },
        }
      } else if (el.type === 'way' && el.geometry?.length) {
        const coords = el.geometry.map(p => [p.lon, p.lat])
        const layer = layers.find(l => l.id === layerId)!
        const isClosed = coords.length > 2 &&
          coords[0][0] === coords[coords.length - 1][0] &&
          coords[0][1] === coords[coords.length - 1][1]

        if (layer.geometryType === 'polygon' && isClosed) {
          feature = {
            type: 'Feature',
            geometry: { type: 'Polygon', coordinates: [coords] },
            properties: { ...tags, _osm_id: el.id },
          }
        } else {
          feature = {
            type: 'Feature',
            geometry: { type: 'LineString', coordinates: coords },
            properties: { ...tags, _osm_id: el.id },
          }
        }
      } else if (el.type === 'relation' && el.members) {
        const outerRings = el.members
          .filter(m => m.role === 'outer' && m.geometry?.length)
          .map(m => m.geometry!.map(p => [p.lon, p.lat]))
        if (outerRings.length) {
          feature = {
            type: 'Feature',
            geometry: { type: 'MultiPolygon', coordinates: outerRings.map(r => [r]) },
            properties: { ...tags, _osm_id: el.id },
          }
        }
      }

      if (feature) fc.features.push(feature)
    } catch {}
  }

  return result
}

// ── Core fetch ────────────────────────────────────────────────────────────────

async function fetchWithRetry(
  query: string,
  signal?: AbortSignal,
  maxRetries = 3
): Promise<OverpassResponse> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    const endpoint = OVERPASS_ENDPOINTS[endpointIndex % OVERPASS_ENDPOINTS.length]
    try {
      const ac = new AbortController()
      const tid = setTimeout(() => ac.abort(), QUERY_TIMEOUT_MS)
      const merged = (signal && typeof (AbortSignal as unknown as { any?: unknown }).any === 'function')
        ? (AbortSignal as unknown as { any: (s: AbortSignal[]) => AbortSignal }).any([signal, ac.signal])
        : ac.signal

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'User-Agent': 'SAT-Platform/1.0 (site-analysis)',
        },
        body: `data=${encodeURIComponent(query)}`,
        signal: merged,
      })
      clearTimeout(tid)

      if (res.status === 429 || res.status >= 500) {
        endpointIndex++
        await sleep(Math.min(2000 * 2 ** attempt, 10000))
        continue
      }
      return res.json()
    } catch (err) {
      if (signal?.aborted) throw err
      endpointIndex++
      if (attempt < maxRetries - 1) await sleep(Math.min(2000 * 2 ** attempt, 10000))
    }
  }
  throw new Error('Overpass fetch failed after retries')
}

// ── Public API ────────────────────────────────────────────────────────────────

/**
 * Fetch all visible layers in 1-2 batched Overpass requests instead of N
 * individual requests. Splits into polygon+line batch and point batch to keep
 * query size manageable.
 */
export async function fetchMultipleLayers(
  layers: LayerConfig[],
  bbox: string,
  onProgress?: (done: number, total: number) => void,
  signal?: AbortSignal
): Promise<Map<string, GeoJSON.FeatureCollection>> {
  const cacheKey = bbox
  const cached = cache.get(cacheKey)
  if (cached) {
    onProgress?.(layers.length, layers.length)
    return cached
  }

  // Split into two batches: geo (polygon+line) and points
  // Points often return fewer elements and can share the same request,
  // but separate batches avoids one slow query blocking the other.
  const geoLayers = layers.filter(l => l.geometryType !== 'point')
  const pointLayers = layers.filter(l => l.geometryType === 'point')

  onProgress?.(0, layers.length)

  const batches: LayerConfig[][] = []
  if (geoLayers.length) batches.push(geoLayers)
  if (pointLayers.length) batches.push(pointLayers)

  const allResults = new Map<string, GeoJSON.FeatureCollection>(
    layers.map(l => [l.id, { type: 'FeatureCollection', features: [] }])
  )

  let done = 0
  for (const batch of batches) {
    if (signal?.aborted) break
    try {
      const query = buildBatchQuery(batch, bbox)
      const data = await fetchWithRetry(query, signal)
      const batchResult = convertToGeoJSON(data.elements ?? [], batch)
      batchResult.forEach((fc, id) => allResults.set(id, fc))
      done += batch.length
      onProgress?.(done, layers.length)
    } catch (err) {
      if (signal?.aborted) break
      // Partial failure: leave those layers empty
      done += batch.length
      onProgress?.(done, layers.length)
    }
  }

  if (!signal?.aborted) cache.set(cacheKey, allResults)
  return allResults
}

/** Keep for single-layer fetches (e.g. custom layer toggle after initial load) */
export async function fetchLayerData(
  layer: LayerConfig,
  bbox: string,
  signal?: AbortSignal
): Promise<GeoJSON.FeatureCollection> {
  const result = await fetchMultipleLayers([layer], bbox, undefined, signal)
  return result.get(layer.id) ?? { type: 'FeatureCollection', features: [] }
}

export function clearCache() {
  cache.clear()
}

// ── Internal types ────────────────────────────────────────────────────────────

function sleep(ms: number) { return new Promise(r => setTimeout(r, ms)) }

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
