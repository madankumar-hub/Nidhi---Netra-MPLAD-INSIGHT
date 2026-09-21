import { useState } from 'react'
import { IndianRupee, Plus } from 'lucide-react'
import { adminApi } from '@/api'
import { useMutation } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { Button } from '@/components/ui/Button'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { Modal } from '@/components/ui/Modal'
import { TextInput, TextArea } from '@/components/ui/Field'
import { DataTable } from '@/components/ui/Table'
import type { Column } from '@/components/ui/Table'
import { EmptyState, InlineMessage } from '@/components/ui/States'
import { StatCard } from '@/components/ui/Metrics'
import { SpendingTimelineChart, UtilizationDonut } from '@/components/charts'
import { formatDate, formatLakh, formatPercent, todayIso } from '@/utils/format'
import type { FundUpdate, ProjectAdminDetail } from '@/types'

export function FinancialPanel({
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
  const [released, setReleased] = useState('')
  const [expenditure, setExpenditure] = useState('')
  const [voucher, setVoucher] = useState('')
  const [remarks, setRemarks] = useState('')
  const [validation, setValidation] = useState<string | null>(null)
  const add = useMutation(adminApi.addFundUpdate)

  const submit = async () => {
    const expenditureValue = Number(expenditure)
    const releasedValue = Number(released || expenditure)
    if (!Number.isFinite(expenditureValue) || expenditureValue < 0) {
      setValidation(t('common.required'))
      return
    }
    setValidation(null)
    const created = await add.run(project.id, {
      updated_on: updatedOn,
      released_amount: releasedValue,
      expenditure_amount: expenditureValue,
      voucher_reference: voucher.trim() || undefined,
      remarks: remarks.trim() || undefined,
    })
    if (created) {
      setExpenditure('')
      setReleased('')
      setVoucher('')
      setRemarks('')
      setOpen(false)
      onChanged()
    }
  }

  const columns: Column<FundUpdate>[] = [
    { key: 'date', header: t('field.sanctionDate'), render: (row) => formatDate(row.updated_on) },
    {
      key: 'installment',
      header: 'Installment',
      secondary: true,
      render: (row) => row.installment_no ?? '—',
    },
    {
      key: 'released',
      header: 'Released',
      align: 'right',
      render: (row) => formatLakh(row.released_amount),
    },
    {
      key: 'expenditure',
      header: t('field.spent'),
      align: 'right',
      render: (row) => formatLakh(row.expenditure_amount),
    },
    {
      key: 'cumulative',
      header: 'Cumulative',
      align: 'right',
      secondary: true,
      render: (row) => formatLakh(row.cumulative_spent),
    },
    {
      key: 'voucher',
      header: 'Voucher',
      secondary: true,
      render: (row) => <span className="font-mono text-xs">{row.voucher_reference ?? '—'}</span>,
    },
  ]

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <StatCard label={t('field.allocated')} value={formatLakh(project.allocated_amount)} />
        <StatCard label={t('field.spent')} value={formatLakh(project.spent_amount)} />
        <StatCard label={t('field.remaining')} value={formatLakh(project.remaining_amount)} />
        <StatCard
          label={t('field.utilization')}
          value={formatPercent(project.utilization_percent)}
          tone={project.utilization_percent > 100 ? 'danger' : 'default'}
        />
        <StatCard
          label={t('field.estimatedCost')}
          value={formatLakh(project.estimated_cost)}
          sublabel={
            project.expected_utilization_percent !== null &&
            project.expected_utilization_percent !== undefined
              ? `Expected utilisation ${formatPercent(project.expected_utilization_percent)}`
              : undefined
          }
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <SpendingTimelineChart
            data={project.spending_timeline}
            title={t('detail.spendingTimeline')}
            emptyLabel={t('detail.noTimeline')}
            labels={{ spent: t('chart.spent'), allocated: t('chart.allocated') }}
          />
        </div>
        <UtilizationDonut
          allocated={project.allocated_amount}
          spent={project.spent_amount}
          title={t('detail.utilizationChart')}
          labels={{ spent: t('chart.spent'), remaining: t('chart.remaining') }}
        />
      </div>

      <Card>
        <CardHeader
          title={t('fin.entries')}
          icon={<IndianRupee className="h-4 w-4" aria-hidden />}
          actions={
            canAct ? (
              <Button size="sm" onClick={() => setOpen(true)} icon={<Plus className="h-3.5 w-3.5" aria-hidden />}>
                Record expenditure
              </Button>
            ) : undefined
          }
        />
        <CardBody>
          {project.fund_updates.length === 0 ? (
            <EmptyState title={t('detail.noTimeline')} />
          ) : (
            <DataTable
              columns={columns}
              rows={project.fund_updates}
              rowKey={(row) => row.id}
              caption={t('chart.expenditureEntries')}
            />
          )}
        </CardBody>
      </Card>

      <Modal
        open={open}
        title={t('fin.record')}
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
              label={t('fin.amount')}
              type="number"
              step="0.01"
              min="0"
              required
              error={validation}
              value={expenditure}
              onChange={(event) => setExpenditure(event.target.value)}
            />
            <TextInput
              label={t('fin.released')}
              type="number"
              step="0.01"
              min="0"
              hint={t('fin.releasedHint')}
              value={released}
              onChange={(event) => setReleased(event.target.value)}
            />
          </div>
          <TextInput
            label={t('fin.voucher')}
            value={voucher}
            onChange={(event) => setVoucher(event.target.value)}
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
