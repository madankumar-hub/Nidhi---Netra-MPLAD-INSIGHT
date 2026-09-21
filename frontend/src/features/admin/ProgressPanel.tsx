import { useState } from 'react'
import { Plus, TrendingUp } from 'lucide-react'
import { adminApi } from '@/api'
import { useMutation } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { Button } from '@/components/ui/Button'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { Modal } from '@/components/ui/Modal'
import { TextArea, TextInput } from '@/components/ui/Field'
import { DataTable } from '@/components/ui/Table'
import type { Column } from '@/components/ui/Table'
import { EmptyState, InlineMessage } from '@/components/ui/States'
import { ProgressBar, StatCard } from '@/components/ui/Metrics'
import { ProgressTimelineChart } from '@/components/charts'
import { formatDate, formatPercent, todayIso } from '@/utils/format'
import type { ProgressUpdate, ProjectAdminDetail } from '@/types'

export function ProgressPanel({
  project,
  canAct,
  onChanged,
}: {
  project: ProjectAdminDetail
  canAct: boolean
  onChanged: () => void
}) {
  const { t } = useI18n()
  const [open, setOpen] = useState(false)
  const [updatedOn, setUpdatedOn] = useState(todayIso())
  const [progress, setProgress] = useState(String(project.progress_percent))
  const [planned, setPlanned] = useState('')
  const [milestone, setMilestone] = useState('')
  const [remarks, setRemarks] = useState('')
  const [validation, setValidation] = useState<string | null>(null)
  const add = useMutation(adminApi.addProgressUpdate)

  const submit = async () => {
    const value = Number(progress)
    if (!Number.isFinite(value) || value < 0 || value > 100) {
      setValidation('Enter a value between 0 and 100.')
      return
    }
    setValidation(null)
    const created = await add.run(project.id, {
      updated_on: updatedOn,
      progress_percent: value,
      planned_progress_percent: planned ? Number(planned) : undefined,
      milestone: milestone.trim() || undefined,
      remarks: remarks.trim() || undefined,
    })
    if (created) {
      setMilestone('')
      setRemarks('')
      setOpen(false)
      onChanged()
    }
  }

  const columns: Column<ProgressUpdate>[] = [
    { key: 'date', header: 'Date', render: (row) => formatDate(row.updated_on) },
    {
      key: 'progress',
      header: t('field.progress'),
      align: 'right',
      render: (row) => formatPercent(row.progress_percent),
    },
    {
      key: 'planned',
      header: t('field.plannedProgress'),
      align: 'right',
      secondary: true,
      render: (row) =>
        row.planned_progress_percent === null || row.planned_progress_percent === undefined
          ? '—'
          : formatPercent(row.planned_progress_percent),
    },
    { key: 'milestone', header: 'Milestone', render: (row) => row.milestone ?? '—' },
    { key: 'remarks', header: 'Remarks', secondary: true, render: (row) => row.remarks ?? '—' },
  ]

  const variance = project.schedule_variance

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard label={t('field.progress')} value={formatPercent(project.progress_percent)} />
        <StatCard
          label={t('prog.expected')}
          value={formatPercent(project.expected_progress_percent)}
          sublabel={t('prog.expectedHint')}
        />
        <StatCard
          label={t('prog.variance')}
          value={
            variance === null || variance === undefined
              ? '—'
              : `${variance >= 0 ? '+' : ''}${variance.toFixed(1)} pp`
          }
          tone={variance !== null && variance !== undefined && variance < -10 ? 'danger' : 'default'}
        />
        <StatCard
          label={t('field.daysRemaining')}
          value={
            project.days_remaining === null || project.days_remaining === undefined
              ? '—'
              : `${project.days_remaining}`
          }
          tone={project.is_overdue ? 'danger' : 'default'}
          sublabel={project.is_overdue ? t('field.overdue') : undefined}
        />
      </div>

      <Card>
        <CardBody>
          <ProgressBar
            value={project.progress_percent}
            target={project.expected_progress_percent ?? undefined}
            label={`${t('field.progress')} vs ${t('field.plannedProgress').toLowerCase()}`}
          />
        </CardBody>
      </Card>

      <ProgressTimelineChart
        data={project.progress_timeline}
        title={t('detail.progressChart')}
        emptyLabel={t('detail.noProgress')}
        labels={{ actual: t('chart.actual'), planned: t('chart.planned') }}
      />

      <Card>
        <CardHeader
          title={t('prog.entries')}
          icon={<TrendingUp className="h-4 w-4" aria-hidden />}
          actions={
            canAct ? (
              <Button size="sm" onClick={() => setOpen(true)} icon={<Plus className="h-3.5 w-3.5" aria-hidden />}>
                Record progress
              </Button>
            ) : undefined
          }
        />
        <CardBody>
          {project.progress_updates.length === 0 ? (
            <EmptyState title={t('detail.noProgress')} />
          ) : (
            <DataTable
              columns={columns}
              rows={project.progress_updates}
              rowKey={(row) => row.id}
              caption={t('chart.progressEntries')}
            />
          )}
        </CardBody>
      </Card>

      <Modal
        open={open}
        title={t('prog.record')}
        onClose={() => setOpen(false)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setOpen(false)}>
              {t('common.cancel')}
            </Button>
            <Button onClick={submit} loading={add.pending}>
              {t('common.save')}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {add.error ? <InlineMessage tone="warning">{add.error.message}</InlineMessage> : null}
          <TextInput
            label={t('fin.date')}
            type="date"
            required
            value={updatedOn}
            onChange={(event) => setUpdatedOn(event.target.value)}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <TextInput
              label={`${t('field.progress')} (%)`}
              type="number"
              min="0"
              max="100"
              step="0.1"
              required
              error={validation}
              value={progress}
              onChange={(event) => setProgress(event.target.value)}
            />
            <TextInput
              label={`${t('field.plannedProgress')} (%)`}
              type="number"
              min="0"
              max="100"
              step="0.1"
              value={planned}
              onChange={(event) => setPlanned(event.target.value)}
            />
          </div>
          <TextInput
            label={t('prog.milestone')}
            value={milestone}
            onChange={(event) => setMilestone(event.target.value)}
          />
          <TextArea
            label={t('admin.remarks')}
            rows={2}
            value={remarks}
            onChange={(event) => setRemarks(event.target.value)}
          />
        </div>
      </Modal>
    </div>
  )
}
