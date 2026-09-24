/**
 * Citizen project page - a small map of where this one work is.
 * Public fields only: coordinates and status, never a risk score.
 */
import { useMemo, useState } from 'react'
import { MapPin, Navigation, WifiOff } from 'lucide-react'
import { useI18n } from '@/i18n'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import type { ProjectPublicDetail } from '@/types'
import { LeafletMap } from './LeafletMap'
import { STATUS_COLOR, directionsUrl } from './mapConfig'
import { hasCoordinates } from './mapData'
import type { MapPoint } from './mapData'
import { useMapText } from './mapText'

export function ProjectLocationCard({ project }: { project: ProjectPublicDetail }) {
  const tm = useMapText()
  const { tEnum } = useI18n()
  const [tilesFailed, setTilesFailed] = useState(false)
  const located = hasCoordinates(project)

  const points = useMemo<MapPoint[]>(
    () =>
      hasCoordinates(project)
        ? [
            {
              id: project.id,
              lat: project.latitude,
              lng: project.longitude,
              color: STATUS_COLOR[project.status] ?? '#6b7280',
              radius: 10,
              title: project.title,
              lines: [
                [project.location, tEnum('district', project.district)].filter(Boolean).join(', '),
                tEnum('projectStatus', project.status),
              ],
            },
          ]
        : [],
    [project, tEnum],
  )

  return (
    <Card>
      <CardHeader title={tm('locationTitle')} icon={<MapPin className="h-4 w-4" aria-hidden />} />
      <CardBody className="space-y-3">
        {located ? (
          <>
            <LeafletMap
              points={points}
              ariaLabel={tm('locationTitle')}
              openLabel={tm('getDirections')}
              onOpen={() =>
                window.open(directionsUrl(project.latitude as number, project.longitude as number), '_blank', 'noopener')
              }
              fitKey={String(project.id)}
              fitMaxZoom={14}
              onTilesFailed={() => setTilesFailed(true)}
              height={260}
            />
            {tilesFailed ? (
              <p className="flex items-start gap-1.5 text-xs text-saffron-900">
                <WifiOff className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
                {tm('tilesFailed')}
              </p>
            ) : null}
            <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
              <span className="text-ink-600">
                {tm('coordinates')}:{' '}
                <span className="font-mono tabular-nums text-ink-800">
                  {(project.latitude as number).toFixed(5)}, {(project.longitude as number).toFixed(5)}
                </span>
              </span>
              <a
                href={directionsUrl(project.latitude as number, project.longitude as number)}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 font-medium text-ink-800 underline hover:text-ink-950"
              >
                <Navigation className="h-3.5 w-3.5" aria-hidden />
                {tm('getDirections')}
              </a>
            </div>
            <p className="text-xs text-ink-500">{tm('approxNote')}</p>
          </>
        ) : (
          <p className="text-sm text-ink-600">{tm('noLocationPublic')}</p>
        )}
      </CardBody>
    </Card>
  )
}
