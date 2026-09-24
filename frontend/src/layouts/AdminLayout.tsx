import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  Activity,
  AlertTriangle,
  BarChart3,
  ClipboardCheck,
  Clock,
  ShieldCheck,
  UserCog,
  FolderOpen,
  Globe,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquareWarning,
  X,
} from 'lucide-react'
import { useAuth } from '@/features/auth/AuthContext'
import { useI18n } from '@/i18n'
import { LanguageSwitcher } from '@/components/layout/LanguageSwitcher'
import { Emblem } from '@/components/layout/Emblem'
import { MapNavIcon, MapNavLabel } from '@/features/map'

export function AdminLayout() {
  const { t, tEnum } = useI18n()
  const { user, isAdmin, signOut } = useAuth()
  const navigate = useNavigate()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const items = [
    { to: '/admin', label: t('nav.dashboard'), icon: LayoutDashboard, end: true },
    { to: '/admin/projects', label: t('nav.projects'), icon: FolderOpen, end: false },
    { to: '/admin/flagged', label: t('nav.flagged'), icon: AlertTriangle, end: false },
    { to: '/admin/delayed', label: t('nav.delayed'), icon: Clock, end: false },
    { to: '/admin/reviews', label: t('nav.reviewQueue'), icon: ClipboardCheck, end: false },
    { to: '/admin/citizen-reports', label: t('nav.citizenReports'), icon: MessageSquareWarning, end: false },
    { to: '/admin/analytics', label: t('nav.analytics'), icon: BarChart3, end: false },
    { to: '/admin/map', label: <MapNavLabel />, icon: MapNavIcon, end: false },
    { to: '/admin/activity', label: t('nav.activity'), icon: Activity, end: false },
    // Granting official roles is an Administrator power, so the link only
    // appears for them. The route and the API are guarded independently.
    ...(isAdmin
      ? [
          {
            to: '/admin/access-requests',
            label: t('nav.accessRequests'),
            icon: ShieldCheck,
            end: false,
          },
          {
            to: '/admin/users',
            label: t('nav.users'),
            icon: UserCog,
            end: false,
          },
        ]
      : []),
  ]

  const itemClass = ({ isActive }: { isActive: boolean }) =>
    `tap-target relative flex items-center gap-2.5 rounded px-3 py-2.5 text-sm font-medium transition-colors ${
      isActive
        ? 'bg-ink-800 text-white before:absolute before:inset-y-1 before:left-0 before:w-1 before:rounded-r before:bg-saffron-500'
        : 'text-ink-200 hover:bg-ink-800/60 hover:text-white'
    }`

  const handleSignOut = async () => {
    await signOut()
    navigate('/')
  }

  const sidebar = (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2.5 border-b-2 border-saffron-500 px-4 py-4">
        <Emblem className="h-9 w-9 text-white" />
        <div>
          <p className="text-sm font-semibold leading-tight text-white">{t('app.name')}</p>
          <p className="text-[11px] leading-tight text-ink-300">{t('nav.adminPortal')}</p>
        </div>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto p-3" aria-label={t('a11y.adminNav')}>
        {items.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={itemClass}
            onClick={() => setSidebarOpen(false)}
          >
            <item.icon className="h-4 w-4 shrink-0" aria-hidden />
            <span className="truncate">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-white/10 p-3">
        <Link
          to="/"
          className="tap-target flex items-center gap-2.5 rounded px-3 py-2.5 text-sm text-ink-200 hover:bg-ink-800/60 hover:text-white"
        >
          <Globe className="h-4 w-4" aria-hidden />
          {t('nav.citizenPortal')}
        </Link>
      </div>
    </div>
  )

  return (
    <div className="flex min-h-screen bg-ink-50">
      {/* GIGW 3.0 requires a skip link on every page, not only the public ones.
          An officer navigating by keyboard would otherwise tab through the whole
          sidebar on every route change. */}
      <a href="#admin-main-content" className="skip-link">
        {t('a11y.skipToContent')}
      </a>

      {/* Desktop sidebar */}
      <aside className="hidden w-60 shrink-0 bg-ink-900 lg:block">
        <div className="sticky top-0 h-screen">{sidebar}</div>
      </aside>

      {/* Mobile / tablet drawer */}
      {sidebarOpen ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div
            className="absolute inset-0 bg-ink-950/50"
            onClick={() => setSidebarOpen(false)}
            aria-hidden
          />
          <aside className="absolute inset-y-0 left-0 w-64 bg-ink-900 shadow-raised">{sidebar}</aside>
        </div>
      ) : null}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="no-print sticky top-0 z-30 flex items-center gap-3 border-b-2 border-saffron-500 bg-white px-4 py-3">
          <button
            type="button"
            className="tap-target inline-flex items-center justify-center rounded border border-ink-300 text-ink-700 hover:bg-ink-50 lg:hidden"
            onClick={() => setSidebarOpen((open) => !open)}
            aria-label={t('a11y.menu')}
            aria-expanded={sidebarOpen}
          >
            {sidebarOpen ? <X className="h-5 w-5" aria-hidden /> : <Menu className="h-5 w-5" aria-hidden />}
          </button>

          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-ink-900">{t('nav.adminPortal')}</p>
            <p className="truncate text-xs text-ink-500">{t('gov.bar')}</p>
          </div>

          <div className="ml-auto flex items-center gap-3">
            <span className="hidden rounded bg-ink-900 px-2 py-1 text-white sm:inline-flex">
              <LanguageSwitcher compact />
            </span>
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium leading-tight text-ink-900">{user?.full_name}</p>
              <p className="text-[11px] leading-tight text-ink-500">
                {user ? tEnum('userRole', user.role) : ''}
                {user?.designation ? ` · ${user.designation}` : ''}
              </p>
            </div>
            <button
              type="button"
              onClick={handleSignOut}
              className="tap-target inline-flex items-center gap-1.5 rounded border border-ink-300 px-2.5 py-2 text-sm text-ink-700 hover:bg-ink-50 hover:text-ink-900"
            >
              <LogOut className="h-4 w-4" aria-hidden />
              <span className="sr-only">{t('nav.logout')}</span>
            </button>
          </div>
        </header>

        <main
          id="admin-main-content"
          tabIndex={-1}
          className="relative z-0 w-full min-w-0 flex-1 px-4 py-6 sm:px-6"
        >
          <Outlet />
        </main>
      </div>
    </div>
  )
}
