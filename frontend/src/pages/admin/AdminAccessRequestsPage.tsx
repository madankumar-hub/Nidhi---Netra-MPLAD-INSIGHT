import { useState } from 'react'
import { CheckCircle2, Clock, ShieldAlert, ShieldCheck, UserMinus, XCircle } from 'lucide-react'
import { adminApi } from '@/api'
import { useApi, useMutation } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { PageHeader } from '@/components/layout/PageHeader'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { SelectInput, TextArea } from '@/components/ui/Field'
import { DataTable } from '@/components/ui/Table'
import type { Column } from '@/components/ui/Table'
import { SkeletonRows } from '@/components/ui/Spinner'
import { EmptyState, ErrorState, InlineMessage } from '@/components/ui/States'
import { formatDateTime } from '@/utils/format'
import type { AccessRequest, AccessRequestStatus, User, UserRole } from '@/types'

const STATUS_TONE: Record<AccessRequestStatus, 'warning' | 'success' | 'critical' | 'neutral'> = {
  Pending: 'warning',
  Approved: 'success',
  Rejected: 'critical',
  Withdrawn: 'neutral',
}

const ROLE_TONE: Record<UserRole, 'neutral' | 'info' | 'success' | 'danger'> = {
  citizen: 'neutral',
  officer: 'info',
  auditor: 'success',
  admin: 'danger',
}

