/**
 * Officials' portal - risk map with geotagging.
 *
 * Markers are coloured by risk level (or status). Selecting one opens a side
 * panel with the work's summary and, for reviewers, the geotag editor. Works
 * with no recorded location are listed so they can be geotagged too.
 */
import { useCallback, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ExternalLink, Info, WifiOff, X } from 'lucide-react'
import { adminApi } from '@/api'
import { useApi } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { useAuth } from '@/features/auth/AuthContext'
import { PageHeader } from '@/components/layout/PageHeader'
import { SelectInput } from '@/components/ui/Field'
import { ErrorState } from '@/components/ui/States'
import { RiskBadge, StatusBadge } from '@/components/ui/Badge'
import { formatLakh, formatPercent } from '@/utils/format'
import {
  GeotagPanel,
  LeafletMap,
  MapLegend,
  RISK_ORDER,
  RISK_STYLE,
  STATUS_COLOR,
  STATUS_ORDER,
  fetchAllPages,
  hasCoordinates,
  useMapText,
} from '@/features/map'
import type { DraftPosition, MapPoint } from '@/features/map'
import type { ProjectAdminSummary, RiskLevel } from '@/types'

type ColourMode = 'risk' | 'status'

const RISK_LEVELS: RiskLevel[] = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']

function riskKey(work: ProjectAdminSummary): RiskLevel | 'NONE' {
  return work.risk_level ?? 'NONE'
}

