import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { LayoutDashboard, LogOut, Menu, ShieldCheck, User2, X } from 'lucide-react'
import { useAuth } from '@/features/auth/AuthContext'
import { useI18n } from '@/i18n'
import { AccessibilityBar } from '@/components/layout/AccessibilityBar'
import { Emblem } from '@/components/layout/Emblem'
import { MapNavLabel } from '@/features/map'

/**
 * Citizen-facing chrome, laid out the way an Indian government portal is:
 *
 *   1. accessibility / language utility strip (GIGW)
 *   2. masthead - emblem, ministry line, scheme name
 *   3. primary navigation bar in the institutional navy
 *   4. content
 *   5. footer with the data disclaimer and the last-reviewed date
 */
export function PublicLayout() {
  const { t } = useI18n()
  const { user, isInternal, signOut } = useAuth()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  // A signed-in citizen is the only person who can usefully ask for an
  // official role, so the entry point appears for them and nobody else.
  const isCitizen = user !== null && user.role === 'citizen'

    const navItems = [
    { to: '/', label: t('nav.home'), end: true },
    { to: '/projects', label: t('nav.projects'), end: false },
    { to: '/statistics', label: t('nav.statistics'), end: false },
    { to: '/map', label: <MapNavLabel />, end: false },
    { to: '/about', label: t('nav.about'), end: false },
    ...(isCitizen
      ? [{ to: '/request-access', label: t('nav.officialAccess'), end: false }]
      : []),
  ]

  /** Navy bar navigation: active item carries a saffron underline. */
  const navClass = ({ isActive }: { isActive: boolean }) =>
    `tap-target relative flex items-center px-3.5 py-2.5 text-sm font-medium transition-colors ${
      isActive
        ? 'bg-ink-800 text-white after:absolute after:inset-x-0 after:bottom-0 after:h-[3px] after:bg-saffron-500'
        : 'text-white/85 hover:bg-ink-800 hover:text-white'
    }`

  const mobileNavClass = ({ isActive }: { isActive: boolean }) =>
    `tap-target flex items-center rounded px-3 py-2.5 text-sm font-medium ${
      isActive ? 'bg-ink-100 text-ink-900' : 'text-ink-700 hover:bg-ink-100'
    }`

  const handleSignOut = async () => {
    await signOut()
    navigate('/')
  }

  return (
    <div className="flex min-h-screen flex-col overflow-x-clip">
      <a href="#main-content" className="skip-link">
        {t('a11y.skipToContent')}
      </a>

      <AccessibilityBar />

      {/* Masthead */}
      <div className="border-b-4 border-saffron-500 bg-white">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-3">
          <Link to="/" className="flex items-center gap-3">
            <Emblem className="h-11 w-11 bg-ink-900 text-white" />
            <span>
              <span className="block text-lg font-bold leading-tight text-ink-900">
                {t('app.name')}
              </span>
              <span className="block text-xs leading-snug text-ink-600">{t('app.tagline')}</span>
            </span>
          </Link>

          <div className="ml-auto flex items-center gap-2">
            {user ? (
              <div className="hidden items-center gap-2 sm:flex">
                <span className="flex items-center gap-1.5 rounded bg-ink-50 px-2.5 py-1.5 text-sm text-ink-800">
                  <User2 className="h-4 w-4 text-ink-500" aria-hidden />
                  {user.full_name}
                </span>
                <button
                  type="button"
                  onClick={handleSignOut}
                  className="tap-target inline-flex items-center gap-1.5 rounded border border-ink-300 px-2.5 py-2 text-sm font-medium text-ink-700 hover:bg-ink-50"
                >
                  <LogOut className="h-4 w-4" aria-hidden />
                  <span className="sr-only lg:not-sr-only">{t('nav.logout')}</span>
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className="tap-target hidden items-center rounded bg-ink-800 px-4 py-2 text-sm font-semibold text-white hover:bg-ink-900 sm:inline-flex"
              >
                {t('nav.login')}
              </Link>
            )}

            <button
              type="button"
              className="tap-target inline-flex items-center justify-center rounded border border-ink-300 text-ink-700 hover:bg-ink-50 md:hidden"
              onClick={() => setMenuOpen((open) => !open)}
              aria-expanded={menuOpen}
              aria-label={t('a11y.menu')}
            >
              {menuOpen ? (
                <X className="h-5 w-5" aria-hidden />
              ) : (
                <Menu className="h-5 w-5" aria-hidden />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Primary navigation */}
      <header className="no-print sticky top-0 z-30 bg-ink-900 shadow-header">
        <div className="mx-auto hidden max-w-7xl items-center px-4 md:flex">
          <nav className="flex items-center" aria-label={t('a11y.primaryNav')}>
            {navItems.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.end} className={navClass}>
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-2 py-1.5">
            {isCitizen ? (
              <Link
                to="/request-access"
                className="tap-target hidden items-center gap-1.5 rounded border border-white/30 px-3 py-1.5 text-sm font-medium text-white hover:bg-white/10 lg:inline-flex"
              >
                <ShieldCheck className="h-4 w-4" aria-hidden />
                {t('nav.officialAccess')}
              </Link>
            ) : null}

            {isInternal ? (
              <Link
                to="/admin"
                className="tap-target inline-flex items-center gap-1.5 rounded bg-saffron-500 px-3 py-1.5 text-sm font-semibold text-ink-950 hover:bg-saffron-400"
              >
                <LayoutDashboard className="h-4 w-4" aria-hidden />
                {t('nav.adminPortal')}
              </Link>
            ) : null}
          </div>
        </div>

        {menuOpen ? (
          <nav
            className="space-y-1 border-t border-ink-200 bg-white px-4 py-2 md:hidden"
            aria-label={t('a11y.mobileNav')}
          >
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={mobileNavClass}
                onClick={() => setMenuOpen(false)}
              >
                {item.label}
              </NavLink>
            ))}
            {isInternal ? (
              <NavLink to="/admin" className={mobileNavClass} onClick={() => setMenuOpen(false)}>
                {t('nav.adminPortal')}
              </NavLink>
            ) : null}
            {user ? (
              <button
                type="button"
                onClick={handleSignOut}
                className={`${mobileNavClass({ isActive: false })} w-full`}
              >
                {t('nav.logout')}
              </button>
            ) : (
              <NavLink to="/login" className={mobileNavClass} onClick={() => setMenuOpen(false)}>
                {t('nav.login')}
              </NavLink>
            )}
          </nav>
        ) : null}
      </header>

      {/* min-w-0 stops a wide child (a chart, a long table) from forcing the
          column wider than the viewport and spilling over the footer. */}
      <main id="main-content" className="relative z-0 w-full min-w-0 flex-1">
        <Outlet />
      </main>

      <footer className="relative z-10 mt-12 border-t-4 border-saffron-500 bg-ink-900 text-white">
        <div className="mx-auto max-w-7xl px-4 py-8">
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            <div className="lg:col-span-2">
              <div className="flex items-center gap-2.5">
                <Emblem className="h-9 w-9 bg-white/10 text-white" />
                <div>
                  <p className="text-sm font-bold">{t('app.name')}</p>
                  <p className="text-xs text-white/70">{t('app.subtitle')}</p>
                </div>
              </div>
              <p className="mt-4 max-w-md text-xs leading-relaxed text-white/60">
                {t('footer.note')}
              </p>
            </div>

            <nav aria-label={t('a11y.footerNav')}>
              <p className="text-xs font-semibold uppercase tracking-wide text-white/50">
                {t('footer.explore')}
              </p>
              <ul className="mt-3 space-y-2 text-sm">
                <li>
                  <Link to="/projects" className="text-white/80 hover:text-white hover:underline">
                    {t('nav.projects')}
                  </Link>
                </li>
                <li>
                  <Link to="/statistics" className="text-white/80 hover:text-white hover:underline">
                    {t('nav.statistics')}
                  </Link>
                </li>
                <li>
                  <Link to="/about" className="text-white/80 hover:text-white hover:underline">
                    {t('nav.about')}
                  </Link>
                </li>
              </ul>
            </nav>

            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-white/50">
                {t('footer.accessibility')}
              </p>
              <p className="mt-3 text-xs leading-relaxed text-white/70">
                {t('footer.accessibilityNote')}
              </p>
            </div>
          </div>

          <div className="mt-8 flex flex-col gap-2 border-t border-white/15 pt-4 text-xs text-white/50 sm:flex-row sm:items-center sm:justify-between">
            <p>{t('footer.rights')} · SIH26102</p>
            <p>
              {t('footer.lastReviewed')}:{' '}
              {new Date().toLocaleDateString('en-IN', {
                day: 'numeric',
                month: 'long',
                year: 'numeric',
              })}
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