export function AdminAccessRequestsPage() {
  const { t } = useI18n()
  const [version, setVersion] = useState(0)
  const [openId, setOpenId] = useState<number | null>(null)
  const [grantRole, setGrantRole] = useState<UserRole>('officer')
  const [note, setNote] = useState('')
  const [message, setMessage] = useState<string | null>(null)

  const requests = useApi((signal) => adminApi.listAccessRequests({}, signal), [version])
  const policy = useApi((signal) => adminApi.getAccessPolicy(signal), [])
  const users = useApi((signal) => adminApi.listUsers({}, signal), [version])
  const decide = useMutation(adminApi.decideAccessRequest)
  const revoke = useMutation(adminApi.revokeOfficialRole)

  const reload = () => setVersion((value) => value + 1)

  const act = async (request: AccessRequest, approve: boolean) => {
    const result = await decide.run(request.id, {
      approve,
      granted_role: approve ? grantRole : undefined,
      note: note.trim() || undefined,
    })
    if (result) {
      setOpenId(null)
      setNote('')
      setMessage(
        approve
          ? `${result.full_name} is now ${t(`auth.role.${result.granted_role ?? 'officer'}` as const)}.`
          : `Request from ${result.full_name} declined.`,
      )
      reload()
    }
  }

  const pending = (requests.data ?? []).filter((item) => item.status === 'Pending')
  const decided = (requests.data ?? []).filter((item) => item.status !== 'Pending')
  const officials = (users.data ?? []).filter((item) => item.role !== 'citizen')

  const userColumns: Column<User>[] = [
    {
      key: 'name',
      header: t('auth.fullName'),
      render: (row) => (
        <div>
          <p className="text-sm font-medium text-ink-900">{row.full_name}</p>
          <p className="text-xs text-ink-500">{row.email}</p>
        </div>
      ),
    },
    {
      key: 'role',
      header: t('field.status'),
      render: (row) => <Badge tone={ROLE_TONE[row.role]}>{t(`auth.role.${row.role}` as const)}</Badge>,
    },
    {
      key: 'posting',
      header: t('auth.designation'),
      secondary: true,
      render: (row) => (
        <div className="text-xs text-ink-600">
          <p>{row.designation ?? '—'}</p>
          <p>{[row.department, row.district].filter(Boolean).join(' · ') || '—'}</p>
        </div>
      ),
    },
    {
      key: 'actions',
      header: '',
      align: 'right',
      render: (row) =>
        row.role === 'admin' ? (
          <span className="text-xs text-ink-400">—</span>
        ) : (
          <Button
            variant="secondary"
            size="sm"
            loading={revoke.pending}
            icon={<UserMinus className="h-3.5 w-3.5" aria-hidden />}
            onClick={async () => {
              const result = await revoke.run(row.id)
              if (result) {
                setMessage(t('admin.revoked'))
                reload()
              }
            }}
          >
            {t('admin.revoke')}
          </Button>
        ),
    },
  ]

  return (
    <div>
      <PageHeader title={t('admin.accessTitle')} description={t('admin.accessSubtitle')} />

      {message ? (
        <div className="mb-4">
          <InlineMessage tone="success">{message}</InlineMessage>
        </div>
      ) : null}
      {decide.error ? (
        <div className="mb-4">
          <InlineMessage tone="warning">{decide.error.message}</InlineMessage>
        </div>
      ) : null}

      {policy.data ? (
        <div className="mb-5 flex items-start gap-2 rounded-lg border border-ink-200 bg-white px-4 py-3 text-xs leading-relaxed text-ink-600">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-ink-400" aria-hidden />
          <span>
            {policy.data.enforced && policy.data.domains.length > 0 ? (
              <>
                {t('auth.allowlistNote')}{' '}
                <span className="font-medium text-ink-800">
                  {policy.data.domains.map((domain) => `@${domain}`).join(', ')}
                </span>
                {policy.data.explicit_addresses > 0
                  ? `, plus ${policy.data.explicit_addresses} named address(es).`
                  : '.'}
              </>
            ) : (
              t('auth.allowlistOpen')
            )}{' '}
            {t('auth.adminNeverRequestable')}
          </span>
        </div>
      ) : null}

      <Card>
        <CardHeader
          title={t('admin.accessPending')}
          icon={<Clock className="h-4 w-4" aria-hidden />}
          actions={
            pending.length > 0 ? <Badge tone="warning">{pending.length}</Badge> : undefined
          }
        />
        <CardBody>
          {requests.loading ? (
            <SkeletonRows rows={3} />
          ) : requests.error ? (
            <ErrorState error={requests.error} onRetry={requests.reload} retryLabel={t('common.retry')} />
          ) : pending.length === 0 ? (
            <EmptyState title={t('admin.accessNone')} icon={<CheckCircle2 className="h-8 w-8" aria-hidden />} />
          ) : (
            <ul className="space-y-3">
              {pending.map((item) => (
                <li key={item.id} className="rounded-lg border border-ink-200 p-4">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-ink-900">{item.full_name}</p>
                      <p className="text-xs text-ink-500">{item.email}</p>
                    </div>
                    <div className="flex flex-wrap items-center gap-1.5">
                      <Badge tone={ROLE_TONE[item.requested_role]}>
                        {t(`auth.role.${item.requested_role}` as const)}
                      </Badge>
                      <Badge
                        tone={item.email_allowlisted ? 'success' : 'warning'}
                        title={
                          item.email_allowlisted
                            ? t('admin.allowlisted')
                            : t('admin.notAllowlisted')
                        }
                      >
                        {item.email_allowlisted ? (
                          <ShieldCheck className="h-3 w-3" aria-hidden />
                        ) : (
                          <ShieldAlert className="h-3 w-3" aria-hidden />
                        )}
                        {item.email_allowlisted
                          ? t('admin.allowlisted')
                          : t('admin.notAllowlisted')}
                      </Badge>
                      <span className="text-xs text-ink-500">
                        {formatDateTime(item.created_at)}
                      </span>
                    </div>
                  </div>

                  <dl className="mt-3 grid grid-cols-2 gap-x-6 gap-y-1 text-xs sm:grid-cols-4">
                    <div>
                      <dt className="data-label">{t('auth.designation')}</dt>
                      <dd className="text-ink-800">{item.designation ?? '—'}</dd>
                    </div>
                    <div>
                      <dt className="data-label">{t('auth.department')}</dt>
                      <dd className="text-ink-800">{item.department ?? '—'}</dd>
                    </div>
                    <div>
                      <dt className="data-label">{t('field.district')}</dt>
                      <dd className="text-ink-800">{item.district ?? '—'}</dd>
                    </div>
                    <div>
                      <dt className="data-label">{t('auth.employeeId')}</dt>
                      <dd className="text-ink-800">{item.employee_id ?? '—'}</dd>
                    </div>
                  </dl>

                  <p className="mt-3 rounded bg-ink-50 px-3 py-2 text-sm leading-relaxed text-ink-700">
                    {item.justification}
                  </p>

                  {openId === item.id ? (
                    <div className="mt-3 space-y-3 rounded-md border border-ink-200 bg-ink-50/60 p-3">
                      <SelectInput
                        label={t('admin.grantAs')}
                        value={grantRole}
                        options={[
                          { label: t('auth.role.officer'), value: 'officer' },
                          { label: t('auth.role.auditor'), value: 'auditor' },
                        ]}
                        onChange={(event) => setGrantRole(event.target.value as UserRole)}
                      />
                      <TextArea
                        label={t('admin.decisionNote')}
                        rows={2}
                        value={note}
                        onChange={(event) => setNote(event.target.value)}
                      />
                      <div className="flex flex-wrap justify-end gap-2">
                        <Button variant="secondary" size="sm" onClick={() => setOpenId(null)}>
                          {t('common.cancel')}
                        </Button>
                        <Button
                          variant="danger"
                          size="sm"
                          loading={decide.pending}
                          icon={<XCircle className="h-3.5 w-3.5" aria-hidden />}
                          onClick={() => act(item, false)}
                        >
                          {t('admin.decline')}
                        </Button>
                        <Button
                          size="sm"
                          loading={decide.pending}
                          icon={<CheckCircle2 className="h-3.5 w-3.5" aria-hidden />}
                          onClick={() => act(item, true)}
                        >
                          {t('admin.approve')}
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <Button
                      variant="secondary"
                      size="sm"
                      className="mt-3"
                      onClick={() => {
                        setOpenId(item.id)
                        setGrantRole(item.requested_role)
                        setNote('')
                      }}
                    >
                      Review
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </CardBody>
      </Card>

      <Card className="mt-6">
        <CardHeader title={t('admin.accountsTitle')} description={`${officials.length} official account(s)`} />
        <CardBody>
          {users.loading ? (
            <SkeletonRows rows={4} />
          ) : users.error ? (
            <ErrorState error={users.error} onRetry={users.reload} retryLabel={t('common.retry')} />
          ) : officials.length === 0 ? (
            <EmptyState title={t('common.empty')} />
          ) : (
            <DataTable
              columns={userColumns}
              rows={officials}
              rowKey={(row) => row.id}
              caption={t('admin.accountsTitle')}
            />
          )}
        </CardBody>
      </Card>

      {decided.length > 0 ? (
        <Card className="mt-6">
          <CardHeader title={t('admin.accessDecided')} />
          <CardBody>
            <ul className="divide-y divide-ink-100">
              {decided.map((item) => (
                <li key={item.id} className="flex flex-wrap items-center justify-between gap-2 py-2.5">
                  <div className="min-w-0">
                    <p className="text-sm text-ink-800">
                      {item.full_name}{' '}
                      <span className="text-xs text-ink-500">({item.email})</span>
                    </p>
                    {item.decision_note ? (
                      <p className="text-xs text-ink-500">{item.decision_note}</p>
                    ) : null}
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge tone={STATUS_TONE[item.status]}>{item.status}</Badge>
                    <span className="text-xs text-ink-500">
                      {item.decided_by_name} · {formatDateTime(item.decided_at)}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          </CardBody>
        </Card>
      ) : null}
    </div>
  )
}