export function AdminMapPage() {
  const tm = useMapText()
  const { tEnum } = useI18n()
  const { isReviewer } = useAuth()
  const navigate = useNavigate()

  const [district, setDistrict] = useState('')
  const [riskLevel, setRiskLevel] = useState<RiskLevel | ''>('')
  const [colourMode, setColourMode] = useState<ColourMode>('risk')
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [draft, setDraft] = useState<DraftPosition | null>(null)
  const [picking, setPicking] = useState(false)
  const [tilesFailed, setTilesFailed] = useState(false)

  const filters = useApi((signal) => adminApi.getAdminFilters(signal), [])
  const works = useApi(
    (signal) =>
      fetchAllPages((page) =>
        adminApi.listAdminProjects(
          { district: district || undefined, risk_level: riskLevel || undefined, page, page_size: 200 },
          signal,
        ),
      ),
    [district, riskLevel],
  )

  const all = useMemo(() => works.data ?? [], [works.data])
  const located = useMemo(() => all.filter(hasCoordinates), [all])
  const unlocated = useMemo(() => all.filter((work) => !hasCoordinates(work)), [all])
  const selected = useMemo(
    () => all.find((work) => work.id === selectedId) ?? null,
    [all, selectedId],
  )

  const points = useMemo<MapPoint[]>(() => {
    // Draw high-risk works last so they sit on top of low-risk neighbours.
    const ordered = [...located].sort(
      (a, b) => RISK_ORDER.indexOf(riskKey(b)) - RISK_ORDER.indexOf(riskKey(a)),
    )
    return ordered.map((work) => {
      const risk = RISK_STYLE[riskKey(work)]
      return {
        id: work.id,
        lat: work.latitude,
        lng: work.longitude,
        color: colourMode === 'risk' ? risk.color : STATUS_COLOR[work.status] ?? '#6b7280',
        radius: colourMode === 'risk' ? risk.radius : 7,
        title: work.title,
        lines: [
          `${work.project_code} · ${tEnum('district', work.district)}`,
          `${tm('colRisk')}: ${
            work.risk_level
              ? `${tEnum('riskLevel', work.risk_level)}${
                  typeof work.risk_score === 'number' ? ` (${work.risk_score.toFixed(0)})` : ''
                }`
              : tm('notAssessed')
          }`,
          `${tEnum('projectStatus', work.status)} · ${tm('progress')} ${formatPercent(work.progress_percent, 0)}`,
          `${tm('utilisation')} ${formatPercent(work.utilization_percent, 0)} · ${formatLakh(work.allocated_amount)}`,
        ],
      }
    })
  }, [located, colourMode, tEnum, tm])

  const legend = useMemo(() => {
    if (colourMode === 'risk') {
      return RISK_ORDER.map((key) => ({
        label: key === 'NONE' ? tm('notAssessed') : tEnum('riskLevel', key),
        color: RISK_STYLE[key].color,
        radius: RISK_STYLE[key].radius,
        count: located.filter((work) => riskKey(work) === key).length,
      })).filter((item) => item.count > 0)
    }
    return STATUS_ORDER.map((value) => ({
      label: tEnum('projectStatus', value),
      color: STATUS_COLOR[value],
      count: located.filter((work) => work.status === value).length,
    })).filter((item) => item.count > 0)
  }, [colourMode, located, tEnum, tm])

  const selectWork = useCallback((id: number | null) => {
    setSelectedId(id)
    setDraft(null)
    setPicking(false)
  }, [])

  const openWork = useCallback((id: number) => navigate(`/admin/projects/${id}`), [navigate])

  const handlePick = useCallback((lat: number, lng: number) => {
    setDraft({ lat, lng, source: 'map' })
  }, [])

  const districtOptions = (filters.data?.districts ?? []).map((option) => ({
    value: option.value,
    label: tEnum('district', option.value),
    count: option.count,
  }))
  const riskOptions = RISK_LEVELS.map((level) => ({ value: level, label: tEnum('riskLevel', level) }))
  const colourOptions = [
    { value: 'risk', label: tm('colourRisk') },
    { value: 'status', label: tm('colourStatus') },
  ]

  return (
    <div>
      <PageHeader title={tm('adminTitle')} description={tm('adminDescription')} />

      <div className="mb-4 grid gap-3 sm:grid-cols-3 lg:max-w-3xl">
        <SelectInput
          label={tm('filterDistrict')}
          placeholder={tm('all')}
          options={districtOptions}
          value={district}
          onChange={(e) => {
            setDistrict(e.target.value)
            selectWork(null)
          }}
        />
        <SelectInput
          label={tm('filterRisk')}
          placeholder={tm('all')}
          options={riskOptions}
          value={riskLevel}
          onChange={(e) => {
            setRiskLevel(e.target.value as RiskLevel | '')
            selectWork(null)
          }}
        />
        <SelectInput
          label={tm('colourBy')}
          options={colourOptions}
          value={colourMode}
          onChange={(e) => setColourMode(e.target.value as ColourMode)}
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

      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div className="min-w-0 space-y-3">
          <LeafletMap
            points={points}
            ariaLabel={tm('mapAria')}
            openLabel={tm('openDetails')}
            onOpen={openWork}
            onSelect={selectWork}
            selectedId={selectedId}
            pickMode={picking}
            onPick={handlePick}
            draft={draft}
            fitKey={`${district}|${riskLevel}`}
            onTilesFailed={() => setTilesFailed(true)}
            height={600}
          />
          {legend.length > 0 ? <MapLegend title={tm('legendTitle')} items={legend} /> : null}
          <p className="flex items-start gap-1.5 text-xs text-ink-600">
            <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden />
            <span>
              {unlocated.length > 0 ? `${tm('missing', { count: unlocated.length })} ` : ''}
              {tm('approxNote')}
            </span>
          </p>
        </div>

        <aside className="space-y-3">
          {selected ? (
            <section className="rounded border border-ink-200 bg-white p-4" aria-labelledby="map-selected-heading">
              <div className="flex items-start justify-between gap-2">
                <p id="map-selected-heading" className="text-xs font-semibold uppercase tracking-wide text-ink-600">
                  {tm('selectedTitle')}
                </p>
                <button
                  type="button"
                  onClick={() => selectWork(null)}
                  className="rounded p-1 text-ink-500 hover:bg-ink-100 hover:text-ink-800"
                  aria-label={tm('clearSelection')}
                >
                  <X className="h-4 w-4" aria-hidden />
                </button>
              </div>
              <h2 className="mt-1 text-base font-semibold leading-snug text-ink-900">{selected.title}</h2>
              <p className="mt-0.5 text-xs text-ink-600">
                {selected.project_code} · {tEnum('district', selected.district)} ·{' '}
                {tEnum('category', selected.category)}
              </p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                <StatusBadge status={selected.status} />
                {selected.risk_level ? (
                  <RiskBadge level={selected.risk_level} score={selected.risk_score} />
                ) : null}
              </div>
              <dl className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
                <dt className="text-ink-600">{tm('progress')}</dt>
                <dd className="text-right tabular-nums text-ink-900">
                  {formatPercent(selected.progress_percent, 0)}
                </dd>
                <dt className="text-ink-600">{tm('utilisation')}</dt>
                <dd className="text-right tabular-nums text-ink-900">
                  {formatPercent(selected.utilization_percent, 0)}
                </dd>
                <dt className="text-ink-600">{tm('allocated')}</dt>
                <dd className="text-right tabular-nums text-ink-900">
                  {formatLakh(selected.allocated_amount)}
                </dd>
              </dl>
              <Link
                to={`/admin/projects/${selected.id}`}
                className="mt-3 inline-flex items-center gap-1.5 text-sm font-medium text-ink-800 underline hover:text-ink-950"
              >
                {tm('openDetails')}
                <ExternalLink className="h-3.5 w-3.5" aria-hidden />
              </Link>
            </section>
          ) : (
            <p className="rounded border border-dashed border-ink-300 bg-white p-4 text-sm text-ink-600">
              {tm('selectHint')}
            </p>
          )}

          {selected && isReviewer ? (
            <GeotagPanel
              projectId={selected.id}
              latitude={selected.latitude}
              longitude={selected.longitude}
              draft={draft}
              onDraftChange={setDraft}
              picking={picking}
              onPickingChange={setPicking}
              onSaved={works.reload}
            />
          ) : null}

          {unlocated.length > 0 ? (
            <section className="rounded border border-ink-200 bg-white" aria-labelledby="map-unlocated-heading">
              <div className="border-b border-ink-200 px-4 py-3">
                <h3 id="map-unlocated-heading" className="text-sm font-semibold text-ink-900">
                  {tm('noLocationList')} ({unlocated.length})
                </h3>
                {isReviewer ? <p className="text-xs text-ink-600">{tm('noLocationHint')}</p> : null}
              </div>
              <ul className="max-h-64 divide-y divide-ink-100 overflow-auto">
                {unlocated.map((work) => (
                  <li key={work.id}>
                    <button
                      type="button"
                      onClick={() => selectWork(work.id)}
                      className={`w-full px-4 py-2 text-left text-sm hover:bg-ink-50 ${
                        work.id === selectedId ? 'bg-saffron-50' : ''
                      }`}
                    >
                      <span className="block truncate text-ink-900">{work.title}</span>
                      <span className="block text-xs text-ink-600">
                        {work.project_code} · {tEnum('district', work.district)}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
        </aside>
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
                  <th className="px-4 py-2">{tm('colRisk')}</th>
                  <th className="px-4 py-2">{tm('colLocation')}</th>
                </tr>
              </thead>
              <tbody>
                {located.map((work) => (
                  <tr key={work.id} className="border-t border-ink-100">
                    <td className="px-4 py-2">
                      <Link to={`/admin/projects/${work.id}`} className="text-ink-800 underline hover:text-ink-950">
                        {work.title}
                      </Link>
                    </td>
                    <td className="px-4 py-2">{tEnum('district', work.district)}</td>
                    <td className="px-4 py-2">
                      {work.risk_level ? tEnum('riskLevel', work.risk_level) : tm('notAssessed')}
                    </td>
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
