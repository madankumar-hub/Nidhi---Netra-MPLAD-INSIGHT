/** Data helpers for the map pages. */
import type { Page } from '@/types'

/**
 * Reads every page of a paginated endpoint.
 *
 * The public endpoint allows 500 rows per page and the admin one 200, so the
 * seeded 600 works take two or three requests. `maxPages` is a safety stop so a
 * very large real dataset cannot freeze the browser.
 */
export async function fetchAllPages<T>(
  loadPage: (page: number) => Promise<Page<T>>,
  maxPages = 25,
): Promise<T[]> {
  const first = await loadPage(1)
  const items = [...first.items]
  const last = Math.min(first.total_pages, maxPages)
  for (let page = 2; page <= last; page += 1) {
    const next = await loadPage(page)
    items.push(...next.items)
  }
  return items
}

interface MaybeLocated {
  latitude?: number | null
  longitude?: number | null
}

export function hasCoordinates<T extends MaybeLocated>(
  work: T,
): work is T & { latitude: number; longitude: number } {
  return (
    typeof work.latitude === 'number' &&
    typeof work.longitude === 'number' &&
    Number.isFinite(work.latitude) &&
    Number.isFinite(work.longitude)
  )
}

/** One marker on the map. Text fields are rendered with textContent, never as HTML. */
export interface MapPoint {
  id: number
  lat: number
  lng: number
  color: string
  radius: number
  /** Work title - free text typed by an officer, so treated as untrusted. */
  title: string
  /** Short lines under the title in the popup. */
  lines: string[]
}

export interface DraftPosition {
  lat: number
  lng: number
  /** GPS accuracy in metres, when the position came from the device. */
  accuracy?: number
  source: 'gps' | 'map' | 'typed'
}
