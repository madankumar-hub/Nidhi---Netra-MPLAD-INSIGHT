import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { LogIn, ShieldCheck, User2 } from 'lucide-react'
import { authApi } from '@/api'
import { useAuth } from '@/features/auth/AuthContext'
import { useApi, useMutation } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { Button } from '@/components/ui/Button'
import { TextInput } from '@/components/ui/Field'
import { InlineMessage } from '@/components/ui/States'
import { Emblem } from '@/components/layout/Emblem'

type Audience = 'citizen' | 'official'

/**
 * One sign-in form, two framings.
 *
 * The tabs are presentational on purpose: the API decides what an account is
 * from the database, never from which tab the browser was on. Choosing
 * "Official" cannot grant anything — it changes the copy and the links below
 * the form, nothing else.
 */
export function LoginPage() {
  const { t } = useI18n()
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [audience, setAudience] = useState<Audience>('citizen')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const { run, pending, error } = useMutation(signIn)
  const policy = useApi((signal) => authApi.getAccessPolicy(signal), [])

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const user = await run(email.trim(), password)
    if (!user) return
    const from = (location.state as { from?: string } | null)?.from
    if (from) {
      navigate(from, { replace: true })
    } else {
      navigate(user.role === 'citizen' ? '/' : '/admin', { replace: true })
    }
  }

  const tabs: { id: Audience; label: string; icon: typeof User2 }[] = [
    { id: 'citizen', label: t('auth.tabCitizen'), icon: User2 },
    { id: 'official', label: t('auth.tabOfficial'), icon: ShieldCheck },
  ]

  return (
    <div className="mx-auto flex min-h-[70vh] max-w-md flex-col justify-center px-4 py-12">
      <div className="surface overflow-hidden">
        <div className="flex items-center gap-3 px-6 pt-6 sm:px-8 sm:pt-8">
          <Emblem className="h-10 w-10 bg-ink-900 text-white" />
          <div>
            <h1 className="text-lg font-semibold text-ink-900">{t('auth.loginTitle')}</h1>
            <p className="text-xs text-ink-500">
              {audience === 'citizen' ? t('auth.citizenSubtitle') : t('auth.officialSubtitle')}
            </p>
          </div>
        </div>

        {/* Audience selector */}
        <div
          className="mx-6 mt-5 grid grid-cols-2 gap-1 rounded-lg bg-ink-100 p-1 sm:mx-8"
          role="tablist"
          aria-label={t('auth.loginTitle')}
        >
          {tabs.map((tab) => {
            const selected = tab.id === audience
            return (
              <button
                key={tab.id}
                type="button"
                role="tab"
                aria-selected={selected}
                onClick={() => setAudience(tab.id)}
                className={`tap-target flex items-center justify-center gap-2 rounded-md px-3 py-2
                  text-sm font-medium transition-colors ${
                    selected
                      ? 'bg-white text-ink-900 shadow-card'
                      : 'text-ink-600 hover:text-ink-900'
                  }`}
              >
                <tab.icon className="h-4 w-4" aria-hidden />
                {tab.label}
              </button>
            )
          })}
        </div>

        <form className="space-y-4 px-6 py-5 sm:px-8 sm:pb-8" onSubmit={submit}>
          {error ? <InlineMessage tone="warning">{error.message}</InlineMessage> : null}

          <TextInput
            label={t('auth.email')}
            type="email"
            autoComplete="email"
            required
            value={email}
            placeholder={audience === 'official' ? 'officer@mplad.gov.in' : 'you@example.com'}
            onChange={(event) => setEmail(event.target.value)}
          />
          <TextInput
            label={t('auth.password')}
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />

          <Button
            type="submit"
            className="w-full"
            loading={pending}
            icon={<LogIn className="h-4 w-4" aria-hidden />}
          >
            {t('auth.signIn')}
          </Button>

          {audience === 'citizen' ? (
            <p className="text-sm text-ink-600">
              {t('auth.noAccount')}{' '}
              <Link to="/signup" className="font-medium text-ink-900 underline underline-offset-2">
                {t('auth.createAccount')}
              </Link>
            </p>
          ) : (
            <div className="space-y-3">
              <div className="flex items-start gap-2 rounded-md bg-ink-50 px-3 py-2.5 text-xs leading-relaxed text-ink-600">
                <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-ink-400" aria-hidden />
                <span>
                  {t('auth.officialHelp')}
                  {policy.data ? (
                    <>
                      {' '}
                      {policy.data.enforced && policy.data.domains.length > 0 ? (
                        <>
                          {t('auth.allowlistNote')}{' '}
                          <span className="font-medium text-ink-800">
                            {policy.data.domains.map((domain) => `@${domain}`).join(', ')}
                          </span>
                          .
                        </>
                      ) : (
                        t('auth.allowlistOpen')
                      )}
                    </>
                  ) : null}
                </span>
              </div>
              <p className="text-sm text-ink-600">
                <Link
                  to="/request-access"
                  className="font-medium text-ink-900 underline underline-offset-2"
                >
                  {t('auth.requestAccess')}
                </Link>
              </p>
            </div>
          )}
        </form>
      </div>
    </div>
  )
}
