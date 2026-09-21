import { useState } from 'react'
import { Link } from 'react-router-dom'
import { CheckCircle2, Clock, ShieldCheck, XCircle } from 'lucide-react'
import { authApi } from '@/api'
import { useAuth } from '@/features/auth/AuthContext'
import { useApi, useMutation } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { PageHeader } from '@/components/layout/PageHeader'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { SelectInput, TextArea, TextInput } from '@/components/ui/Field'
import { Spinner } from '@/components/ui/Spinner'
import { InlineMessage } from '@/components/ui/States'
import { formatDateTime } from '@/utils/format'
import type { AccessRequestStatus, UserRole } from '@/types'

const STATUS_TONE: Record<AccessRequestStatus, 'warning' | 'success' | 'critical' | 'neutral'> = {
  Pending: 'warning',
  Approved: 'success',
  Rejected: 'critical',
  Withdrawn: 'neutral',
}

const STATUS_ICON = {
  Pending: Clock,
  Approved: CheckCircle2,
  Rejected: XCircle,
  Withdrawn: XCircle,
}

/**
 * A citizen asks to be made an Officer or Auditor. Submitting this changes
 * nothing about the account — it queues a request that an administrator has to
 * approve. Administrator itself cannot be requested at all.
 */
export function RequestAccessPage() {
  const { t, tEnum } = useI18n()
  const { user, isAuthenticated, refreshUser } = useAuth()

  const [role, setRole] = useState<UserRole>('officer')
  const [designation, setDesignation] = useState('')
  const [department, setDepartment] = useState('')
  const [district, setDistrict] = useState('')
  const [employeeId, setEmployeeId] = useState('')
  const [justification, setJustification] = useState('')
  const [validation, setValidation] = useState<string | null>(null)
  const [submitted, setSubmitted] = useState(false)

  const policy = useApi((signal) => authApi.getAccessPolicy(signal), [])
  const roles = useApi((signal) => authApi.getRequestableRoles(signal), [])
  const mine = useApi((signal) => authApi.listMyAccessRequests(signal), [submitted], {
    enabled: isAuthenticated,
  })
  const submit = useMutation(authApi.requestOfficialAccess)

  if (!isAuthenticated) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <ShieldCheck className="mx-auto h-10 w-10 text-ink-400" aria-hidden />
        <h1 className="mt-4 text-lg font-semibold text-ink-900">
          {t('auth.requestAccessTitle')}
        </h1>
        <p className="mt-2 text-sm text-ink-600">{t('auth.mustSignIn')}</p>
        <div className="mt-5 flex justify-center gap-2">
          <Link to="/login">
            <Button>{t('auth.signIn')}</Button>
          </Link>
          <Link to="/signup">
            <Button variant="secondary">{t('auth.createAccount')}</Button>
          </Link>
        </div>
      </div>
    )
  }

  const alreadyOfficial = user !== null && user.role !== 'citizen'
  const pending = (mine.data ?? []).some((item) => item.status === 'Pending')

  const send = async () => {
    if (justification.trim().length < 20) {
      setValidation(t('auth.justificationHint'))
      return
    }
    setValidation(null)
    const result = await submit.run({
      requested_role: role,
      designation: designation.trim() || undefined,
      department: department.trim() || undefined,
      district: district.trim() || undefined,
      employee_id: employeeId.trim() || undefined,
      justification: justification.trim(),
    })
    if (result) {
      setJustification('')
      setSubmitted(true)
      await refreshUser()
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <PageHeader
        title={t('auth.requestAccessTitle')}
        description={t('auth.requestAccessSubtitle')}
      />

      {submitted ? (
        <div className="mb-5">
          <InlineMessage tone="success">{t('auth.requestSubmitted')}</InlineMessage>
        </div>
      ) : null}

      {alreadyOfficial ? (
        <Card>
          <CardBody>
            <p className="text-sm text-ink-700">
              {t('auth.signedInAs')} <span className="font-medium">{user?.full_name}</span> (
              {user ? t(`auth.role.${user.role}` as const) : ''}). {t('nav.adminPortal')}:{' '}
              <Link to="/admin" className="font-medium text-ink-900 underline underline-offset-2">
                {t('nav.dashboard')}
              </Link>
            </p>
          </CardBody>
        </Card>
      ) : (
        <Card>
          <CardHeader
            title={t('auth.requestAccess')}
            description={
              policy.data?.enforced && policy.data.domains.length > 0
                ? `${t('auth.allowlistNote')} ${policy.data.domains.map((d) => `@${d}`).join(', ')}`
                : t('auth.allowlistOpen')
            }
            icon={<ShieldCheck className="h-4 w-4" aria-hidden />}
          />
          <CardBody>
            {submit.error ? (
              <div className="mb-4">
                <InlineMessage tone="warning">{submit.error.message}</InlineMessage>
              </div>
            ) : null}

            {pending ? (
              <div className="mb-4">
                <InlineMessage tone="info">{t('auth.requestSubmitted')}</InlineMessage>
              </div>
            ) : null}

            <div className="grid gap-4 sm:grid-cols-2">
              <SelectInput
                label={t('auth.requestedRole')}
                value={role}
                options={(roles.data ?? ['officer', 'auditor']).map((item) => ({
                  label: t(`auth.role.${item}` as const),
                  value: item,
                }))}
                onChange={(event) => setRole(event.target.value as UserRole)}
                disabled={pending}
              />
              <TextInput
                label={t('auth.designation')}
                value={designation}
                disabled={pending}
                onChange={(event) => setDesignation(event.target.value)}
              />
              <TextInput
                label={t('auth.department')}
                value={department}
                disabled={pending}
                onChange={(event) => setDepartment(event.target.value)}
              />
              <TextInput
                label={t('field.district')}
                value={district}
                disabled={pending}
                onChange={(event) => setDistrict(event.target.value)}
              />
              <TextInput
                label={t('auth.employeeId')}
                value={employeeId}
                disabled={pending}
                onChange={(event) => setEmployeeId(event.target.value)}
                wrapperClassName="sm:col-span-2"
              />
            </div>

            <div className="mt-4">
              <TextArea
                label={t('auth.justification')}
                hint={t('auth.justificationHint')}
                error={validation}
                rows={4}
                value={justification}
                disabled={pending}
                onChange={(event) => setJustification(event.target.value)}
              />
            </div>

            <div className="mt-4 flex justify-end">
              <Button onClick={send} loading={submit.pending} disabled={pending}>
                {t('common.submit')}
              </Button>
            </div>
          </CardBody>
        </Card>
      )}

      <Card className="mt-6">
        <CardHeader title={t('auth.myRequests')} />
        <CardBody>
          {mine.loading ? (
            <Spinner label={t('common.loading')} />
          ) : (mine.data?.length ?? 0) === 0 ? (
            <p className="text-sm text-ink-500">{t('common.empty')}</p>
          ) : (
            <ul className="space-y-3">
              {mine.data?.map((item) => {
                const Icon = STATUS_ICON[item.status]
                return (
                  <li key={item.id} className="rounded-lg border border-ink-200 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <Badge tone={STATUS_TONE[item.status]}>
                          <Icon className="h-3 w-3" aria-hidden />
                          {tEnum('accessRequestStatus', item.status)}
                        </Badge>
                        <span className="text-sm font-medium text-ink-800">
                          {t(`auth.role.${item.requested_role}` as const)}
                        </span>
                      </div>
                      <span className="text-xs text-ink-500">
                        {formatDateTime(item.created_at)}
                      </span>
                    </div>
                    <p className="mt-2 text-sm leading-relaxed text-ink-700">
                      {item.justification}
                    </p>
                    {item.decided_by_name ? (
                      <div
                        className={`mt-3 rounded border px-3 py-2 text-xs leading-relaxed ${
                          item.status === 'Rejected'
                            ? 'border-[#e8adad] bg-[#fbe3e3] text-[#6d1414]'
                            : 'border-moss-300 bg-moss-50 text-moss-900'
                        }`}
                      >
                        <p className="font-semibold">
                          {item.status === 'Rejected'
                            ? t('auth.requestDeclined')
                            : t('auth.requestApproved')}
                        </p>
                        <p className="mt-0.5">
                          {t('auth.decidedBy')} {item.decided_by_name} ·{' '}
                          {formatDateTime(item.decided_at)}
                        </p>
                        {item.decision_note ? (
                          <p className="mt-1.5">
                            <span className="font-semibold">{t('auth.decisionNote')}:</span>{' '}
                            {item.decision_note}
                          </p>
                        ) : null}
                      </div>
                    ) : null}
                  </li>
                )
              })}
            </ul>
          )}
        </CardBody>
      </Card>
    </div>
  )
}
