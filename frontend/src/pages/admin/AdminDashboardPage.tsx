import { Link } from 'react-router-dom'
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ClipboardList,
  Clock,
  FolderOpen,
  IndianRupee,
  ListChecks,
  MessageSquareWarning,
  TrendingUp,
} from 'lucide-react'
import { adminApi, riskApi } from '@/api'
import { useApi } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { PageHeader } from '@/components/layout/PageHeader'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { RiskBadge } from '@/components/ui/Badge'
import { StatCard } from '@/components/ui/Metrics'
import { SkeletonRows, Spinner } from '@/components/ui/Spinner'
import { EmptyState, ErrorState } from '@/components/ui/States'
import { ActivityTimeline } from '@/features/admin/ActivityTimeline'
import { StateDonutChart, TrendChart } from '@/components/charts'
import { formatLakh, formatNumber, formatPercent, truncate } from '@/utils/format'

export function AdminDashboardPage() {
  const { t, tEnum } = useI18n()
  const analytics = useApi((signal) => adminApi.getAnalytics(signal), [])
  const flagged = useApi((signal) => riskApi.listFlaggedProjects(8, 35, signal), [])
  const activity = useApi((signal) => adminApi.listRecentActivity(12, signal), [])

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

  const s = analytics.data.summary

  return (
    <div>
      <PageHeader title={t('admin.dashboardTitle')} description={t('admin.dashboardSubtitle')} />

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4 xl:grid-cols-5">
        <StatCard
          label={t('admin.totalProjects')}
          value={formatNumber(s.total_projects)}
          icon={<FolderOpen className="h-4 w-4" aria-hidden />}
          to="/admin/projects"
        />
        <StatCard
          label={t('admin.activeProjects')}
          value={formatNumber(s.active_projects)}
          icon={<TrendingUp className="h-4 w-4" aria-hidden />}
        />
        <StatCard
          label={t('admin.completedProjects')}
          value={formatNumber(s.completed_projects)}
          icon={<CheckCircle2 className="h-4 w-4" aria-hidden />}
          tone="success"
        />
        <StatCard
          label={t('admin.delayedProjects')}
          value={formatNumber(s.delayed_projects)}
          icon={<Clock className="h-4 w-4" aria-hidden />}
          tone="danger"
          to="/admin/delayed"
        />
        <StatCard
          label={t('admin.pendingReview')}
          value={formatNumber(s.pending_review_projects)}
          icon={<ClipboardList className="h-4 w-4" aria-hidden />}
          tone="warning"
          to="/admin/reviews"
        />
      </div>

      <div className="mt-3 grid grid-cols-2 gap-3 lg:grid-cols-4 xl:grid-cols-5">
        <StatCard
          label={t('admin.openRisks')}
          value={formatNumber(s.projects_with_open_risks)}
          icon={<AlertTriangle className="h-4 w-4" aria-hidden />}
          to="/admin/flagged"
        />
        <StatCard
          label={t('admin.criticalRisk')}
          value={formatNumber(s.critical_risk_projects)}
          sublabel={`${formatNumber(s.high_risk_projects)} ${t('admin.highRisk').toLowerCase()}`}
          tone="danger"
          to="/admin/flagged"
        />
        <StatCard
          label={t('admin.openMitigations')}
          value={formatNumber(s.open_mitigations)}
          icon={<ListChecks className="h-4 w-4" aria-hidden />}
        />
        <StatCard
          label={t('admin.overdue')}
          value={formatNumber(s.overdue_projects)}
          tone="warning"
        />
        <StatCard
          label={t('admin.citizenReportsOpen')}
          value={formatNumber(s.citizen_reports_open)}
          icon={<MessageSquareWarning className="h-4 w-4" aria-hidden />}
          to="/admin/citizen-reports"
        />
      </div>

      <div className="mt-3 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard
          label={t('admin.totalAllocation')}
          value={formatLakh(s.total_allocated, { compact: true })}
          icon={<IndianRupee className="h-4 w-4" aria-hidden />}
        />
        <StatCard
          label={t('admin.totalExpenditure')}
          value={formatLakh(s.total_spent, { compact: true })}
          sublabel={`${formatLakh(s.total_remaining, { compact: true })} ${t('chart.remaining').toLowerCase()}`}
        />
        <StatCard label={t('admin.utilization')} value={formatPercent(s.utilization_percent)} />
        <StatCard
          label={t('admin.averageProgress')}
          value={formatPercent(s.average_progress)}
          sublabel={`${t('admin.averageRisk')}: ${s.average_risk_score.toFixed(1)}`}
        />
      </div>

      <div className="mt-6 grid gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <TrendChart
            data={analytics.data.yearly_trend}
            title={t('chart.yearlyTrend')}
            emptyLabel={t('chart.noData')}
            labels={{ allocated: t('chart.allocated'), spent: t('chart.spent') }}
            height={300}
          />
        </div>
        <StateDonutChart
          data={analytics.data.by_status}
          title={t('chart.byStatus')}
          emptyLabel={t('chart.noData')}
          height={300}
        />
      </div>

      <div className="mt-6 grid gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader
            title={t('admin.flaggedTitle')}
            description={t('admin.flaggedSubtitle')}
            icon={<AlertTriangle className="h-4 w-4" aria-hidden />}
            actions={
              <Link
                to="/admin/flagged"
                className="text-sm font-medium text-ink-700 underline-offset-2 hover:underline"
              >
                {t('home.viewAll')}
              </Link>
            }
          />
          <CardBody>
            {flagged.loading ? (
              <SkeletonRows rows={5} />
            ) : flagged.error ? (
              <ErrorState error={flagged.error} onRetry={flagged.reload} retryLabel={t('common.retry')} />
            ) : (flagged.data?.length ?? 0) === 0 ? (
              <EmptyState title={t('common.empty')} />
            ) : (
              <ul className="divide-y divide-ink-100">
                {flagged.data?.map((item) => (
                  <li key={item.project_id} className="py-3 first:pt-0 last:pb-0">
                    <div className="flex flex-wrap items-start justify-between gap-2">
                      <div className="min-w-0">
                        <Link
                          to={`/admin/scheme/${item.project_id}`}
                          className="text-sm font-medium text-ink-900 hover:underline"
                        >
                          {truncate(item.title, 80)}
                        </Link>
                        <p className="mt-0.5 text-xs text-ink-500">
                          <span className="font-mono">{item.project_code}</span> ·{' '}
                          {tEnum('district', item.district)} · {tEnum('category', item.category)}
                        </p>
                      </div>
                      <RiskBadge level={item.risk_level} score={item.risk_score} />
                    </div>
                    {item.top_factors.length > 0 ? (
                      <ul className="mt-1.5 list-inside list-disc text-xs text-ink-600">
                        {item.top_factors.map((factor) => (
                          <li key={factor}>{factor}</li>
                        ))}
                      </ul>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader
            title={t('admin.recentActivity')}
            icon={<Activity className="h-4 w-4" aria-hidden />}
            actions={
              <Link
                to="/admin/activity"
                className="text-sm font-medium text-ink-700 underline-offset-2 hover:underline"
              >
                {t('home.viewAll')}
              </Link>
            }
          />
          <CardBody>
            {activity.loading ? (
              <SkeletonRows rows={5} />
            ) : activity.error ? (
              <ErrorState error={activity.error} onRetry={activity.reload} retryLabel={t('common.retry')} />
            ) : (
              <ActivityTimeline entries={activity.data ?? []} showProject />
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
