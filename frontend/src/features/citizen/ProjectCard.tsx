import { Link } from 'react-router-dom'
import { Building2, CalendarDays, MapPin } from 'lucide-react'
import { Badge, StatusBadge } from '@/components/ui/Badge'
import { ProgressBar } from '@/components/ui/Metrics'
import { formatDate, formatLakh, truncate } from '@/utils/format'
import { useI18n } from '@/i18n'
import type { ProjectPublicSummary } from '@/types'

export function ProjectCard({ project }: { project: ProjectPublicSummary }) {
  const { t, tEnum } = useI18n()
  const underReview = project.public_indicator === 'Under Review'

  return (
    <article className="surface flex h-full flex-col p-4 transition-shadow hover:shadow-raised">
      <div className="flex items-start justify-between gap-2">
        <span className="font-mono text-[11px] text-ink-500">{project.project_code}</span>
        <StatusBadge status={project.status} />
      </div>

      <h3 className="mt-2 text-sm font-semibold leading-snug text-ink-900">
        <Link to={`/scheme/${project.id}`} className="hover:underline">
          {truncate(project.title, 95)}
        </Link>
      </h3>

      <dl className="mt-3 space-y-1.5 text-xs text-ink-600">
        <div className="flex items-start gap-1.5">
          <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ink-400" aria-hidden />
          <dd>
            {tEnum('district', project.district)}, {tEnum('state', project.state)}
          </dd>
        </div>
        <div className="flex items-start gap-1.5">
          <Building2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ink-400" aria-hidden />
          <dd>{truncate(tEnum('agency', project.executing_agency), 44)}</dd>
        </div>
        <div className="flex items-start gap-1.5">
          <CalendarDays className="mt-0.5 h-3.5 w-3.5 shrink-0 text-ink-400" aria-hidden />
          <dd>
            {project.sanction_year} · {formatDate(project.planned_end_date)}
          </dd>
        </div>
      </dl>

      <div className="mt-4 grid grid-cols-2 gap-3 border-t border-ink-100 pt-3">
        <div>
          <p className="data-label">{t('field.allocated')}</p>
          <p className="mt-0.5 text-sm font-semibold tabular-nums text-ink-900">
            {formatLakh(project.allocated_amount)}
          </p>
        </div>
        <div>
          <p className="data-label">{t('field.spent')}</p>
          <p className="mt-0.5 text-sm font-semibold tabular-nums text-ink-900">
            {formatLakh(project.spent_amount)}
          </p>
        </div>
      </div>

      <div className="mt-3 space-y-2">
        <ProgressBar
          value={project.progress_percent}
          label={t('field.progress')}
          tone={project.progress_percent >= 100 ? 'success' : 'default'}
        />
        <ProgressBar
          value={project.utilization_percent}
          label={t('field.utilization')}
          tone={project.utilization_percent > 100 ? 'danger' : 'default'}
        />
      </div>

      <div className="mt-4 flex items-center justify-between gap-2">
        <Badge tone={underReview ? 'warning' : 'success'} dot title={t('detail.indicatorHelp')}>
          {underReview ? t('detail.indicatorUnderReview') : t('detail.indicatorNormal')}
        </Badge>
        <Link
          to={`/scheme/${project.id}`}
          className="text-xs font-medium text-ink-700 underline-offset-2 hover:underline"
        >
          {t('common.viewDetails')} →
        </Link>
      </div>
    </article>
  )
}
