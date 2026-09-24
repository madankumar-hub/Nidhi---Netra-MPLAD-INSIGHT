/**
 * Officials' project page - "Location" tab.
 *
 * The work on a street-level map, coloured by its risk level, with the geotag
 * editor beside it for Officers, Auditors and Administrators. A work with no
 * coordinates opens on India so it can be pinned by GPS or by clicking.
 */
import { useMemo, useState } from 'react'
import { MapPin, Navigation, WifiOff } from 'lucide-react'
import { useI18n } from '@/i18n'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import type { ProjectAdminDetail } from '@/types'
import { GeotagPanel } from './GeotagPanel'
import { LeafletMap } from './LeafletMap'
import { RISK_STYLE, directionsUrl } from './mapConfig'
import { hasCoordinates } from './mapData'
import type { DraftPosition, MapPoint } from './mapData'
import { useMapText } from './mapText'

interface ProjectLocationPanelProps {
  project: ProjectAdminDetail
  /** Reviewers (Officer, Auditor, Administrator) may change the geotag. */
  canEdit: boolean
  /** The page's reload, so a saved geotag refreshes the whole record. */
  onSaved: () => void
}

export function ProjectLocationPanel({ project, canEdit, onSaved }: ProjectLocationPanelProps) {
  const tm = useMapText()
  const { tEnum } = useI18n()
  const [draft, setDraft] = useState<DraftPosition | null>(null)
  const [picking, setPicking] = useState(false)
  const [tilesFailed, setTilesFailed] = useState(false)
  const located = hasCoordinates(project)

  const points = useMemo<MapPoint[]>(() => {
    if (!hasCoordinates(project)) return []
    const style = RISK_STYLE[project.risk_level ?? 'NONE']
    return [
      {
        id: project.id,
        lat: project.latitude,
        lng: project.longitude,
        color: style.color,
        radius: Math.max(style.radius, 9),
        title: project.title,
        lines: [
          [project.location, project.block, tEnum('district', project.district)]
            .filter(Boolean)
            .join(', '),
          `${tm('colRisk')}: ${
            project.risk_level ? tEnum('riskLevel', project.risk_level) : tm('notAssessed')
          }`,
        ],
      },
    ]
  }, [project, tEnum, tm])

  return (
    <div className={`grid items-start gap-4 ${canEdit ? 'xl:grid-cols-[minmax(0,1fr)_340px]' : ''}`}>
      <Card>
        <CardHeader
          title={tm('locationTitle')}
          icon={<MapPin className="h-4 w-4" aria-hidden />}
          actions={
            located ? (
              <a
                href={directionsUrl(project.latitude as number, project.longitude as number)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm font-medium text-ink-800 underline hover:text-ink-950"
              >
                <Navigation className="h-4 w-4" aria-hidden />
                {tm('getDirections')}
              </a>
            ) : null
          }
        />
        <CardBody className="space-y-3">
          {!located ? (
            <p className="rounded border border-saffron-300 bg-saffron-50 px-3 py-2 text-sm text-saffron-900">
              {canEdit ? tm('noLocationAdmin') : tm('noLocationPublic')}
            </p>
          ) : null}
          {tilesFailed ? (
            <p className="flex items-start gap-1.5 text-xs text-saffron-900">
              <WifiOff className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
              {tm('tilesFailed')}
            </p>
          ) : null}
          <LeafletMap
            points={points}
            ariaLabel={tm('locationTitle')}
            openLabel={tm('getDirections')}
            onOpen={() => {
              if (hasCoordinates(project)) {
                window.open(directionsUrl(project.latitude, project.longitude), '_blank', 'noopener')
              }
            }}
            pickMode={canEdit && picking}
            onPick={(lat, lng) => setDraft({ lat, lng, source: 'map' })}
            draft={draft}
            fitKey={String(project.id)}
            fitMaxZoom={15}
            onTilesFailed={() => setTilesFailed(true)}
            height={420}
          />
          <p className="text-xs text-ink-500">{tm('approxNote')}</p>
        </CardBody>
      </Card>

      {canEdit ? (
        <GeotagPanel
          projectId={project.id}
          latitude={project.latitude}
          longitude={project.longitude}
          draft={draft}
          onDraftChange={setDraft}
          picking={picking}
          onPickingChange={setPicking}
          onSaved={onSaved}
        />
      ) : null}
    </div>
  )
}
