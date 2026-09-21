import { projectsApi } from '@/api'
import { useApi } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { PageHeader } from '@/components/layout/PageHeader'
import { StatCard } from '@/components/ui/Metrics'
import { Spinner } from '@/components/ui/Spinner'
import { ErrorState } from '@/components/ui/States'
import { AllocationByDimensionChart, StateDonutChart, TrendChart } from '@/components/charts'
import { formatLakh, formatNumber, formatPercent } from '@/utils/format'

/** Public statistics - aggregates only, no internal risk information. */
export function StatisticsPage() {
  const { t } = useI18n()
  const stats = useApi((signal) => projectsApi.getPublicStatistics(signal), [])

  if (stats.loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Spinner label={t('common.loading')} />
      </div>
    )
  }

  if (stats.error || !stats.data) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-16">
        <ErrorState error={stats.error} onRetry={stats.reload} retryLabel={t('common.retry')} />
      </div>
    )
  }

  const { summary, by_status, by_category, by_district, yearly_trend } = stats.data

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <PageHeader title={t('nav.statistics')} description={t('home.statsTitle')} />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <StatCard label={t('admin.totalProjects')} value={formatNumber(summary.total_projects)} />
        <StatCard
          label={t('admin.completedProjects')}
          value={formatNumber(summary.completed_projects)}
          tone="success"
        />
        <StatCard label={t('admin.activeProjects')} value={formatNumber(summary.ongoing_projects)} />
        <StatCard
          label={t('admin.totalAllocation')}
          value={formatLakh(summary.total_allocated, { compact: true })}
        />
        <StatCard
          label={t('admin.utilization')}
          value={formatPercent(summary.utilization_percent)}
          sublabel={formatLakh(summary.total_spent, { compact: true })}
        />
      </div>

      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <StateDonutChart
          data={by_status}
          title={t('chart.byStatus')}
          emptyLabel={t('chart.noData')}
        />
        <TrendChart
          data={yearly_trend}
          title={t('chart.yearlyTrend')}
          emptyLabel={t('chart.noData')}
          labels={{ allocated: t('chart.allocated'), spent: t('chart.spent') }}
        />
        <AllocationByDimensionChart
          data={by_category}
          title={t('chart.byCategory')}
          emptyLabel={t('chart.noData')}
          labels={{ allocated: t('chart.allocated'), spent: t('chart.spent') }}
          height={420}
          family="category"
        />
        <AllocationByDimensionChart
          data={by_district}
          title={t('chart.byDistrict')}
          emptyLabel={t('chart.noData')}
          labels={{ allocated: t('chart.allocated'), spent: t('chart.spent') }}
          height={420}
          family="district"
        />
      </div>
    </div>
  )
}
