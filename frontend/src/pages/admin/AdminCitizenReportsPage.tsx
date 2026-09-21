import { useState } from 'react'
import { Link } from 'react-router-dom'
import { MessageSquareWarning } from 'lucide-react'
import { adminApi } from '@/api'
import { useApi, useMutation } from '@/hooks/useApi'
import { useAuth } from '@/features/auth/AuthContext'
import { useI18n } from '@/i18n'
import { PageHeader } from '@/components/layout/PageHeader'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardBody } from '@/components/ui/Card'
import { SelectInput } from '@/components/ui/Field'
import { SkeletonRows } from '@/components/ui/Spinner'
import { EmptyState, ErrorState, InlineMessage } from '@/components/ui/States'
import { formatDateTime } from '@/utils/format'
import { CITIZEN_REPORT_STATUSES } from '@/utils/constants'
import type { CitizenReportStatus } from '@/types'

const TONE: Record<CitizenReportStatus, 'neutral' | 'info' | 'warning' | 'success'> = {
  Submitted: 'warning',
  'Under Review': 'info',
  'Action Taken': 'success',
  Closed: 'neutral',
}

export function AdminCitizenReportsPage() {
  const { t, tEnum } = useI18n()
  const { isReviewer } = useAuth()
  const [filter, setFilter] = useState<CitizenReportStatus | ''>('')
  const [version, setVersion] = useState(0)

  const reports = useApi(
    (signal) => adminApi.listCitizenReports({ status: filter }, signal),
    [filter, version],
  )
  const triage = useMutation(adminApi.triageCitizenReport)

  const advance = async (id: number, status: CitizenReportStatus) => {
    const result = await triage.run(id, { status })
    if (result) setVersion((value) => value + 1)
  }

  return (
    <div>
      <PageHeader
        title={t('admin.citizenReportsTitle')}
        description={t('admin.citizenReportsSubtitle')}
      />

      <div className="mb-4 max-w-xs">
        <SelectInput
          label={t('field.status')}
          value={filter}
          placeholder={t('common.all')}
          options={CITIZEN_REPORT_STATUSES.map((item) => ({ label: item, value: item }))}
          onChange={(event) => setFilter(event.target.value as CitizenReportStatus | '')}
        />
      </div>

      {triage.error ? (
        <div className="mb-4">
          <InlineMessage tone="warning">{triage.error.message}</InlineMessage>
        </div>
      ) : null}

      <Card>
        <CardBody>
          {reports.loading ? (
            <SkeletonRows rows={6} />
          ) : reports.error ? (
            <ErrorState error={reports.error} onRetry={reports.reload} retryLabel={t('common.retry')} />
          ) : (reports.data?.length ?? 0) === 0 ? (
            <EmptyState
              title={t('common.empty')}
              icon={<MessageSquareWarning className="h-8 w-8" aria-hidden />}
            />
          ) : (
            <ul className="space-y-3">
              {reports.data?.map((report) => (
                <li key={report.id} className="rounded-lg border border-ink-200 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone="neutral">{tEnum('reportCategory', report.category)}</Badge>
                      <Badge tone={TONE[report.status]}>{report.status}</Badge>
                      <Link
                        to={`/admin/scheme/${report.project_id}`}
                        className="text-sm font-medium text-ink-800 hover:underline"
                      >
                        Work #{report.project_id}
                      </Link>
                    </div>
                    <span className="text-xs text-ink-500">{formatDateTime(report.created_at)}</span>
                  </div>
                  <p className="mt-2 text-sm leading-relaxed text-ink-800">{report.description}</p>
                  <p className="mt-1.5 text-xs text-ink-500">{t('report.filedBy')} {report.reporter_name}</p>
                  {report.official_response ? (
                    <p className="mt-2 rounded bg-ink-50 px-2.5 py-2 text-xs leading-relaxed text-ink-700">
                      <span className="font-semibold">{t('report.officialResponse')}: </span>
                      {report.official_response}
                    </p>
                  ) : null}

                  {isReviewer && report.status !== 'Closed' ? (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {CITIZEN_REPORT_STATUSES.filter((status) => status !== report.status).map(
                        (status) => (
                          <Button
                            key={status}
                            variant="secondary"
                            size="sm"
                            loading={triage.pending}
                            onClick={() => advance(report.id, status)}
                          >
                            {status}
                          </Button>
                        ),
                      )}
                    </div>
                  ) : null}
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>
    </div>
  )
}
