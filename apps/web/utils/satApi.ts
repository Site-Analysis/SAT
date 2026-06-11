import type {
  ClimateArchiveResponse,
  ThermalGridResponse,
  SunPathResponse,
  SolarEventsResponse,
  SunOrientationResponse,
  FloodAnalysisResponse,
  WindAnalysisResponse,
  RainfallArchiveResponse,
} from '@/types'

const TEMP_URL = process.env.NEXT_PUBLIC_TEMP_API_URL ?? 'http://localhost:8000'
const SUNPATH_URL = process.env.NEXT_PUBLIC_SUNPATH_API_URL ?? 'http://localhost:8001'
const FLOOD_URL = process.env.NEXT_PUBLIC_FLOOD_API_URL ?? 'http://localhost:8002'
const WIND_URL = process.env.NEXT_PUBLIC_WIND_API_URL ?? 'http://localhost:8003'
const RAINFALL_URL = process.env.NEXT_PUBLIC_RAINFALL_API_URL ?? 'http://localhost:8004'

async function get<T>(url: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(url, { signal })
  if (!res.ok) throw new Error(`${res.status} ${url}`)
  return res.json()
}

async function post<T>(url: string, body: unknown, signal?: AbortSignal): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })
  if (!res.ok) throw new Error(`${res.status} ${url}`)
  return res.json()
}

export async function fetchClimateArchive(
  lat: number,
  lon: number,
  signal?: AbortSignal
): Promise<ClimateArchiveResponse> {
  const today = new Date()
  const startDate = `${today.getFullYear() - 1}-01-01`
  const endDate = `${today.getFullYear() - 1}-12-31`
  return get(
    `${TEMP_URL}/weather/climate-archive?latitude=${lat}&longitude=${lon}&start_date=${startDate}&end_date=${endDate}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto`,
    signal
  )
}

export async function fetchThermalGrid(
  polygon: GeoJSON.Polygon,
  signal?: AbortSignal
): Promise<ThermalGridResponse> {
  return post(`${TEMP_URL}/weather/thermal-grid`, polygon, signal)
}

export async function fetchSunPath(
  lat: number,
  lon: number,
  signal?: AbortSignal
): Promise<SunPathResponse> {
  return get(`${SUNPATH_URL}/sunpath/annual?lat=${lat}&lon=${lon}`, signal)
}

export async function fetchSunPathSvg(lat: number, lon: number): Promise<string> {
  const res = await fetch(`${SUNPATH_URL}/sunpath/diagram.svg?lat=${lat}&lon=${lon}`)
  if (!res.ok) throw new Error(`${res.status} sunpath svg`)
  return res.text()
}

export async function fetchSolarEvents(
  lat: number,
  lon: number,
  signal?: AbortSignal
): Promise<SolarEventsResponse> {
  return get(`${SUNPATH_URL}/sunpath/events?lat=${lat}&lon=${lon}`, signal)
}

export async function fetchSunOrientation(
  lat: number,
  lon: number,
  signal?: AbortSignal
): Promise<SunOrientationResponse> {
  return get(`${SUNPATH_URL}/sunpath/orientation?lat=${lat}&lon=${lon}`, signal)
}

export async function fetchFloodAnalysis(
  lat: number,
  lon: number,
  radiusM = 1000,
  signal?: AbortSignal
): Promise<FloodAnalysisResponse> {
  return post(`${FLOOD_URL}/flood/analyze`, { latitude: lat, longitude: lon, radius_meters: radiusM }, signal)
}

export async function fetchWindAnalysis(
  lat: number,
  lon: number,
  radiusM = 1000,
  signal?: AbortSignal
): Promise<WindAnalysisResponse> {
  return post(`${WIND_URL}/wind/analyze`, { latitude: lat, longitude: lon, radius_meters: radiusM }, signal)
}

export async function fetchRainfallArchive(
  lat: number,
  lon: number,
  signal?: AbortSignal
): Promise<RainfallArchiveResponse> {
  const today = new Date()
  const startDate = `${today.getFullYear() - 1}-01-01`
  const endDate = `${today.getFullYear() - 1}-12-31`
  return get(
    `${RAINFALL_URL}/rainfall/archive?latitude=${lat}&longitude=${lon}&start_date=${startDate}&end_date=${endDate}`,
    signal
  )
}
