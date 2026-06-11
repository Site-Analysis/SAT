export type MapStyle = 'dark' | 'light' | 'satellite'
export type DrawingMode = 'polygon' | 'rectangle' | 'circle'
export type LayerGroup = 'environment' | 'landUse' | 'infrastructure' | 'access' | 'traffic' | 'amenities' | 'custom'

export interface LayerConfig {
  id: string
  name: string
  group: LayerGroup
  osmQuery: string
  geometryType: 'polygon' | 'line' | 'point'
  color: [number, number, number]
  strokeWidth: number
  extrusionHeight: number
  visible: boolean
  statisticsRecipes: ('count' | 'area' | 'density')[]
}

export interface SelectionPolygon {
  id: string
  geometry: GeoPolygon
  area: number
}

export interface Drawing {
  id: string
  name: string
  type: 'polygon'
  geometry: GeoPolygon
  area: number
  visible: boolean
  style: {
    color: string
    opacity: number
    lineWidth: number
  }
  createdAt: number
}

export interface GeoPolygon {
  type: 'Polygon'
  coordinates: number[][][]
}

export interface ComparisonArea {
  id: string
  name: string
  polygon: SelectionPolygon
  layerData: Map<string, GeoJSON.FeatureCollection>
  bbox: [number, number, number, number]
}

export interface POIMetrics {
  totalCount: number
  density: number
  diversityIndex: number
  diversityLabel: string
  areaKm2: number
  timestamp: Date
  categoryBreakdown: {
    id: string
    name: string
    count: number
    share: number
    color: string
  }[]
}

export interface ViewState {
  longitude: number
  latitude: number
  zoom: number
  pitch: number
  bearing: number
}

// SAT backend response types
export interface ClimateArchiveResponse {
  latitude: number
  longitude: number
  daily: {
    time: string[]
    temperature_2m_max: number[]
    temperature_2m_min: number[]
    precipitation_sum: number[]
  }
}

export interface ThermalGridResponse {
  type: 'FeatureCollection'
  features: Array<{
    type: 'Feature'
    geometry: { type: string; coordinates: number[][][] }
    properties: { avg_temp: number }
  }>
}

export interface SunPathResponse {
  summer: Array<{ hour: number; azimuth: number; elevation: number }>
  winter: Array<{ hour: number; azimuth: number; elevation: number }>
  equinox: Array<{ hour: number; azimuth: number; elevation: number }>
}

export interface SolarEventsResponse {
  sunrise: string
  solar_noon: string
  sunset: string
}

export interface SunOrientationResponse {
  recommended_orientation: string
  shading_strategy: string
  notes: string
}

export interface FloodAnalysisResponse {
  risk_category: 'Very Low' | 'Low' | 'Moderate' | 'High' | 'Very High'
  overall_score: number
  elevation_risk: number
  hydrology_risk: number
  historical_risk: number
  llai_risk: number
  notes: string
}

export interface WindAnalysisResponse {
  dominant_orientation: string
  comfort_level: 'Poor' | 'Fair' | 'Good' | 'Excellent'
  wind_load_risk: string
  avg_speed_ms: number
  notes: string
}

export interface RainfallArchiveResponse {
  latitude: number
  longitude: number
  monthly: Array<{
    month: string
    total_mm: number
    rainy_days: number
  }>
}

export interface SatAnalysisResults {
  climate: ClimateArchiveResponse | null
  thermalGrid: ThermalGridResponse | null
  sunPath: SunPathResponse | null
  solarEvents: SolarEventsResponse | null
  sunOrientation: SunOrientationResponse | null
  flood: FloodAnalysisResponse | null
  wind: WindAnalysisResponse | null
  rainfall: RainfallArchiveResponse | null
  loading: boolean
  error: string | null
}

export type AnalysisTab = 'metrics' | 'climate' | 'sun' | 'flood' | 'wind' | 'rainfall'
