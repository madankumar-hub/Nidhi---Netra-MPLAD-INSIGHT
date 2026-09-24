/**
 * A thin React wrapper around plain Leaflet.
 *
 * Plain `leaflet` is used instead of `react-leaflet` on purpose: react-leaflet 5
 * needs React 19 and this app is on React 18, and one small wrapper is easier to
 * reason about than a second dependency. The map is created once; markers are
 * redrawn when `points` change. Canvas rendering keeps 600+ markers smooth.
 */
import { useEffect, useRef } from 'react'
import * as L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import {
  DRAFT_COLOR,
  INDIA_CENTER,
  INDIA_ZOOM,
  TILE_ATTRIBUTION,
  TILE_URL,
} from './mapConfig'
import type { DraftPosition, MapPoint } from './mapData'

interface LeafletMapProps {
  points: MapPoint[]
  /** Accessible name for the map region. */
  ariaLabel: string
  /** Label of the button inside each popup. */
  openLabel: string
  /** Called from the popup button. */
  onOpen: (id: number) => void
  /** Called when a marker is clicked. */
  onSelect?: (id: number) => void
  selectedId?: number | null
  /** When true, clicking the map reports a position through `onPick`. */
  pickMode?: boolean
  onPick?: (lat: number, lng: number) => void
  /** Unsaved geotag preview. */
  draft?: DraftPosition | null
  /** Change this value to re-fit the view to the current points (e.g. on a filter change). */
  fitKey?: string
  /** Called once if the background tiles cannot be downloaded. */
  onTilesFailed?: () => void
  height?: number
  /** Closest zoom used when fitting the view (a single work wants a street-level view). */
  fitMaxZoom?: number
}

