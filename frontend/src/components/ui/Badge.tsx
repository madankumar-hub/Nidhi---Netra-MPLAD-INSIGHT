import type { ReactNode } from 'react'
import type {
  AccessRequestStatus,
  CitizenReportStatus,
  MitigationStatus,
  ProjectStatus,
  ReviewStatus,
  RiskLevel,
} from '@/types'
import { useI18n } from '@/i18n'

type Tone = 'neutral' | 'info' | 'success' | 'warning' | 'danger' | 'critical'

/**
 * Government portals are read on low-quality displays in bright rooms, so every
 * tone clears WCAG-AA on white and pairs colour with a dot or a word - colour
 * alone never carries the meaning.
 */
const TONES: Record<Tone, string> = {
  neutral: 'bg-ink-100 text-ink-800 ring-ink-300',
  info: 'bg-[#e8f1fd] text-[#0f3c6e] ring-[#a9caf0]',
  success: 'bg-moss-100 text-moss-800 ring-moss-300',
  warning: 'bg-[#fdf3d8] text-[#5f4a0f] ring-[#e8d296]',
  danger: 'bg-saffron-100 text-saffron-900 ring-saffron-300',
  critical: 'bg-[#fbe3e3] text-[#6d1414] ring-[#e8adad]',
}

interface BadgeProps {
  children: ReactNode
  tone?: Tone
  /** Small leading dot; helps when colour alone must not carry meaning. */
  dot?: boolean
  className?: string
  title?: string
}

export function Badge({ children, tone = 'neutral', dot = false, className = '', title }: BadgeProps) {
  return (
    <span
      title={title}
      className={`inline-flex items-center gap-1.5 rounded px-2.5 py-1 text-xs font-semibold
        ring-1 ring-inset ${TONES[tone]} ${className}`}
    >
      {dot ? <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden /> : null}
      {children}
    </span>
  )
}

const PROJECT_STATUS_TONE: Record<ProjectStatus, Tone> = {
  'Not Started': 'neutral',
  'In Progress': 'info',
  Delayed: 'danger',
  'On Hold': 'warning',
  Completed: 'success',
  Cancelled: 'neutral',
}

export function StatusBadge({ status }: { status: ProjectStatus }) {
  const { tEnum } = useI18n()
  return (
    <Badge tone={PROJECT_STATUS_TONE[status] ?? 'neutral'} dot>
      {tEnum('projectStatus', status)}
    </Badge>
  )
}

const REVIEW_STATUS_TONE: Record<ReviewStatus, Tone> = {
  'Pending Review': 'neutral',
  Reviewed: 'info',
  'On Track': 'success',
  Delayed: 'danger',
  Escalated: 'critical',
  Resolved: 'success',
}

export function ReviewStatusBadge({ status }: { status: ReviewStatus }) {
  const { tEnum } = useI18n()
  return <Badge tone={REVIEW_STATUS_TONE[status] ?? 'neutral'}>{tEnum('reviewStatus', status)}</Badge>
}

const RISK_TONE: Record<RiskLevel, Tone> = {
  LOW: 'success',
  MEDIUM: 'warning',
  HIGH: 'danger',
  CRITICAL: 'critical',
}

export function RiskBadge({ level, score }: { level: RiskLevel; score?: number | null }) {
  const { tEnum } = useI18n()
  return (
    <Badge tone={RISK_TONE[level]} dot>
      {tEnum('riskLevel', level)}
      {score !== undefined && score !== null ? (
        <span className="font-bold tabular-nums"> · {score.toFixed(0)}</span>
      ) : null}
    </Badge>
  )
}

const MITIGATION_TONE: Record<MitigationStatus, Tone> = {
  Open: 'warning',
  'In Progress': 'info',
  Resolved: 'success',
}

export function MitigationBadge({ status }: { status: MitigationStatus }) {
  const { tEnum } = useI18n()
  return <Badge tone={MITIGATION_TONE[status]}>{tEnum('mitigationStatus', status)}</Badge>
}

const REPORT_STATUS_TONE: Record<CitizenReportStatus, Tone> = {
  Submitted: 'info',
  'Under Review': 'warning',
  'Action Taken': 'success',
  Closed: 'neutral',
}

export function ReportStatusBadge({ status }: { status: CitizenReportStatus }) {
  const { tEnum } = useI18n()
  return <Badge tone={REPORT_STATUS_TONE[status] ?? 'neutral'}>{tEnum('reportStatus', status)}</Badge>
}

const ACCESS_STATUS_TONE: Record<AccessRequestStatus, Tone> = {
  Pending: 'warning',
  Approved: 'success',
  Rejected: 'critical',
  Withdrawn: 'neutral',
}

export function AccessStatusBadge({ status }: { status: AccessRequestStatus }) {
  const { tEnum } = useI18n()
  return (
    <Badge tone={ACCESS_STATUS_TONE[status] ?? 'neutral'} dot>
      {tEnum('accessRequestStatus', status)}
    </Badge>
  )
}

/** Public-safe indicator (FR6). Citizens see this instead of a numeric score. */
export function PublicIndicatorBadge({ indicator }: { indicator: string }) {
  const { tEnum } = useI18n()
  return (
    <Badge tone={indicator === 'Under Review' ? 'warning' : 'success'} dot>
      {tEnum('publicIndicator', indicator)}
    </Badge>
  )
}
