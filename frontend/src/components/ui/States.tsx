import type { ReactNode } from 'react'
import { AlertTriangle, Inbox, Lock, RefreshCw, WifiOff } from 'lucide-react'
import { ApiError } from '@/api/client'
import { useI18n } from '@/i18n'
import { Button } from './Button'

interface EmptyStateProps {
  title: string
  description?: string
  icon?: ReactNode
  action?: ReactNode
}

export function EmptyState({ title, description, icon, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center rounded border border-dashed border-ink-300 bg-white px-6 py-12 text-center">
      <span className="text-ink-400">{icon ?? <Inbox className="h-8 w-8" aria-hidden />}</span>
      <h3 className="mt-3 text-base font-semibold text-ink-800">{title}</h3>
      {description ? <p className="mt-1 max-w-sm text-sm text-ink-600">{description}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  )
}

interface ErrorStateProps {
  error: ApiError | Error | null
  onRetry?: () => void
  retryLabel?: string
}

export function ErrorState({ error, onRetry, retryLabel }: ErrorStateProps) {
  const { t } = useI18n()
  const apiError = error instanceof ApiError ? error : null
  const isForbidden = apiError?.isForbidden ?? false
  const isNetwork = apiError?.code === 'network_error'

  let icon = <AlertTriangle className="h-8 w-8" aria-hidden />
  if (isForbidden) icon = <Lock className="h-8 w-8" aria-hidden />
  if (isNetwork) icon = <WifiOff className="h-8 w-8" aria-hidden />

  // A network failure and a server message need different wording: the first is
  // the citizen's connection, the second is ours. Neither should show a stack.
  let heading: string
  if (isForbidden) heading = t('state.forbidden')
  else if (isNetwork) heading = t('state.network')
  else heading = error?.message ?? t('state.unexpected')

  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center rounded border border-saffron-300 bg-saffron-50 px-6 py-10 text-center"
    >
      <span className="text-saffron-700">{icon}</span>
      <h3 className="mt-3 text-base font-semibold text-ink-900">{heading}</h3>
      {apiError?.status ? (
        <p className="mt-1 text-xs text-ink-600">
          {t('state.errorCode')} {apiError.status} · {apiError.code}
        </p>
      ) : null}
      {onRetry && !isForbidden ? (
        <Button
          variant="secondary"
          size="sm"
          className="mt-4"
          onClick={onRetry}
          icon={<RefreshCw className="h-3.5 w-3.5" aria-hidden />}
        >
          {retryLabel ?? t('state.retry')}
        </Button>
      ) : null}
    </div>
  )
}

export function InlineMessage({
  tone = 'info',
  children,
}: {
  tone?: 'info' | 'success' | 'warning'
  children: ReactNode
}) {
  const tones = {
    info: 'border-ink-300 bg-ink-50 text-ink-800',
    success: 'border-moss-300 bg-moss-50 text-moss-900',
    warning: 'border-saffron-300 bg-saffron-50 text-saffron-900',
  }
  return (
    <div className={`rounded border px-3 py-2 text-sm ${tones[tone]}`} role="status">
      {children}
    </div>
  )
}
