/**
 * Citizen portal - map of works.
 *
 * Uses only the public API, so it inherits the separation the rest of the
 * citizen portal enforces: status and the public indicator, never a risk score.
 */
import { useCallback, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Info, WifiOff } from 'lucide-react'
import { projectsApi } from '@/api'
import { useApi } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { PageHeader } from '@/components/layout/PageHeader'
import { SelectInput } from '@/components/ui/Field'
import { ErrorState } from '@/components/ui/States'
import { formatLakh, formatPercent } from '@/utils/format'
import {
  LeafletMap,
  MapLegend,
  STATUS_COLOR,
  STATUS_ORDER,
  fetchAllPages,
  hasCoordinates,
  useMapText,
} from '@/features/map'
import type { MapPoint } from '@/features/map'
import type { ProjectStatus } from '@/types'

export function PublicMapPage() {
  const tm = useMapText()
  const { tEnum } = useI18n()
  const navigate = useNavigate()

  const [district, setDistrict] = useState('')
  const [status, setStatus] = useState<ProjectStatus | ''>('')
  const [tilesFailed, setTilesFailed] = useState(false)

  const filters = useApi((signal) => projectsApi.getPublicFilters(signal), [])
  const works = useApi(
    (signal) =>
      fetchAllPages((page) =>
        projectsApi.listPublicProjects(
          { district: district || undefined, status: status || undefined, page, page_size: 500 },
          signal,
        ),
      ),
    [district, status],
  )

  const all = useMemo(() => works.data ?? [], [works.data])
  const located = useMemo(() => all.filter(hasCoordinates), [all])

  const points = useMemo<MapPoint[]>(
    () =>
      located.map((work) => ({
        id: work.id,
        lat: work.latitude,
        lng: work.longitude,
        color: STATUS_COLOR[work.status] ?? '#6b7280',
        radius: 7,
        title: work.title,
        lines: [
          `${tEnum('district', work.district)} · ${tEnum('category', work.category)}`,
          `${tEnum('projectStatus', work.status)} · ${tm('progress')} ${formatPercent(work.progress_percent, 0)}`,
          `${tm('allocated')} ${formatLakh(work.allocated_amount)}`,
          tEnum('publicIndicator', work.public_indicator),
        ],
      })),
    [located, tEnum, tm],
  )

  const legend = useMemo(
    () =>
      STATUS_ORDER.map((value) => ({
        label: tEnum('projectStatus', value),
        color: STATUS_COLOR[value],
        count: located.filter((work) => work.status === value).length,
      })).filter((item) => item.count > 0),
    [located, tEnum],
  )

  const openWork = useCallback((id: number) => navigate(`/scheme/${id}`), [navigate])

  const districtOptions = (filters.data?.districts ?? []).map((option) => ({
    value: option.value,
    label: tEnum('district', option.value),
    count: option.count,
  }))
    // The backend's status facet returns Python enum names ("ProjectStatus.COMPLETED"),
  // so - like the Projects page - the options come from the fixed list instead.
  const statusOptions = STATUS_ORDER.map((value) => ({
    value,
    label: tEnum('projectStatus', value),
  }))

  const missingCount = all.length - located.length

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <PageHeader title={tm('publicTitle')} description={tm('publicDescription')} />

      <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:max-w-2xl">
        <SelectInput
          label={tm('filterDistrict')}
          placeholder={tm('all')}
          options={districtOptions}
          value={district}
          onChange={(e) => setDistrict(e.target.value)}
        />
        <SelectInput
          label={tm('filterStatus')}
          placeholder={tm('all')}
          options={statusOptions}
          value={status}
          onChange={(e) => setStatus(e.target.value as ProjectStatus | '')}
        />
      </div>

      {works.error ? (
        <div className="mb-4">
          <ErrorState error={works.error} onRetry={works.reload} />
        </div>
      ) : null}

      {tilesFailed ? (
        <p className="mb-3 flex items-start gap-2 rounded border border-saffron-300 bg-saffron-50 px-3 py-2 text-sm text-saffron-900">
          <WifiOff className="mt-0.5 h-4 w-4 shrink-0" aria-hidden />
          {tm('tilesFailed')}
        </p>
      ) : null}

      <p className="mb-2 text-sm text-ink-700" aria-live="polite">
        {works.loading ? tm('loading') : tm('plotted', { shown: located.length, total: all.length })}
      </p>

      <LeafletMap
        points={points}
        ariaLabel={tm('mapAria')}
        openLabel={tm('openDetails')}
        onOpen={openWork}
        fitKey={`${district}|${status}`}
        onTilesFailed={() => setTilesFailed(true)}
      />

      <div className="mt-3 space-y-3">
        {legend.length > 0 ? <MapLegend title={tm('legendTitle')} items={legend} /> : null}
        <p className="flex items-start gap-1.5 text-xs text-ink-600">
          <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
          <span>
            {missingCount > 0 ? `${tm('missing', { count: missingCount })} ` : ''}
            {tm('approxNote')}
          </span>
        </p>
      </div>

      {/* Keyboard and screen-reader equivalent of the map (GIGW). */}
      {located.length > 0 ? (
        <details className="mt-6 rounded border border-ink-200 bg-white">
          <summary className="cursor-pointer px-4 py-3 text-sm font-semibold text-ink-800">
            {tm('listTitle')} ({located.length})
          </summary>
          <div className="max-h-96 overflow-auto border-t border-ink-200">
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 bg-ink-50 text-xs uppercase text-ink-600">
                <tr>
                  <th className="px-4 py-2">{tm('colWork')}</th>
                  <th className="px-4 py-2">{tm('colDistrict')}</th>
                  <th className="px-4 py-2">{tm('colStatus')}</th>
                  <th className="px-4 py-2">{tm('colLocation')}</th>
                </tr>
              </thead>
              <tbody>
                {located.map((work) => (
                  <tr key={work.id} className="border-t border-ink-100">
                    <td className="px-4 py-2">
                      <Link to={`/scheme/${work.id}`} className="text-ink-800 underline hover:text-ink-950">
                        {work.title}
                      </Link>
                    </td>
                    <td className="px-4 py-2">{tEnum('district', work.district)}</td>
                    <td className="px-4 py-2">{tEnum('projectStatus', work.status)}</td>
                    <td className="px-4 py-2 font-mono text-xs tabular-nums">
                      {work.latitude.toFixed(4)}, {work.longitude.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      ) : null}
    </div>
  )
}
