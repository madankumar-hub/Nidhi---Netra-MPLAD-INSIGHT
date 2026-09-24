import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  ArrowLeft,
  Banknote,
  CalendarClock,
  FileText,
  ImageOff,
  Info,
  MessageSquareWarning,
} from 'lucide-react'
import { projectsApi } from '@/api'
import { useApi } from '@/hooks/useApi'
import { useAuth } from '@/features/auth/AuthContext'
import { useI18n } from '@/i18n'
import { Badge, StatusBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { ProjectLocationCard } from '@/features/map'
import { DataGrid, DataRow, ProgressBar, StatCard } from '@/components/ui/Metrics'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState, ErrorState, InlineMessage } from '@/components/ui/States'
import { ProgressTimelineChart, SpendingTimelineChart, UtilizationDonut } from '@/components/charts'
import { ReportIssueDialog } from '@/features/citizen/ReportIssueDialog'
import { formatDate, formatLakh, formatNumber, formatPercent } from '@/utils/format'

/**
 * CITIZEN scheme detail page (SRS FR7a) - deliberately separate from the
 * administrative page. It renders public project information, funds, progress
 * and public charts only. Internal risk scores, mitigation, notes, reviews and
 * the audit trail are not requested here and are not served by this API.
 */
export function SchemeDetailPage() {
  const { id } = useParams<{ id: string }>()
  const projectId = Number(id)
  const { t, tEnum } = useI18n()
  const { isAuthenticated } = useAuth()
  const [reportOpen, setReportOpen] = useState(false)
  const [reportMessage, setReportMessage] = useState<string | null>(null)

  const project = useApi(
    (signal) => projectsApi.getPublicProject(projectId, signal),
    [projectId],
    { enabled: Number.isFinite(projectId) },
  )
  const myReports = useApi(
    (signal) => projectsApi.listMyReports(projectId, signal),
    [projectId, reportMessage],
    { enabled: isAuthenticated && Number.isFinite(projectId) },
  )

  if (!Number.isFinite(projectId)) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16">
        <EmptyState title={t('common.empty')} description={t('common.emptyHint')} />
      </div>
    )
  }

  if (project.loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Spinner label={t('common.loading')} />
      </div>
    )
  }

  if (project.error || !project.data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16">
        <ErrorState error={project.error} onRetry={project.reload} retryLabel={t('common.retry')} />
      </div>
    )
  }

  const p = project.data
  const underReview = p.public_indicator === 'Under Review'

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <Link
        to="/projects"
        className="inline-flex items-center gap-1.5 text-sm text-ink-600 hover:text-ink-900"
      >
        <ArrowLeft className="h-4 w-4" aria-hidden />
        {t('nav.projects')}
      </Link>

      <header className="mt-4">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-mono text-xs text-ink-500">{p.project_code}</span>
          <StatusBadge status={p.status} />
          <Badge tone={underReview ? 'warning' : 'success'} dot title={t('detail.indicatorHelp')}>
            {underReview ? t('detail.indicatorUnderReview') : t('detail.indicatorNormal')}
          </Badge>
          {p.is_overdue ? <Badge tone="danger">{t('field.overdue')}</Badge> : null}
        </div>
        <h1 className="mt-2 text-xl font-semibold leading-snug text-ink-900 sm:text-2xl">{p.title}</h1>
        <p className="mt-1 text-sm text-ink-600">
          {tEnum('district', p.district)}, {tEnum('state', p.state)} ·{' '}
          {tEnum('category', p.category)}
        </p>
      </header>

      {reportMessage ? (
        <div className="mt-4">
          <InlineMessage tone="success">{reportMessage}</InlineMessage>
        </div>
      ) : null}

      {/* Headline figures */}
      <div className="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard
          label={t('field.allocated')}
          value={formatLakh(p.allocated_amount)}
          icon={<Banknote className="h-4 w-4" aria-hidden />}
        />
        <StatCard label={t('field.spent')} value={formatLakh(p.spent_amount)} />
        <StatCard label={t('field.remaining')} value={formatLakh(p.remaining_amount)} />
        <StatCard
          label={t('field.utilization')}
          value={formatPercent(p.utilization_percent)}
          tone={p.utilization_percent > 100 ? 'danger' : 'default'}
        />
      </div>

      <div className="mt-6 grid items-start gap-6 lg:grid-cols-3">
        <div className="min-w-0 space-y-6 lg:col-span-2">
          {/* Project information */}
          <Card>
            <CardHeader
              title={t('detail.projectInformation')}
              icon={<Info className="h-4 w-4" aria-hidden />}
            />
            <CardBody>
              <DataGrid>
                <DataRow label={t('field.projectId')}>{p.project_code}</DataRow>
                <DataRow label={t('field.mp')}>
                  {p.mp_name}
                  {p.constituency ? ` (${p.constituency})` : ''}
                </DataRow>
                <DataRow label={t('field.house')}>{p.house}</DataRow>
                <DataRow label={t('field.district')}>{p.district}</DataRow>
                <DataRow label={t('field.state')}>{p.state}</DataRow>
                <DataRow label={t('field.block')}>{p.block ?? t('common.notRecorded')}</DataRow>
                <DataRow label={t('field.location')}>{p.location ?? t('common.notRecorded')}</DataRow>
                <DataRow label={t('field.category')}>{p.category}</DataRow>
                <DataRow label={t('field.agency')}>{p.executing_agency}</DataRow>
                <DataRow label={t('field.contractor')}>{p.contractor ?? t('common.notRecorded')}</DataRow>
                <DataRow label={t('field.sanctionYear')}>{p.sanction_year}</DataRow>
                <DataRow label={t('field.sanctionDate')}>{formatDate(p.sanction_date)}</DataRow>
                <DataRow label={t('field.startDate')}>{formatDate(p.start_date)}</DataRow>
                <DataRow label={t('field.endDate')}>{formatDate(p.planned_end_date)}</DataRow>
                <DataRow label={t('field.actualEndDate')}>{formatDate(p.actual_end_date)}</DataRow>
                <DataRow label={t('field.beneficiaries')}>{formatNumber(p.beneficiaries)}</DataRow>
                <DataRow label={t('field.status')}>{p.status}</DataRow>
                <DataRow label={t('detail.publicIndicator')}>
                  {underReview ? t('detail.indicatorUnderReview') : t('detail.indicatorNormal')}
                </DataRow>
              </DataGrid>

              {p.description ? (
                <div className="mt-4 border-t border-ink-100 pt-4">
                  <p className="data-label">{t('field.description')}</p>
                  <p className="mt-1 text-sm leading-relaxed text-ink-700">{p.description}</p>
                </div>
              ) : null}

              <p className="mt-4 rounded-md bg-ink-50 px-3 py-2 text-xs leading-relaxed text-ink-600">
                {t('detail.indicatorHelp')}
              </p>
            </CardBody>
          </Card>

          {/* Charts */}
          <div className="grid gap-4 lg:grid-cols-2">
            <SpendingTimelineChart
              data={p.spending_timeline}
              title={t('detail.spendingTimeline')}
              emptyLabel={t('detail.noTimeline')}
              labels={{ spent: t('chart.spent'), allocated: t('chart.allocated') }}
            />
            <ProgressTimelineChart
              data={p.progress_timeline}
              title={t('detail.progressChart')}
              emptyLabel={t('detail.noProgress')}
              labels={{ actual: t('chart.actual'), planned: t('chart.planned') }}
            />
          </div>


          {/* Documents */}
          <Card>
            <CardHeader
              title={t('detail.documents')}
              icon={<FileText className="h-4 w-4" aria-hidden />}
            />
            <CardBody>
              {p.photo_url || p.document_url ? (
                <div className="space-y-4">
                  {p.photo_url ? (
                    <figure>
                      <img
                        src={p.photo_url}
                        alt={t('detail.sitePhotograph')}
                        loading="lazy"
                        className="w-full rounded border border-ink-200 bg-ink-50"
                      />
                      <figcaption className="mt-1.5 text-xs text-ink-500">
                        {t('detail.sitePhotograph')}
                      </figcaption>
                    </figure>
                  ) : null}
                  {p.document_url ? (
                    <a
                      href={p.document_url}
                      target="_blank"
                      rel="noreferrer"
                      className="tap-target inline-flex items-center gap-2 rounded border border-ink-300 px-3 py-2 text-sm font-medium text-ink-800 hover:bg-ink-50"
                    >
                      <FileText className="h-4 w-4" aria-hidden />
                      {t('detail.sanctionDocument')}
                    </a>
                  ) : null}
                </div>
              ) : (
                <div className="flex items-center gap-2 text-sm text-ink-500">
                  <ImageOff className="h-4 w-4" aria-hidden />
                  {t('detail.noDocuments')}
                </div>
              )}
            </CardBody>
          </Card>
        </div>

        {/* Sidebar */}
                <div className="min-w-0 space-y-6">
          <UtilizationDonut
            allocated={p.allocated_amount}
            spent={p.spent_amount}
            title={t('detail.utilizationChart')}
            labels={{ spent: t('chart.spent'), remaining: t('chart.remaining') }}
          />

          <ProjectLocationCard project={p} />

          <Card>
            <CardHeader
              title={t('detail.progressInformation')}
              icon={<CalendarClock className="h-4 w-4" aria-hidden />}
            />
            <CardBody className="space-y-4">
              <ProgressBar
                value={p.progress_percent}
                label={t('field.progress')}
                tone={p.progress_percent >= 100 ? 'success' : 'default'}
              />
              <ProgressBar
                value={p.utilization_percent}
                label={t('field.utilization')}
                tone={p.utilization_percent > 100 ? 'danger' : 'default'}
              />
              <DataGrid columns={2}>
                <DataRow label={t('field.daysRemaining')}>
                  {p.days_remaining === null || p.days_remaining === undefined
                    ? t('common.notRecorded')
                    : `${p.days_remaining} ${t('common.days')}`}
                </DataRow>
                <DataRow label={t('field.overdue')}>
                  {p.is_overdue ? t('common.yes') : t('common.no')}
                </DataRow>
              </DataGrid>
            </CardBody>
          </Card>

          <Card>
            <CardHeader
              title={t('detail.reportIssue')}
              icon={<MessageSquareWarning className="h-4 w-4" aria-hidden />}
            />
            <CardBody>
              {isAuthenticated ? (
                <>
                  <Button onClick={() => setReportOpen(true)} className="w-full">
                    {t('report.title')}
                  </Button>
                  <div className="mt-4">
                    <p className="data-label">{t('detail.myReports')}</p>
                    {myReports.loading ? (
                      <p className="mt-2 text-xs text-ink-500">{t('common.loading')}</p>
                    ) : (myReports.data?.length ?? 0) === 0 ? (
                      <p className="mt-2 text-xs text-ink-500">{t('common.empty')}</p>
                    ) : (
                      <ul className="mt-2 space-y-2">
                        {myReports.data?.map((report) => (
                          <li key={report.id} className="rounded-md border border-ink-200 p-2.5">
                            <div className="flex items-center justify-between gap-2">
                              <span className="text-xs font-medium text-ink-800">{tEnum('reportCategory', report.category)}</span>
                              <Badge tone={report.status === 'Closed' ? 'success' : 'info'}>
                                {report.status}
                              </Badge>
                            </div>
                            <p className="mt-1 text-xs leading-relaxed text-ink-600">
                              {report.description}
                            </p>
                            {report.official_response ? (
                              <p className="mt-2 rounded bg-ink-50 px-2 py-1.5 text-xs text-ink-700">
                                {report.official_response}
                              </p>
                            ) : null}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </>
              ) : (
                <div className="text-sm text-ink-600">
                  {t('detail.reportIssueHint')}
                  <Link
                    to="/login"
                    className="ml-1 font-medium text-ink-800 underline underline-offset-2"
                  >
                    {t('nav.login')}
                  </Link>
                </div>
              )}
            </CardBody>
          </Card>
        </div>
      </div>

      <ReportIssueDialog
        open={reportOpen}
        projectId={projectId}
        onClose={() => setReportOpen(false)}
        onSubmitted={() => setReportMessage(t('report.submitted'))}
      />
    </div>
  )
}
