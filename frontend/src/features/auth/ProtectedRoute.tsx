import { Navigate, useLocation } from 'react-router-dom'
import type { ReactNode } from 'react'
import { ShieldAlert } from 'lucide-react'
import { useAuth } from './AuthContext'
import { useI18n } from '@/i18n'
import { Spinner } from '@/components/ui/Spinner'
import type { UserRole } from '@/types'

interface ProtectedRouteProps {
  children: ReactNode
  /** When omitted any signed-in user may pass. */
  roles?: UserRole[]
}

/**
 * Convenience guard only. The backend independently rejects every
 * unauthorised request, so removing this component would not expose data.
 */
export function ProtectedRoute({ children, roles }: ProtectedRouteProps) {
  const { user, initialising } = useAuth()
  const { t, tEnum } = useI18n()
  const location = useLocation()

  if (initialising) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Spinner label={t('common.loading')} />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  if (roles && !roles.includes(user.role)) {
    return (
      <div className="mx-auto max-w-lg px-4 py-20 text-center">
        <ShieldAlert className="mx-auto h-12 w-12 text-saffron-600" aria-hidden />
        <h1 className="mt-4 text-xl font-semibold text-ink-900">{t('common.unauthorized')}</h1>
        <p className="mt-2 text-sm text-ink-600">
          {t('auth.signedInAs')} {user.full_name} ({tEnum('userRole', user.role)}).
        </p>
      </div>
    )
  }

  return <>{children}</>
}
