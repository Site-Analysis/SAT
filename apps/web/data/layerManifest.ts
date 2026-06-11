import type { LayerConfig } from '@/types'

export const LAYER_MANIFEST: LayerConfig[] = [
  // Environment
  { id: 'water', name: 'Water Bodies', group: 'environment', osmQuery: 'natural=water|waterway', geometryType: 'polygon', color: [30, 144, 255], strokeWidth: 1, extrusionHeight: 0, visible: true, statisticsRecipes: ['area', 'density'] },
  { id: 'park', name: 'Parks & Green', group: 'environment', osmQuery: 'leisure=park|leisure=garden|landuse=grass', geometryType: 'polygon', color: [34, 139, 34], strokeWidth: 1, extrusionHeight: 0, visible: true, statisticsRecipes: ['area', 'density'] },
  { id: 'vegetation', name: 'Vegetation', group: 'environment', osmQuery: 'natural=wood|landuse=forest|natural=scrub', geometryType: 'polygon', color: [0, 100, 0], strokeWidth: 1, extrusionHeight: 0, visible: false, statisticsRecipes: ['area'] },
  { id: 'trees', name: 'Trees', group: 'environment', osmQuery: 'natural=tree', geometryType: 'point', color: [50, 120, 50], strokeWidth: 4, extrusionHeight: 0, visible: false, statisticsRecipes: ['count', 'density'] },

  // Land Use
  { id: 'buildings', name: 'Buildings', group: 'landUse', osmQuery: 'building', geometryType: 'polygon', color: [180, 160, 140], strokeWidth: 1, extrusionHeight: 10, visible: true, statisticsRecipes: ['count', 'area', 'density'] },
  { id: 'residential', name: 'Residential', group: 'landUse', osmQuery: 'landuse=residential', geometryType: 'polygon', color: [255, 200, 150], strokeWidth: 1, extrusionHeight: 0, visible: false, statisticsRecipes: ['area'] },
  { id: 'commercial', name: 'Commercial', group: 'landUse', osmQuery: 'landuse=commercial|landuse=retail', geometryType: 'polygon', color: [255, 100, 50], strokeWidth: 1, extrusionHeight: 0, visible: false, statisticsRecipes: ['area'] },
  { id: 'industrial', name: 'Industrial', group: 'landUse', osmQuery: 'landuse=industrial', geometryType: 'polygon', color: [150, 100, 150], strokeWidth: 1, extrusionHeight: 0, visible: false, statisticsRecipes: ['area'] },
  { id: 'agricultural', name: 'Agricultural', group: 'landUse', osmQuery: 'landuse=farmland|landuse=farmyard', geometryType: 'polygon', color: [200, 190, 100], strokeWidth: 1, extrusionHeight: 0, visible: false, statisticsRecipes: ['area'] },

  // Infrastructure
  { id: 'roads_primary', name: 'Primary Roads', group: 'infrastructure', osmQuery: 'highway=primary|highway=trunk|highway=motorway', geometryType: 'line', color: [220, 80, 80], strokeWidth: 3, extrusionHeight: 0, visible: true, statisticsRecipes: ['count'] },
  { id: 'roads_secondary', name: 'Secondary Roads', group: 'infrastructure', osmQuery: 'highway=secondary|highway=tertiary', geometryType: 'line', color: [200, 140, 60], strokeWidth: 2, extrusionHeight: 0, visible: true, statisticsRecipes: ['count'] },
  { id: 'roads_local', name: 'Local Roads', group: 'infrastructure', osmQuery: 'highway=residential|highway=unclassified|highway=service', geometryType: 'line', color: [180, 180, 180], strokeWidth: 1, extrusionHeight: 0, visible: false, statisticsRecipes: ['count'] },
  { id: 'cycling', name: 'Bike Lanes', group: 'infrastructure', osmQuery: 'highway=cycleway|cycleway=lane', geometryType: 'line', color: [0, 200, 150], strokeWidth: 2, extrusionHeight: 0, visible: false, statisticsRecipes: ['count'] },
  { id: 'railway', name: 'Railways', group: 'infrastructure', osmQuery: 'railway=rail|railway=subway|railway=tram', geometryType: 'line', color: [100, 100, 200], strokeWidth: 2, extrusionHeight: 0, visible: false, statisticsRecipes: ['count'] },

  // Access & Transit
  { id: 'bus_stops', name: 'Bus Stops', group: 'access', osmQuery: 'highway=bus_stop|public_transport=stop_position', geometryType: 'point', color: [255, 165, 0], strokeWidth: 6, extrusionHeight: 0, visible: true, statisticsRecipes: ['count', 'density'] },
  { id: 'metro', name: 'Metro Stations', group: 'access', osmQuery: 'station=subway|railway=station', geometryType: 'point', color: [148, 0, 211], strokeWidth: 8, extrusionHeight: 0, visible: false, statisticsRecipes: ['count', 'density'] },
  { id: 'pedestrian', name: 'Pedestrian Paths', group: 'access', osmQuery: 'highway=footway|highway=path|highway=pedestrian', geometryType: 'line', color: [200, 200, 100], strokeWidth: 1, extrusionHeight: 0, visible: false, statisticsRecipes: ['count'] },

  // Traffic
  { id: 'traffic_lights', name: 'Traffic Lights', group: 'traffic', osmQuery: 'highway=traffic_signals', geometryType: 'point', color: [255, 50, 50], strokeWidth: 6, extrusionHeight: 0, visible: false, statisticsRecipes: ['count', 'density'] },
  { id: 'parking', name: 'Parking', group: 'traffic', osmQuery: 'amenity=parking|parking=surface', geometryType: 'polygon', color: [160, 160, 80], strokeWidth: 1, extrusionHeight: 0, visible: false, statisticsRecipes: ['count', 'area'] },
  { id: 'crossings', name: 'Crossings', group: 'traffic', osmQuery: 'highway=crossing', geometryType: 'point', color: [255, 255, 100], strokeWidth: 5, extrusionHeight: 0, visible: false, statisticsRecipes: ['count'] },

  // Amenities
  { id: 'food', name: 'Food & Dining', group: 'amenities', osmQuery: 'amenity=restaurant|amenity=cafe|amenity=fast_food|amenity=bar', geometryType: 'point', color: [255, 120, 60], strokeWidth: 6, extrusionHeight: 0, visible: true, statisticsRecipes: ['count', 'density'] },
  { id: 'shopping', name: 'Shopping', group: 'amenities', osmQuery: 'shop=supermarket|shop=mall|shop=department_store|amenity=marketplace', geometryType: 'point', color: [255, 180, 50], strokeWidth: 6, extrusionHeight: 0, visible: false, statisticsRecipes: ['count', 'density'] },
  { id: 'healthcare', name: 'Healthcare', group: 'amenities', osmQuery: 'amenity=hospital|amenity=clinic|amenity=pharmacy|amenity=doctors', geometryType: 'point', color: [220, 50, 50], strokeWidth: 7, extrusionHeight: 0, visible: false, statisticsRecipes: ['count', 'density'] },
  { id: 'education', name: 'Education', group: 'amenities', osmQuery: 'amenity=school|amenity=university|amenity=college|amenity=kindergarten', geometryType: 'point', color: [100, 180, 255], strokeWidth: 7, extrusionHeight: 0, visible: false, statisticsRecipes: ['count', 'density'] },
  { id: 'entertainment', name: 'Entertainment', group: 'amenities', osmQuery: 'leisure=cinema|amenity=theatre|leisure=sports_centre|leisure=fitness_centre', geometryType: 'point', color: [200, 100, 255], strokeWidth: 6, extrusionHeight: 0, visible: false, statisticsRecipes: ['count', 'density'] },
  { id: 'finance', name: 'Banks & ATMs', group: 'amenities', osmQuery: 'amenity=bank|amenity=atm', geometryType: 'point', color: [80, 200, 120], strokeWidth: 6, extrusionHeight: 0, visible: false, statisticsRecipes: ['count', 'density'] },
  { id: 'religious', name: 'Places of Worship', group: 'amenities', osmQuery: 'amenity=place_of_worship', geometryType: 'point', color: [180, 140, 80], strokeWidth: 6, extrusionHeight: 0, visible: false, statisticsRecipes: ['count'] },
  { id: 'post', name: 'Post & Services', group: 'amenities', osmQuery: 'amenity=post_office|amenity=police|amenity=fire_station', geometryType: 'point', color: [120, 120, 200], strokeWidth: 6, extrusionHeight: 0, visible: false, statisticsRecipes: ['count'] },
]

export const LAYER_GROUPS: Record<string, { label: string; color: string }> = {
  environment: { label: 'Environment', color: '#22c55e' },
  landUse: { label: 'Land Use', color: '#f97316' },
  infrastructure: { label: 'Infrastructure', color: '#94a3b8' },
  access: { label: 'Access & Transit', color: '#a855f7' },
  traffic: { label: 'Traffic', color: '#ef4444' },
  amenities: { label: 'Amenities', color: '#eab308' },
  custom: { label: 'Custom', color: '#06b6d4' },
}

export function getLayerById(id: string): LayerConfig | undefined {
  return LAYER_MANIFEST.find(l => l.id === id)
}

export function getLayersByGroup(group: string): LayerConfig[] {
  return LAYER_MANIFEST.filter(l => l.group === group)
}
