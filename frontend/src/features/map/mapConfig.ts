/**
 * Map module - constants and colour scales.
 *
 * Everything map-specific lives in `features/map/` so the module can be removed
 * by deleting one folder, two pages and a handful of pasted lines.
 */
import type { ProjectStatus, RiskLevel } from '@/types'

/** OpenStreetMap standard tiles. Free, no API key; attribution is mandatory. */
export const TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
export const TILE_ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors'

/** Opening view: the whole of India. */
export const INDIA_CENTER: [number, number] = [22.9, 79.0]
export const INDIA_ZOOM = 5

/**
 * India's bounding box. Matches INDIA_LAT / INDIA_LON in
 * backend/tests/test_geography.py, so a geotag the UI accepts is one the
 * backend's own geography test would also accept.
 */
export const INDIA_LAT_RANGE: [number, number] = [6.4, 35.8]
export const INDIA_LNG_RANGE: [number, number] = [68.0, 97.5]

export function isInsideIndia(lat: number, lng: number): boolean {
  return (
    lat >= INDIA_LAT_RANGE[0] &&
    lat <= INDIA_LAT_RANGE[1] &&
    lng >= INDIA_LNG_RANGE[0] &&
    lng <= INDIA_LNG_RANGE[1]
  )
}

/** Risk colours. Size also grows with risk, so colour is never the only cue. */
export const RISK_STYLE: Record<RiskLevel | 'NONE', { color: string; radius: number }> = {
  CRITICAL: { color: '#b71c1c', radius: 10 },
  HIGH: { color: '#e65100', radius: 8.5 },
  MEDIUM: { color: '#f9a825', radius: 7 },
  LOW: { color: '#2e7d32', radius: 6 },
  NONE: { color: '#6b7280', radius: 6 },
}

export const RISK_ORDER: (RiskLevel | 'NONE')[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'NONE']

export const STATUS_COLOR: Record<ProjectStatus, string> = {
  'Not Started': '#6b7280',
  'In Progress': '#1d4ed8',
  Delayed: '#b71c1c',
  'On Hold': '#f9a825',
  Completed: '#2e7d32',
  Cancelled: '#374151',
}

export const STATUS_ORDER: ProjectStatus[] = [
  'In Progress',
  'Delayed',
  'On Hold',
  'Not Started',
  'Completed',
  'Cancelled',
]

/** Colour of the unsaved geotag preview marker. */
export const DRAFT_COLOR = '#0b3d91'

/**
 * Turn-by-turn directions to a work, for a site inspection. A plain link -
 * no API key and nothing is sent anywhere until the user clicks it.
 */
export function directionsUrl(lat: number, lng: number): string {
  return `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`
}
