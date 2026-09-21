import { Link } from 'react-router-dom'
import {
  ArrowRight,
  BarChart3,
  FileSearch,
  IndianRupee,
  LineChart,
  MessageSquareWarning,
} from 'lucide-react'
import { projectsApi } from '@/api'
import { useApi } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { ProjectCard } from '@/features/citizen/ProjectCard'
import { Button } from '@/components/ui/Button'
import { SkeletonCards, Spinner } from '@/components/ui/Spinner'
import { EmptyState, ErrorState } from '@/components/ui/States'
import { StatCard } from '@/components/ui/Metrics'
import { formatLakh, formatNumber, formatPercent } from '@/utils/format'

export function HomePage() {
  const { t } = useI18n()
  const stats = useApi((signal) => projectsApi.getPublicStatistics(signal), [])
  const recent = useApi(
    (signal) =>
      projectsApi.listPublicProjects({ page: 1, page_size: 6, sort_by: 'updated_at' }, signal),
    [],
  )

  const summary = stats.data?.summary

  const features = [
    { icon: FileSearch, title: t('home.how1Title'), body: t('home.how1Body') },
    { icon: IndianRupee, title: t('home.how2Title'), body: t('home.how2Body') },
    { icon: LineChart, title: t('home.how3Title'), body: t('home.how3Body') },
    { icon: MessageSquareWarning, title: t('home.how4Title'), body: t('home.how4Body') },
  ]

  return (
    <div>
      <section className="border-b border-ink-200 bg-ink-900">
        <div className="mx-auto max-w-7xl px-4 py-12 sm:py-16">
          <div className="max-w-3xl">
            <p className="text-xs font-semibold uppercase tracking-widest text-saffron-300">
              {t('app.tagline')}
            </p>
            <h1 className="mt-3 text-2xl font-bold leading-tight text-white sm:text-4xl">
              {t('home.heroTitle')}
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-relaxed text-ink-200 sm:text-base">
              {t('home.heroSubtitle')}
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <Link to="/projects">
                <Button variant="accent" icon={<FileSearch className="h-4 w-4" aria-hidden />}>
                  {t('home.browse')}
                </Button>
              </Link>
              <Link to="/statistics">
                <Button variant="onDark" icon={<BarChart3 className="h-4 w-4" aria-hidden />}>
                  {t('nav.statistics')}
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-10">
        <h2 className="text-lg font-semibold text-ink-900">{t('home.statsTitle')}</h2>
        {stats.loading ? (
          <div className="mt-4">
            <Spinner label={t('common.loading')} />
          </div>
        ) : stats.error ? (
          <div className="mt-4">
            <ErrorState error={stats.error} onRetry={stats.reload} retryLabel={t('common.retry')} />
          </div>
        ) : summary ? (
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
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
              label={t('admin.totalExpenditure')}
              value={formatLakh(summary.total_spent, { compact: true })}
              sublabel={`${formatPercent(summary.utilization_percent)} ${t('admin.utilization').toLowerCase()}`}
            />
            <StatCard
              label={t('admin.averageProgress')}
              value={formatPercent(summary.average_progress)}
              sublabel={`${summary.districts_covered} districts · ${summary.categories_covered} categories`}
            />
          </div>
        ) : null}
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-10">
        <h2 className="text-lg font-semibold text-ink-900">{t('home.howTitle')}</h2>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {features.map((feature) => (
            <div key={feature.title} className="surface p-4">
              <feature.icon className="h-5 w-5 text-ink-500" aria-hidden />
              <h3 className="mt-3 text-sm font-semibold text-ink-900">{feature.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-ink-600">{feature.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 pb-14">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-ink-900">{t('home.recentTitle')}</h2>
          <Link
            to="/projects"
            className="inline-flex items-center gap-1 text-sm font-medium text-ink-700 hover:underline"
          >
            {t('home.viewAll')}
            <ArrowRight className="h-3.5 w-3.5" aria-hidden />
          </Link>
        </div>

        <div className="mt-4">
          {recent.loading ? (
            <SkeletonCards count={6} />
          ) : recent.error ? (
            <ErrorState error={recent.error} onRetry={recent.reload} retryLabel={t('common.retry')} />
          ) : (recent.data?.items.length ?? 0) === 0 ? (
            <EmptyState title={t('common.empty')} description={t('common.emptyHint')} />
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {recent.data?.items.map((project) => (
                <ProjectCard key={project.id} project={project} />
              ))}
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