export function LeafletMap({
  points,
  ariaLabel,
  openLabel,
  onOpen,
  onSelect,
  selectedId = null,
  pickMode = false,
  onPick,
  draft = null,
  fitKey = '',
  onTilesFailed,
  height = 560,
  fitMaxZoom = 11,
}: LeafletMapProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const markerLayerRef = useRef<L.LayerGroup | null>(null)
  const draftLayerRef = useRef<L.LayerGroup | null>(null)
  const lastFitKeyRef = useRef<string | null>(null)

  // Latest callbacks in refs, so a new function identity from the parent never
  // forces the map or its markers to be rebuilt.
  const onOpenRef = useRef(onOpen)
  const onSelectRef = useRef(onSelect)
  const onPickRef = useRef(onPick)
  const onTilesFailedRef = useRef(onTilesFailed)
  onOpenRef.current = onOpen
  onSelectRef.current = onSelect
  onPickRef.current = onPick
  onTilesFailedRef.current = onTilesFailed

  // ---- Create the map once -------------------------------------------------
  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const map = L.map(container, {
      center: INDIA_CENTER,
      zoom: INDIA_ZOOM,
      minZoom: 4,
      maxZoom: 18,
      preferCanvas: true,
      scrollWheelZoom: true,
    })

    const tiles = L.tileLayer(TILE_URL, { attribution: TILE_ATTRIBUTION, maxZoom: 19 })
    let tileLoaded = false
    let tileErrors = 0
    let reported = false
    tiles.on('tileload', () => {
      tileLoaded = true
    })
    tiles.on('tileerror', () => {
      tileErrors += 1
      if (!tileLoaded && tileErrors >= 3 && !reported) {
        reported = true
        onTilesFailedRef.current?.()
      }
    })
    tiles.addTo(map)

    markerLayerRef.current = L.layerGroup().addTo(map)
    draftLayerRef.current = L.layerGroup().addTo(map)
    mapRef.current = map

    // Leaflet measures its container once. If the layout changes size later
    // (sidebar toggle, window resize), tell it to measure again.
    const observer = new ResizeObserver(() => map.invalidateSize())
    observer.observe(container)

    return () => {
      observer.disconnect()
      map.remove()
      mapRef.current = null
      markerLayerRef.current = null
      draftLayerRef.current = null
      lastFitKeyRef.current = null
    }
  }, [])

  // ---- Markers -------------------------------------------------------------
  useEffect(() => {
    const map = mapRef.current
    const layer = markerLayerRef.current
    if (!map || !layer) return

    layer.clearLayers()
    let selectedMarker: L.CircleMarker | null = null

    for (const point of points) {
      const isSelected = point.id === selectedId
      const marker = L.circleMarker([point.lat, point.lng], {
        radius: isSelected ? point.radius + 3 : point.radius,
        color: isSelected ? '#111827' : '#ffffff',
        weight: isSelected ? 3 : 1,
        fillColor: point.color,
        fillOpacity: 0.9,
      })
      marker.bindTooltip(point.title, { direction: 'top', offset: [0, -4] })
      marker.bindPopup(() => buildPopup(point, openLabel, (id) => onOpenRef.current(id)), {
        maxWidth: 280,
      })
      marker.on('click', () => onSelectRef.current?.(point.id))
      layer.addLayer(marker)
      if (isSelected) selectedMarker = marker
    }
    // Draw the selected marker above its neighbours.
    if (selectedMarker) selectedMarker.bringToFront()

    // Re-fit only when the caller says the dataset changed, not on every redraw
    // (a selection change must not jump the view).
    if (points.length > 0 && lastFitKeyRef.current !== fitKey) {
      lastFitKeyRef.current = fitKey
      const bounds = L.latLngBounds(points.map((p) => [p.lat, p.lng] as [number, number]))
      if (bounds.isValid()) map.fitBounds(bounds, { padding: [28, 28], maxZoom: fitMaxZoom })
    }
  }, [points, selectedId, openLabel, fitKey, fitMaxZoom])

  // ---- Pick-on-map mode ----------------------------------------------------
  useEffect(() => {
    const map = mapRef.current
    if (!map || !pickMode) return

    const container = map.getContainer()
    container.style.cursor = 'crosshair'
    const handleClick = (event: L.LeafletMouseEvent) => {
      onPickRef.current?.(event.latlng.lat, event.latlng.lng)
    }
    map.on('click', handleClick)
    return () => {
      map.off('click', handleClick)
      container.style.cursor = ''
    }
  }, [pickMode])

  // ---- Unsaved geotag preview ----------------------------------------------
  useEffect(() => {
    const map = mapRef.current
    const layer = draftLayerRef.current
    if (!map || !layer) return
    layer.clearLayers()
    if (!draft) return

    L.circleMarker([draft.lat, draft.lng], {
      radius: 11,
      color: DRAFT_COLOR,
      weight: 3,
      dashArray: '4 4',
      fillColor: '#ffffff',
      fillOpacity: 0.6,
    }).addTo(layer)

    if (draft.accuracy && draft.accuracy > 0) {
      // Real-world radius in metres: shows how trustworthy a GPS fix is.
      L.circle([draft.lat, draft.lng], {
        radius: draft.accuracy,
        color: DRAFT_COLOR,
        weight: 1,
        fillOpacity: 0.08,
      }).addTo(layer)
    }

    // Fly to a GPS fix. A map click is already where the user is looking, and
    // typed coordinates change on every keystroke, so neither moves the view.
    if (draft.source === 'gps') {
      map.setView([draft.lat, draft.lng], Math.max(map.getZoom(), 14))
    }
  }, [draft])

  return (
    <div
      ref={containerRef}
      role="region"
      aria-label={ariaLabel}
      // `isolate` + `z-0` keep Leaflet's internal z-indexes (400-1000) inside
      // this box, so the map never paints over the sticky header or modals.
      className="relative isolate z-0 w-full overflow-hidden rounded border border-ink-200 bg-ink-100"
      style={{ height }}
    />
  )
}

/**
 * Popup content built with DOM APIs and textContent. Work titles are free text,
 * so they must never be injected as HTML.
 */
function buildPopup(point: MapPoint, openLabel: string, onOpen: (id: number) => void): HTMLElement {
  const root = document.createElement('div')
  root.className = 'text-sm'

  const title = document.createElement('p')
  title.className = 'font-semibold text-ink-900'
  title.textContent = point.title
  root.appendChild(title)

  for (const line of point.lines) {
    const row = document.createElement('p')
    row.className = 'mt-0.5 text-xs text-ink-600'
    row.textContent = line
    root.appendChild(row)
  }

  const button = document.createElement('button')
  button.type = 'button'
  button.className =
    'mt-2 rounded bg-ink-800 px-3 py-1.5 text-xs font-semibold text-white hover:bg-ink-900'
  button.textContent = openLabel
  button.addEventListener('click', () => onOpen(point.id))
  root.appendChild(button)

  return root
}
