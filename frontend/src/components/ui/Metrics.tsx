import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

interface StatCardProps {
  label: string
  value: ReactNode
  sublabel?: ReactNode
  icon?: ReactNode
  tone?: 'default' | 'warning' | 'danger' | 'success'
  to?: string
}

const TONES = {
  default: 'border-ink-200',
  warning: 'border-l-4 border-l-[#8a6d1f] border-ink-200',
  danger: 'border-l-4 border-l-saffron-700 border-ink-200',
  success: 'border-l-4 border-l-moss-600 border-ink-200',
}

export function StatCard({ label, value, sublabel, icon, tone = 'default', to }: StatCardProps) {
  const content = (
    <>
      <div className="flex items-start justify-between gap-3">
        <p className="data-label">{label}</p>
        {icon ? <span className="text-ink-400">{icon}</span> : null}
      </div>
      <p className="mt-2 text-2xl font-semibold tabular-nums text-ink-900">{value}</p>
      {sublabel ? <p className="mt-1 text-xs text-ink-500">{sublabel}</p> : null}
    </>
  )

  const className = `block rounded-lg border bg-white px-4 py-3 shadow-card transition-shadow ${TONES[tone]} ${
    to ? 'hover:shadow-raised' : ''
  }`

  if (to) {
    return (
      <Link to={to} className={className}>
        {content}
      </Link>
    )
  }
  return <div className={className}>{content}</div>
}

interface ProgressBarProps {
  value: number
  /** Optional dashed marker showing where the plan says progress should be. */
  target?: number | null
  label?: string
  tone?: 'default' | 'warning' | 'danger' | 'success'
  showValue?: boolean
}

const BAR_TONES = {
  default: 'bg-ink-700',
  warning: 'bg-[#8a6d1f]',
  danger: 'bg-saffron-700',
  success: 'bg-moss-600',
}

export function ProgressBar({
  value,
  target,
  label,
  tone = 'default',
  showValue = true,
}: ProgressBarProps) {
  const clamped = Math.max(0, Math.min(value ?? 0, 100))
  return (
    <div>
      {label || showValue ? (
        <div className="mb-1 flex items-baseline justify-between gap-2">
          {label ? <span className="text-xs font-medium text-ink-600">{label}</span> : <span />}
          {showValue ? (
            <span className="text-xs font-semibold tabular-nums text-ink-800">
              {clamped.toFixed(1)}%
            </span>
          ) : null}
        </div>
      ) : null}
      <div
        className="relative h-2 w-full overflow-hidden rounded-full bg-ink-200"
        role="progressbar"
        aria-valuenow={Math.round(clamped)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label ?? 'Progress'}
      >
        <div className={`h-full rounded-full ${BAR_TONES[tone]}`} style={{ width: `${clamped}%` }} />
        {target !== null && target !== undefined ? (
          <span
            className="absolute top-0 h-full w-0.5 bg-ink-900/60"
            style={{ left: `${Math.max(0, Math.min(target, 100))}%` }}
            title={`Planned ${target.toFixed(1)}%`}
          />
        ) : null}
      </div>
    </div>
  )
}

export function DataRow({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="py-2">
      <dt className="data-label">{label}</dt>
      <dd className="data-value break-words">{children}</dd>
    </div>
  )
}

export function DataGrid({ children, columns = 3 }: { children: ReactNode; columns?: 2 | 3 | 4 }) {
  const cols = {
    2: 'sm:grid-cols-2',
    3: 'sm:grid-cols-2 lg:grid-cols-3',
    4: 'sm:grid-cols-2 lg:grid-cols-4',
  }
  return <dl className={`grid grid-cols-1 gap-x-6 gap-y-1 ${cols[columns]}`}>{children}</dl>
}
