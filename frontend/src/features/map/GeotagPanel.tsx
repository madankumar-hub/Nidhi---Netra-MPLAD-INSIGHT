/**
 * Geotagging: record where a work physically is.
 *
 * Three ways to set a position - the device GPS (an officer standing at the
 * site), a click on the map, or typed coordinates - all previewed on the map
 * before anything is saved. Saving goes through the existing
 * PATCH /api/admin/projects/{id}, which already writes an activity-log entry
 * and re-runs the risk assessment.
 */
import { useEffect, useState } from 'react'
import { Crosshair, LocateFixed, MapPin, Save, X } from 'lucide-react'
import { adminApi, ApiError } from '@/api'
import { Button } from '@/components/ui/Button'
import { TextInput } from '@/components/ui/Field'
import { isInsideIndia } from './mapConfig'
import type { DraftPosition } from './mapData'
import { useMapText } from './mapText'

interface GeotagPanelProps {
  projectId: number
  latitude?: number | null
  longitude?: number | null
  draft: DraftPosition | null
  onDraftChange: (draft: DraftPosition | null) => void
  picking: boolean
  onPickingChange: (picking: boolean) => void
  /** Called after a successful save, so the page can reload its data. */
  onSaved: () => void
}

type Feedback = { tone: 'error' | 'success' | 'info'; text: string } | null

