import {
  Activity,
  AlertTriangle,
  ArrowRightLeft,
  FileDown,
  IndianRupee,
  ListChecks,
  MessageSquareWarning,
  ShieldCheck,
  StickyNote,
  TrendingUp,
} from 'lucide-react'
import { useI18n } from '@/i18n'
import { EmptyState } from '@/components/ui/States'
import { formatDateTime } from '@/utils/format'
import type { ActivityEntry, ActivityType } from '@/types'

const ICONS: Partial<Record<ActivityType, typeof Activity>> = {
  status_changed: ArrowRightLeft,
  review_status_changed: ArrowRightLeft,
  project_reviewed: ShieldCheck,
  risk_assessed: AlertTriangle,
  risk_level_changed: AlertTriangle,
  risk_status_changed: AlertTriangle,
  note_added: StickyNote,
  mitigation_added: ListChecks,
  mitigation_updated: ListChecks,
  mitigation_resolved: ListChecks,
  progress_updated: TrendingUp,
  fund_updated: IndianRupee,
  report_exported: FileDown,
  citizen_report_filed: MessageSquareWarning,
  citizen_report_triaged: MessageSquareWarning,
}

export function ActivityTimeline({
  entries,
  showProject = false,
}: {
  entries: ActivityEntry[]
  showProject?: boolean
}) {
  const { t } = useI18n()

  if (entries.length === 0) {
    return <EmptyState title={t('activity.none')} />
  }

  return (
    <ol className="relative space-y-4 border-l border-ink-200 pl-5">
      {entries.map((entry) => {
        const Icon = ICONS[entry.activity_type] ?? Activity
        return (
          <li key={entry.id} className="relative">
            <span
              className="absolute -left-[1.6875rem] flex h-6 w-6 items-center justify-center rounded-full border border-ink-200 bg-white text-ink-500"
              aria-hidden
            >
              <Icon className="h-3.5 w-3.5" />
            </span>
            <div className="rounded-lg border border-ink-200 bg-white px-3.5 py-2.5">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <p className="text-sm font-medium text-ink-900">{entry.summary}</p>
                <span className="text-xs text-ink-500">{formatDateTime(entry.created_at)}</span>
              </div>
              {entry.detail ? (
                <p className="mt-1 text-xs leading-relaxed text-ink-600">{entry.detail}</p>
              ) : null}
              <p className="mt-1.5 text-xs text-ink-500">
                {entry.actor_name} ({entry.actor_role})
                {showProject && entry.project_id ? ` · work #${entry.project_id}` : ''}
              </p>
            </div>
          </li>
        )
      })}
    </ol>
  )
}
