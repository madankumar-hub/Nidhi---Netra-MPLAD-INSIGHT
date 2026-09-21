import { useState } from 'react'
import { MessageSquareWarning } from 'lucide-react'
import { adminApi } from '@/api'
import { useApi, useMutation } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { SelectInput, TextArea } from '@/components/ui/Field'
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

export function CitizenReportsPanel({
  projectId,
  canAct,
}: {
  projectId: number
  canAct: boolean
}) {
  const { t, tEnum } = useI18n()
  const [version, setVersion] = useState(0)
  const [editing, setEditing] = useState<number | null>(null)
  const [status, setStatus] = useState<CitizenReportStatus>('Under Review')
  const [response, setResponse] = useState('')

  const list = useApi(
    (signal) => adminApi.listProjectCitizenReports(projectId, signal),
    [projectId, version],
  )
  const triage = useMutation(adminApi.triageCitizenReport)

  const submit = async (id: number) => {
    const result = await triage.run(id, {
      status,
      official_response: response.trim() || undefined,
    })
    if (result) {
      setEditing(null)
      setResponse('')
      setVersion((value) => value + 1)
    }
  }

  return (
    <Card>
      <CardHeader
        title={t('admin.citizenReportsTitle')}
        description={t('admin.citizenReportsSubtitle')}
        icon={<MessageSquareWarning className="h-4 w-4" aria-hidden />}
      />
      <CardBody>
        {list.loading ? (
          <SkeletonRows rows={3} />
        ) : list.error ? (
          <ErrorState error={list.error} onRetry={list.reload} retryLabel={t('common.retry')} />
        ) : (list.data?.length ?? 0) === 0 ? (
          <EmptyState title={t('common.empty')} />
        ) : (
          <ul className="space-y-3">
            {list.data?.map((report) => (
              <li key={report.id} className="rounded-lg border border-ink-200 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone="neutral">{tEnum('reportCategory', report.category)}</Badge>
                    <Badge tone={TONE[report.status]}>{report.status}</Badge>
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

                {canAct ? (
                  editing === report.id ? (
                    <div className="mt-3 space-y-3 rounded-md border border-ink-200 bg-ink-50/60 p-3">
                      {triage.error ? (
                        <InlineMessage tone="warning">{triage.error.message}</InlineMessage>
                      ) : null}
                      <SelectInput
                        label={t('field.status')}
                        value={status}
                        options={CITIZEN_REPORT_STATUSES.map((item) => ({
                          label: item,
                          value: item,
                        }))}
                        onChange={(event) => setStatus(event.target.value as CitizenReportStatus)}
                      />
                      <TextArea
                        label={t('report.officialResponse')}
                        rows={3}
                        value={response}
                        onChange={(event) => setResponse(event.target.value)}
                      />
                      <div className="flex justify-end gap-2">
                        <Button variant="secondary" size="sm" onClick={() => setEditing(null)}>
                          {t('common.cancel')}
                        </Button>
                        <Button size="sm" loading={triage.pending} onClick={() => submit(report.id)}>
                          {t('common.save')}
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <Button
                      variant="secondary"
                      size="sm"
                      className="mt-3"
                      onClick={() => {
                        setEditing(report.id)
                        setStatus(report.status)
                        setResponse(report.official_response ?? '')
                      }}
                    >
                      Triage
                    </Button>
                  )
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  )
}
