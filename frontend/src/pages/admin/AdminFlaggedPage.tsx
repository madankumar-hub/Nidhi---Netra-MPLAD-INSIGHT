import { useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle } from 'lucide-react'
import { riskApi } from '@/api'
import { useApi } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { ExportMenu } from '@/features/admin/ExportMenu'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardBody } from '@/components/ui/Card'
import { RiskBadge } from '@/components/ui/Badge'
import { SelectInput } from '@/components/ui/Field'
import { DataTable } from '@/components/ui/Table'
import type { Column } from '@/components/ui/Table'
import { SkeletonRows } from '@/components/ui/Spinner'
import { EmptyState, ErrorState } from '@/components/ui/States'
import { formatLakh, formatPercent, truncate } from '@/utils/format'
import type { FlaggedProject } from '@/types'

const THRESHOLDS = [
  { label: 'Score 25 and above', value: '25' },
  { label: 'Score 50 and above', value: '50' },
  { label: 'Score 75 and above', value: '75' },
]

export function AdminFlaggedPage() {
  const { t, tEnum } = useI18n()
  const [minScore, setMinScore] = useState('25')
  const flagged = useApi(
    (signal) => riskApi.listFlaggedProjects(100, Number(minScore), signal),
    [minScore],
  )

  const columns: Column<FlaggedProject>[] = [
    {
      key: 'title',
      header: t('field.title'),
      render: (row) => (
        <div>
          <Link
            to={`/admin/scheme/${row.project_id}`}
            className="text-sm font-medium text-ink-900 hover:underline"
          >
            {truncate(row.title, 70)}
          </Link>
          <p className="mt-0.5 text-xs text-ink-500">
            <span className="font-mono">{row.project_code}</span> · {tEnum('district', row.district)} ·{' '}
            {tEnum('category', row.category)}
          </p>
        </div>
      ),
    },
    { key: 'mp', header: t('field.mp'), secondary: true, render: (row) => row.mp_name },
    {
      key: 'funds',
      header: t('field.allocated'),
      align: 'right',
      render: (row) => (
        <div>
          <p className="text-sm text-ink-900">{formatLakh(row.allocated_amount)}</p>
          <p className="text-xs text-ink-500">{formatLakh(row.spent_amount)} spent</p>
        </div>
      ),
    },
    {
      key: 'progress',
      header: t('field.progress'),
      align: 'right',
      render: (row) => formatPercent(row.progress_percent),
    },
    {
      key: 'risk',
      header: t('risk.level'),
      render: (row) => <RiskBadge level={row.risk_level} score={row.risk_score} />,
    },
    {
      key: 'factors',
      header: t('risk.factors'),
      secondary: true,
      render: (row) => (
        <ul className="list-inside list-disc text-xs text-ink-600">
          {row.top_factors.map((factor) => (
            <li key={factor}>{truncate(factor, 60)}</li>
          ))}
        </ul>
      ),
    },
    { key: 'review', header: t('field.reviewStatus'), render: (row) => row.review_status },
  ]

  return (
    <div>
      <PageHeader
        title={t('admin.flaggedTitle')}
        description={t('admin.flaggedSubtitle')}
        actions={<ExportMenu params={{ flagged_only: true }} />}
      />


      <div className="mb-4 max-w-xs">
        <SelectInput
          label={t('admin.minRiskScore')}
          value={minScore}
          options={THRESHOLDS}
          onChange={(event) => setMinScore(event.target.value)}
        />
      </div>

      <Card>
        <CardBody>
          {flagged.loading ? (
            <SkeletonRows rows={8} />
          ) : flagged.error ? (
            <ErrorState error={flagged.error} onRetry={flagged.reload} retryLabel={t('common.retry')} />
          ) : (flagged.data?.length ?? 0) === 0 ? (
            <EmptyState
              title={t('common.empty')}
              description={t('empty.noFlagged')}
              icon={<AlertTriangle className="h-8 w-8" aria-hidden />}
            />
          ) : (
            <DataTable
              columns={columns}
              rows={flagged.data ?? []}
              rowKey={(row) => row.project_id}
              caption={t('admin.flaggedTitle')}
              renderCard={(row) => (
                <article className="surface p-4">
                  <div className="flex items-start justify-between gap-2">
                    <span className="font-mono text-[11px] text-ink-500">{row.project_code}</span>
                    <RiskBadge level={row.risk_level} score={row.risk_score} />
                  </div>
                  <Link
                    to={`/admin/scheme/${row.project_id}`}
                    className="mt-2 block text-sm font-semibold text-ink-900 hover:underline"
                  >
                    {truncate(row.title, 90)}
                  </Link>
                  <p className="mt-1 text-xs text-ink-500">
                    {tEnum('district', row.district)} · {tEnum('category', row.category)}
                  </p>
                  <ul className="mt-2 list-inside list-disc text-xs text-ink-600">
                    {row.top_factors.map((factor) => (
                      <li key={factor}>{factor}</li>
                    ))}
                  </ul>
                </article>
              )}
            />
          )}
        </CardBody>
      </Card>
    </div>
  )
}
