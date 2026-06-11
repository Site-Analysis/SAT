import type { POIMetrics } from '@/types'
import type { LayerConfig } from '@/types'

// Area of a GeoJSON polygon in km²
export function polygonAreaKm2(coords: number[][]): number {
  if (coords.length < 3) return 0
  let area = 0
  const n = coords.length
  for (let i = 0; i < n - 1; i++) {
    const [x1, y1] = coords[i]
    const [x2, y2] = coords[i + 1]
    area += (x2 - x1) * (y2 + y1)
  }
  const deg2rad = Math.PI / 180
  const meanLat = coords.reduce((s, c) => s + c[1], 0) / coords.length
  const latScale = Math.cos(meanLat * deg2rad)
  const kmPerDeg = 111.32
  return Math.abs(area / 2) * kmPerDeg * kmPerDeg * latScale
}

export function calcPOIMetrics(
  layerDataMap: Map<string, GeoJSON.FeatureCollection>,
  visibleLayers: LayerConfig[],
  areaKm2: number
): POIMetrics {
  const pointLayers = visibleLayers.filter(l => l.group === 'amenities' && l.geometryType === 'point')
  const breakdown = pointLayers.map(l => {
    const fc = layerDataMap.get(l.id)
    return {
      id: l.id,
      name: l.name,
      count: fc?.features.length ?? 0,
      share: 0,
      color: `rgb(${l.color.join(',')})`,
    }
  })

  const total = breakdown.reduce((s, b) => s + b.count, 0)
  breakdown.forEach(b => { b.share = total > 0 ? b.count / total : 0 })

  // Shannon diversity index
  const diversityIndex = breakdown.reduce((h, b) => {
    if (b.share > 0) return h - b.share * Math.log(b.share)
    return h
  }, 0) / Math.log(Math.max(breakdown.length, 2))

  let diversityLabel = 'Low'
  if (diversityIndex > 0.7) diversityLabel = 'High'
  else if (diversityIndex > 0.4) diversityLabel = 'Moderate'

  return {
    totalCount: total,
    density: areaKm2 > 0 ? total / areaKm2 : 0,
    diversityIndex: Math.min(diversityIndex, 1),
    diversityLabel,
    areaKm2,
    timestamp: new Date(),
    categoryBreakdown: breakdown,
  }
}

export function calcBuildingDensity(
  layerData: Map<string, GeoJSON.FeatureCollection>,
  areaKm2: number
): number {
  const buildings = layerData.get('buildings')?.features.length ?? 0
  return areaKm2 > 0 ? buildings / areaKm2 : 0
}

export function calcGreenSpaceRatio(
  layerData: Map<string, GeoJSON.FeatureCollection>,
  polygonCoords: number[][]
): number {
  const totalArea = polygonAreaKm2(polygonCoords)
  if (totalArea === 0) return 0

  let greenArea = 0
  for (const id of ['park', 'vegetation', 'water']) {
    const fc = layerData.get(id)
    if (!fc) continue
    for (const f of fc.features) {
      if (f.geometry.type === 'Polygon') {
        greenArea += polygonAreaKm2((f.geometry as GeoJSON.Polygon).coordinates[0])
      }
    }
  }

  return Math.min(greenArea / totalArea, 1)
}
