import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { MailCheck, UserPlus } from 'lucide-react'
import { authApi } from '@/api'
import { useAuth } from '@/features/auth/AuthContext'
import { useMutation } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { Button } from '@/components/ui/Button'
import { TextInput } from '@/components/ui/Field'
import { InlineMessage } from '@/components/ui/States'
import { Emblem } from '@/components/layout/Emblem'

export function SignupPage() {
  const { t } = useI18n()
  const { adoptSession } = useAuth()
  const navigate = useNavigate()

  const [step, setStep] = useState<'details' | 'verify'>('details')
  const [email, setEmail] = useState('')
  const [fullName, setFullName] = useState('')
  const [otp, setOtp] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [devOtp, setDevOtp] = useState<string | null>(null)
  const [validation, setValidation] = useState<string | null>(null)

  const requestOtp = useMutation(authApi.requestSignupOtp)
  const completeSignup = useMutation(authApi.completeSignup)

  const submitDetails = async (event: FormEvent) => {
    event.preventDefault()
    setValidation(null)
    const result = await requestOtp.run(email.trim(), fullName.trim())
    if (result) {
      setDevOtp(result.dev_otp ?? null)
      setStep('verify')
    }
  }

  const submitVerify = async (event: FormEvent) => {
    event.preventDefault()
    if (password.length < 8) {
      setValidation(t('auth.passwordRule'))
      return
    }
    if (password !== confirm) {
      setValidation(t('auth.passwordMismatch'))
      return
    }
    setValidation(null)
    const token = await completeSignup.run({
      email: email.trim(),
      full_name: fullName.trim(),
      otp: otp.trim(),
      password,
    })
    if (token) {
      adoptSession(token)
      navigate('/', { replace: true })
    }
  }

  return (
    <div className="mx-auto flex min-h-[70vh] max-w-md flex-col justify-center px-4 py-12">
      <div className="surface p-6 sm:p-8">
        <div className="flex items-center gap-3">
          <Emblem className="h-10 w-10 bg-ink-900 text-white" />
          <div>
            <h1 className="text-lg font-semibold text-ink-900">{t('auth.signupTitle')}</h1>
            <p className="text-xs text-ink-500">{t('auth.signupSubtitle')}</p>
          </div>
        </div>

        {step === 'details' ? (
          <form className="mt-6 space-y-4" onSubmit={submitDetails}>
            {requestOtp.error ? (
              <InlineMessage tone="warning">{requestOtp.error.message}</InlineMessage>
            ) : null}
            <TextInput
              label={t('auth.fullName')}
              name="full_name"
              autoComplete="name"
              required
              minLength={2}
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
            />
            <TextInput
              label={t('auth.email')}
              name="email"
              type="email"
              autoComplete="email"
              inputMode="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
            <Button
              type="submit"
              className="w-full"
              loading={requestOtp.pending}
              icon={<MailCheck className="h-4 w-4" aria-hidden />}
            >
              {t('auth.sendOtp')}
            </Button>
          </form>
        ) : (
          <form className="mt-6 space-y-4" onSubmit={submitVerify}>
            <InlineMessage tone="info">
              {t('auth.otpSent')} <span className="font-medium">{email}</span>
            </InlineMessage>
            {devOtp ? (
              <InlineMessage tone="warning">
                {t('auth.otpDevNotice')} <span className="font-mono font-semibold">{devOtp}</span>
              </InlineMessage>
            ) : null}
            {completeSignup.error ? (
              <InlineMessage tone="warning">{completeSignup.error.message}</InlineMessage>
            ) : null}
            {validation ? <InlineMessage tone="warning">{validation}</InlineMessage> : null}

            <TextInput
              label={t('auth.otp')}
              name="otp"
              autoComplete="one-time-code"
              inputMode="numeric"
              required
              maxLength={8}
              value={otp}
              onChange={(event) => setOtp(event.target.value)}
            />
            <TextInput
              label={t('auth.password')}
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              hint={t('auth.passwordRule')}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
            <TextInput
              label={t('auth.confirmPassword')}
              type="password"
              autoComplete="new-password"
              required
              minLength={8}
              value={confirm}
              onChange={(event) => setConfirm(event.target.value)}
            />

            <Button
              type="submit"
              className="w-full"
              loading={completeSignup.pending}
              icon={<UserPlus className="h-4 w-4" aria-hidden />}
            >
              {t('auth.completeSignup')}
            </Button>
            <Button type="button" variant="ghost" className="w-full" onClick={() => setStep('details')}>
              {t('common.back')}
            </Button>
          </form>
        )}

        <p className="mt-5 text-sm text-ink-600">
          {t('auth.haveAccount')}{' '}
          <Link to="/login" className="font-medium text-ink-900 underline underline-offset-2">
            {t('auth.signIn')}
          </Link>
        </p>

        <p className="mt-3 rounded-md bg-ink-50 px-3 py-2 text-xs leading-relaxed text-ink-600">
          {t('auth.officialHelp')}{' '}
          <Link
            to="/request-access"
            className="font-medium text-ink-800 underline underline-offset-2"
          >
            {t('auth.requestAccess')}
          </Link>
        </p>
      </div>
    </div>
  )
}
