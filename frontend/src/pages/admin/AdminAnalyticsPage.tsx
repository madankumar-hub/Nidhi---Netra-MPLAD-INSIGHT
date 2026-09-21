import { RefreshCw } from 'lucide-react'
import { adminApi, riskApi } from '@/api'
import { useApi, useMutation } from '@/hooks/useApi'
import { useAuth } from '@/features/auth/AuthContext'
import { useI18n } from '@/i18n'
import { PageHeader } from '@/components/layout/PageHeader'
import { Button } from '@/components/ui/Button'
import { StatCard } from '@/components/ui/Metrics'
import { Spinner } from '@/components/ui/Spinner'
import { ErrorState, InlineMessage } from '@/components/ui/States'
import {
  AllocationByDimensionChart,
  CountBarChart,
  StateBarChart,
  StateDonutChart,
  TrendChart,
} from '@/components/charts'
import { RiskEngineCard } from '@/features/risk/RiskEngineCard'
import { formatDateTime, formatLakh, formatNumber, formatPercent } from '@/utils/format'

export function AdminAnalyticsPage() {
  const { t } = useI18n()
  const { isReviewer } = useAuth()
  const analytics = useApi((signal) => adminApi.getAnalytics(signal), [])
  const recompute = useMutation(riskApi.recomputeAllRisk)

  if (analytics.loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Spinner label={t('common.loading')} />
      </div>
    )
  }

  if (analytics.error || !analytics.data) {
    return <ErrorState error={analytics.error} onRetry={analytics.reload} retryLabel={t('common.retry')} />
  }

  const a = analytics.data
  const s = a.summary

  return (
    <div>
      <PageHeader
        title={t('admin.analyticsTitle')}
        description={t('admin.analyticsSubtitle')}
        actions={
          <>
            <Button
              variant="secondary"
              onClick={analytics.reload}
              icon={<RefreshCw className="h-4 w-4" aria-hidden />}
            >
              {t('common.refresh')}
            </Button>
            {isReviewer ? (
              <Button
                loading={recompute.pending}
                onClick={async () => {
                  const result = await recompute.run()
                  if (result) analytics.reload()
                }}
              >
                {t('admin.recomputeAll')}
              </Button>
            ) : null}
          </>
        }
      />

      {recompute.error ? (
        <div className="mb-4">
          <InlineMessage tone="warning">{recompute.error.message}</InlineMessage>
        </div>
      ) : null}

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4 xl:grid-cols-6">
        <StatCard label={t('admin.totalProjects')} value={formatNumber(s.total_projects)} />
        <StatCard
          label={t('admin.totalAllocation')}
          value={formatLakh(s.total_allocated, { compact: true })}
        />
        <StatCard
          label={t('admin.totalExpenditure')}
          value={formatLakh(s.total_spent, { compact: true })}
        />
        <StatCard label={t('admin.utilization')} value={formatPercent(s.utilization_percent)} />
        <StatCard label={t('admin.averageProgress')} value={formatPercent(s.average_progress)} />
        <StatCard label={t('admin.averageRisk')} value={s.average_risk_score.toFixed(1)} />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <StateBarChart
            data={a.by_risk_level}
            title={t('chart.riskDistribution')}
            emptyLabel={t('chart.noData')}
            seriesLabel={t('chart.works')}
            height={260}
            family="riskLevel"
          />
        </div>
        <RiskEngineCard />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <StateDonutChart data={a.by_status} title={t('chart.byStatus')} emptyLabel={t('chart.noData')} />
        <StateBarChart
          data={a.by_review_status}
          title={t('chart.reviewStatus')}
          emptyLabel={t('chart.noData')}
          seriesLabel={t('chart.works')}
          family="reviewStatus"
        />
        <CountBarChart
          data={a.risk_category_distribution}
          title={t('chart.riskCategories')}
          emptyLabel={t('chart.noData')}
          seriesLabel={t('chart.indicators')}
          family="riskCategory"
          horizontal
          height={320}
        />
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <CountBarChart
          data={a.progress_distribution}
          title={t('chart.progressDistribution')}
          emptyLabel={t('chart.noData')}
          seriesLabel={t('chart.works')}
        />
        <CountBarChart
          data={a.utilization_distribution}
          title={t('chart.utilizationDistribution')}
          emptyLabel={t('chart.noData')}
          seriesLabel={t('chart.works')}
          family="bucket"
        />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <TrendChart
          data={a.yearly_trend}
          title={t('chart.yearlyTrend')}
          emptyLabel={t('chart.noData')}
          labels={{ allocated: t('chart.allocated'), spent: t('chart.spent') }}
          height={320}
        />
        <TrendChart
          data={a.spending_trend}
          title={t('chart.spendingTrend')}
          emptyLabel={t('chart.noData')}
          labels={{ allocated: t('chart.released'), spent: t('chart.spent') }}
          height={320}
          formatPeriodLabel
        />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-2">
        <AllocationByDimensionChart
          data={a.by_category}
          title={t('chart.byCategory')}
          emptyLabel={t('chart.noData')}
          labels={{ allocated: t('chart.allocated'), spent: t('chart.spent') }}
          height={460}
          family="category"
        />
        <AllocationByDimensionChart
          data={a.by_district}
          title={t('chart.byDistrict')}
          emptyLabel={t('chart.noData')}
          labels={{ allocated: t('chart.allocated'), spent: t('chart.spent') }}
          height={460}
          family="district"
        />
        <AllocationByDimensionChart
          data={a.by_agency}
          title={t('chart.byAgency')}
          emptyLabel={t('chart.noData')}
          labels={{ allocated: t('chart.allocated'), spent: t('chart.spent') }}
          height={360}
          family="agency"
        />
        <AllocationByDimensionChart
          data={a.by_mp}
          title={t('chart.byMp')}
          emptyLabel={t('chart.noData')}
          labels={{ allocated: t('chart.allocated'), spent: t('chart.spent') }}
          height={360}
        />
      </div>

      <div className="mt-4">
        <CountBarChart
          data={a.top_risk_factors}
          title={t('chart.topFactors')}
          emptyLabel={t('chart.noData')}
          seriesLabel={t('chart.occurrences')}
          family="riskFactorTitle"
          horizontal
          height={360}
        />
      </div>

      <p className="mt-4 text-xs text-ink-500">
        {t('admin.analyticsSubtitle')} · {t('chart.generatedAt')}{' '}
        {formatDateTime(a.generated_at)}
      </p>
    </div>
  )
}