export function GeotagPanel({
  projectId,
  latitude,
  longitude,
  draft,
  onDraftChange,
  picking,
  onPickingChange,
  onSaved,
}: GeotagPanelProps) {
  const tm = useMapText()
  const [latText, setLatText] = useState('')
  const [lngText, setLngText] = useState('')
  const [locating, setLocating] = useState(false)
  const [saving, setSaving] = useState(false)
  const [feedback, setFeedback] = useState<Feedback>(null)

  const hasRecorded = typeof latitude === 'number' && typeof longitude === 'number'

  // A GPS fix or a map click fills the inputs. Typing does not round-trip,
  // otherwise the cursor would jump while the user is still typing.
  useEffect(() => {
    if (draft && draft.source !== 'typed') {
      setLatText(draft.lat.toFixed(6))
      setLngText(draft.lng.toFixed(6))
    }
  }, [draft])

  // Switching to another work starts from its recorded position.
  useEffect(() => {
    setLatText(typeof latitude === 'number' ? latitude.toFixed(6) : '')
    setLngText(typeof longitude === 'number' ? longitude.toFixed(6) : '')
    setFeedback(null)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId])

  const handleTyped = (nextLat: string, nextLng: string) => {
    setLatText(nextLat)
    setLngText(nextLng)
    setFeedback(null)
    const lat = Number(nextLat)
    const lng = Number(nextLng)
    if (nextLat.trim() && nextLng.trim() && Number.isFinite(lat) && Number.isFinite(lng)) {
      onDraftChange({ lat, lng, source: 'typed' })
    }
  }

  const locateWithGps = () => {
    setFeedback(null)
    if (!window.isSecureContext) {
      setFeedback({ tone: 'error', text: tm('gpsInsecure') })
      return
    }
    if (!('geolocation' in navigator)) {
      setFeedback({ tone: 'error', text: tm('gpsUnavailable') })
      return
    }
    setLocating(true)
    onPickingChange(false)
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocating(false)
        const { latitude: lat, longitude: lng, accuracy } = position.coords
        onDraftChange({ lat, lng, accuracy, source: 'gps' })
        setFeedback({ tone: 'info', text: tm('accuracy', { metres: Math.round(accuracy) }) })
      },
      (error) => {
        setLocating(false)
        setFeedback({
          tone: 'error',
          text: error.code === error.PERMISSION_DENIED ? tm('gpsDenied') : tm('gpsUnavailable'),
        })
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 0 },
    )
  }

  const discard = () => {
    onDraftChange(null)
    onPickingChange(false)
    setLatText(hasRecorded ? (latitude as number).toFixed(6) : '')
    setLngText(hasRecorded ? (longitude as number).toFixed(6) : '')
    setFeedback(null)
  }

  const save = async () => {
    const lat = Number(latText)
    const lng = Number(lngText)
    if (!latText.trim() || !lngText.trim() || !Number.isFinite(lat) || !Number.isFinite(lng)) {
      setFeedback({ tone: 'error', text: tm('invalidNumber') })
      return
    }
    if (!isInsideIndia(lat, lng)) {
      setFeedback({ tone: 'error', text: tm('outOfIndia') })
      return
    }
    setSaving(true)
    setFeedback(null)
    try {
      // Six decimals is about 11 cm - more than any phone GPS can justify.
      await adminApi.updateProject(projectId, {
        latitude: Number(lat.toFixed(6)),
        longitude: Number(lng.toFixed(6)),
      })
      onDraftChange(null)
      onPickingChange(false)
      setFeedback({ tone: 'success', text: tm('saved') })
      onSaved()
    } catch (err) {
      setFeedback({
        tone: 'error',
        text: err instanceof ApiError ? err.message : (err as Error)?.message ?? 'Error',
      })
    } finally {
      setSaving(false)
    }
  }

  const feedbackClass =
    feedback?.tone === 'error'
      ? 'border-[#8f1d1d]/30 bg-[#8f1d1d]/5 text-[#8f1d1d]'
      : feedback?.tone === 'success'
        ? 'border-moss-700/30 bg-moss-50 text-moss-800'
        : 'border-ink-200 bg-ink-50 text-ink-700'

  return (
    <section className="rounded border border-ink-200 bg-white p-4" aria-labelledby="geotag-heading">
      <h3 id="geotag-heading" className="flex items-center gap-1.5 text-sm font-semibold text-ink-900">
        <MapPin className="h-4 w-4" aria-hidden />
        {tm('geotagTitle')}
      </h3>

      <p className="mt-1 text-xs text-ink-600">
        {tm('geotagCurrent')}:{' '}
        <span className="font-mono tabular-nums text-ink-800">
          {hasRecorded
            ? `${(latitude as number).toFixed(5)}, ${(longitude as number).toFixed(5)}`
            : tm('geotagNone')}
        </span>
      </p>

      <div className="mt-3 flex flex-wrap gap-2">
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={locateWithGps}
          disabled={locating || saving}
          icon={<LocateFixed className="h-3.5 w-3.5" aria-hidden />}
        >
          {locating ? tm('locating') : tm('useGps')}
        </Button>
        <Button
          type="button"
          variant={picking ? 'accent' : 'secondary'}
          size="sm"
          onClick={() => onPickingChange(!picking)}
          disabled={saving}
          aria-pressed={picking}
          icon={<Crosshair className="h-3.5 w-3.5" aria-hidden />}
        >
          {picking ? tm('stopPicking') : tm('pickOnMap')}
        </Button>
      </div>
      {picking ? <p className="mt-2 text-xs font-medium text-saffron-800">{tm('pickingHint')}</p> : null}

      <div className="mt-3 grid grid-cols-2 gap-2">
        <TextInput
          label={tm('latitude')}
          inputMode="decimal"
          value={latText}
          onChange={(e) => handleTyped(e.target.value, lngText)}
          className="font-mono"
        />
        <TextInput
          label={tm('longitude')}
          inputMode="decimal"
          value={lngText}
          onChange={(e) => handleTyped(latText, e.target.value)}
          className="font-mono"
        />
      </div>

      {draft ? <p className="mt-2 text-xs text-ink-600">{tm('draftNote')}</p> : null}

      {feedback ? (
        <p className={`mt-3 rounded border px-3 py-2 text-xs ${feedbackClass}`} role="status">
          {feedback.text}
        </p>
      ) : null}

      <div className="mt-3 flex flex-wrap gap-2">
        <Button
          type="button"
          size="sm"
          onClick={save}
          disabled={saving || !draft}
          icon={<Save className="h-3.5 w-3.5" aria-hidden />}
        >
          {saving ? tm('saving') : tm('save')}
        </Button>
        {draft || picking ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={discard}
            disabled={saving}
            icon={<X className="h-3.5 w-3.5" aria-hidden />}
          >
            {tm('discard')}
          </Button>
        ) : null}
      </div>
    </section>
  )
}
