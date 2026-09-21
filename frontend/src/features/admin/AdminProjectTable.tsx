import { Link } from 'react-router-dom'
import { Trash2 } from 'lucide-react'
import { Badge, RiskBadge, ReviewStatusBadge, StatusBadge } from '@/components/ui/Badge'
import { DataTable } from '@/components/ui/Table'
import type { Column } from '@/components/ui/Table'
import { ProgressBar } from '@/components/ui/Metrics'
import { useI18n } from '@/i18n'
import { formatDate, formatLakh, formatPercent, truncate } from '@/utils/format'
import type { ProjectAdminSummary } from '@/types'

interface AdminProjectTableProps {
  rows: ProjectAdminSummary[]
  /** Supplied only for roles allowed to delete; the column is hidden without it. */
  onDelete?: (projectId: number) => void
}

export function AdminProjectTable({ rows, onDelete }: AdminProjectTableProps) {
  const { t, tEnum } = useI18n()

  const columns: Column<ProjectAdminSummary>[] = [
    {
      key: 'title',
      header: t('field.title'),
      render: (row) => (
        <div className="min-w-0">
          <Link
            to={`/admin/scheme/${row.id}`}
            className="text-sm font-medium text-ink-900 hover:underline"
          >
            {truncate(row.title, 72)}
          </Link>
          <p className="mt-0.5 text-xs text-ink-500">
            <span className="font-mono">{row.project_code}</span> · {tEnum('district', row.district)} ·{' '}
            {tEnum('category', row.category)}
          </p>
        </div>
      ),
    },
    {
      key: 'mp',
      header: t('field.mp'),
      secondary: true,
      render: (row) => (
        <div>
          <p className="text-sm text-ink-800">{row.mp_name}</p>
          <p className="text-xs text-ink-500">{row.sanction_year}</p>
        </div>
      ),
    },
    {
      key: 'funds',
      header: t('field.allocated'),
      align: 'right',
      render: (row) => (
        <div>
          <p className="text-sm font-medium text-ink-900">{formatLakh(row.allocated_amount)}</p>
          <p className="text-xs text-ink-500">
            {formatLakh(row.spent_amount)} · {formatPercent(row.utilization_percent)}
          </p>
        </div>
      ),
    },
    {
      key: 'progress',
      header: t('field.progress'),
      render: (row) => (
        <div className="w-32">
          <ProgressBar
            value={row.progress_percent}
            target={row.planned_progress_percent ?? undefined}
            showValue
          />
          {row.schedule_variance !== null && row.schedule_variance !== undefined ? (
            <p
              className={`mt-1 text-[11px] tabular-nums ${
                row.schedule_variance < -10 ? 'text-saffron-700' : 'text-ink-500'
              }`}
            >
              {row.schedule_variance >= 0 ? '+' : ''}
              {row.schedule_variance.toFixed(1)} pp vs plan
            </p>
          ) : null}
        </div>
      ),
    },
    {
      key: 'status',
      header: t('field.status'),
      render: (row) => (
        <div className="space-y-1.5">
          <StatusBadge status={row.status} />
          {row.is_overdue ? <Badge tone="danger">{t('field.overdue')}</Badge> : null}
        </div>
      ),
    },
    {
      key: 'review',
      header: t('field.reviewStatus'),
      secondary: true,
      render: (row) => (
        <div className="space-y-1.5">
          <ReviewStatusBadge status={row.review_status} />
          <p className="text-[11px] text-ink-500">
            {row.last_reviewed_at ? formatDate(row.last_reviewed_at) : t('admin.awaitingFirstReview')}
          </p>
        </div>
      ),
    },
    {
      key: 'risk',
      header: t('risk.level'),
      render: (row) =>
        row.risk_level ? (
          <div className="space-y-1.5">
            <RiskBadge level={row.risk_level} score={row.risk_score} />
            <p className="text-[11px] text-ink-500">
              {row.open_risk_factors} indicators · {row.open_mitigations} open actions
            </p>
          </div>
        ) : (
          <span className="text-xs text-ink-400">{t('common.notRecorded')}</span>
        ),
    },
    ...(onDelete
      ? [
          {
            key: 'actions',
            header: '',
            width: '1%',
            render: (row: ProjectAdminSummary) => (
              <button
                type="button"
                onClick={() => onDelete(row.id)}
                title={t('admin.deleteWork')}
                aria-label={`${t('admin.deleteWork')}: ${row.title}`}
                className="tap-target inline-flex items-center justify-center rounded text-ink-500 hover:bg-[#fbe3e3] hover:text-[#6d1414]"
              >
                <Trash2 className="h-4 w-4" aria-hidden />
              </button>
            ),
          },
        ]
      : []),
  ]

  return (
    <DataTable
      columns={columns}
      rows={rows}
      rowKey={(row) => row.id}
      caption={t('admin.projectsTitle')}
      renderCard={(row) => (
        <article className="surface p-4">
          <div className="flex items-start justify-between gap-2">
            <span className="font-mono text-[11px] text-ink-500">{row.project_code}</span>
            <StatusBadge status={row.status} />
          </div>
          <Link
            to={`/admin/scheme/${row.id}`}
            className="mt-2 block text-sm font-semibold text-ink-900 hover:underline"
          >
            {truncate(row.title, 90)}
          </Link>
          <p className="mt-1 text-xs text-ink-500">
            {tEnum('district', row.district)} · {tEnum('category', row.category)} · {row.mp_name}
          </p>
          <div className="mt-3 grid grid-cols-2 gap-3 border-t border-ink-100 pt-3 text-xs">
            <div>
              <p className="data-label">{t('field.allocated')}</p>
              <p className="mt-0.5 font-semibold text-ink-900">{formatLakh(row.allocated_amount)}</p>
            </div>
            <div>
              <p className="data-label">{t('field.spent')}</p>
              <p className="mt-0.5 font-semibold text-ink-900">{formatLakh(row.spent_amount)}</p>
            </div>
          </div>
          <div className="mt-3">
            <ProgressBar value={row.progress_percent} label={t('field.progress')} />
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <ReviewStatusBadge status={row.review_status} />
            {row.risk_level ? <RiskBadge level={row.risk_level} score={row.risk_score} /> : null}
          </div>
        </article>
      )}
    />
  )
}
