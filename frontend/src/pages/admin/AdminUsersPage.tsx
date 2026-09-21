/**
 * Accounts - who currently holds an official role, and revoking one.
 *
 * The approval workflow answers "how does someone become an official". This
 * page answers the other half a reviewer will ask: "who is one right now, and
 * how do we take it back". Administrator only, and the API enforces that
 * independently of this route.
 *
 * Revoking demotes the account to Citizen - it never deletes it, so the
 * person's history and the audit trail stay intact.
 */
import { useCallback, useState } from 'react'
import { ShieldCheck, UserMinus } from 'lucide-react'
import { adminApi } from '@/api'
import { useApi, useMutation } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { PageHeader } from '@/components/layout/PageHeader'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardBody } from '@/components/ui/Card'
import { SelectInput, TextArea } from '@/components/ui/Field'
import { Modal } from '@/components/ui/Modal'
import { DataTable } from '@/components/ui/Table'
import type { Column } from '@/components/ui/Table'
import { SkeletonRows } from '@/components/ui/Spinner'
import { EmptyState, ErrorState, InlineMessage } from '@/components/ui/States'
import { formatDateTime } from '@/utils/format'
import type { User, UserRole } from '@/types'

const ROLE_TONE: Record<UserRole, 'neutral' | 'info' | 'success' | 'danger'> = {
  citizen: 'neutral',
  officer: 'info',
  auditor: 'success',
  admin: 'danger',
}

export function AdminUsersPage() {
  const { t, tEnum } = useI18n()
  const [roleFilter, setRoleFilter] = useState<UserRole | ''>('')
  const [target, setTarget] = useState<User | null>(null)
  const [note, setNote] = useState('')

  const users = useApi(
    (signal) => adminApi.listUsers({ role: roleFilter }, signal),
    [roleFilter],
  )
  const revoke = useMutation(({ userId, reason }: { userId: number; reason: string }) =>
    adminApi.revokeOfficialRole(userId, reason),
  )

  const confirmRevoke = useCallback(async () => {
    if (!target) return
    const result = await revoke.run({ userId: target.id, reason: note.trim() })
    if (result) {
      setTarget(null)
      setNote('')
      users.reload()
    }
  }, [target, note, revoke, users])

  const columns: Column<User>[] = [
    {
      key: 'full_name',
      header: t('admin.accountName'),
      render: (row) => (
        <div className="min-w-0">
          <p className="text-sm font-medium text-ink-900">{row.full_name}</p>
          <p className="truncate text-xs text-ink-500">{row.email}</p>
        </div>
      ),
    },
    {
      key: 'role',
      header: t('auth.requestedRole'),
      render: (row) => <Badge tone={ROLE_TONE[row.role] ?? 'neutral'}>{tEnum('userRole', row.role)}</Badge>,
    },
    {
      key: 'designation',
      header: t('auth.designation'),
      render: (row) => (
        <span className="text-sm text-ink-700">{row.designation || t('common.notRecorded')}</span>
      ),
    },
    {
      key: 'last_login_at',
      header: t('admin.lastSignIn'),
      render: (row) => (
        <span className="text-xs text-ink-600">
          {row.last_login_at ? formatDateTime(row.last_login_at) : t('common.notRecorded')}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      width: '1%',
      render: (row) =>
        // An administrator is never revocable from here, and neither is your
        // own account - both rules are enforced again server-side.
        row.role === 'citizen' || row.role === 'admin' ? null : (
          <Button
            variant="secondary"
            size="sm"
            onClick={() => {
              setTarget(row)
              setNote('')
            }}
            icon={<UserMinus className="h-3.5 w-3.5" aria-hidden />}
          >
            {t('admin.revoke')}
          </Button>
        ),
    },
  ]

  return (
    <div>
      <PageHeader title={t('nav.users')} description={t('admin.accountsSubtitle')} />

      <Card className="mb-4">
        <CardBody>
          <div className="max-w-xs">
            <SelectInput
              label={t('auth.requestedRole')}
              value={roleFilter}
              placeholder={t('common.all')}
              options={[
                { label: tEnum('userRole', 'officer'), value: 'officer' },
                { label: tEnum('userRole', 'auditor'), value: 'auditor' },
                { label: tEnum('userRole', 'admin'), value: 'admin' },
                { label: tEnum('userRole', 'citizen'), value: 'citizen' },
              ]}
              onChange={(event) => setRoleFilter(event.target.value as UserRole | '')}
            />
          </div>
        </CardBody>
      </Card>

      {revoke.error ? (
        <div className="mb-4">
          <InlineMessage tone="warning">{revoke.error.message}</InlineMessage>
        </div>
      ) : null}

      {users.loading ? (
        <SkeletonRows rows={6} />
      ) : users.error ? (
        <ErrorState error={users.error} onRetry={users.reload} />
      ) : (users.data?.length ?? 0) === 0 ? (
        <EmptyState
          icon={<ShieldCheck className="h-8 w-8" aria-hidden />}
          title={t('common.empty')}
          description={t('admin.accountsEmpty')}
        />
      ) : (
        <DataTable rows={users.data ?? []} columns={columns} rowKey={(row) => row.id} />
      )}

      <Modal
        open={target !== null}
        title={t('admin.revokeTitle')}
        onClose={() => setTarget(null)}
      >
        <div className="space-y-4">
          <InlineMessage tone="warning">{t('admin.revokeWarning')}</InlineMessage>
          {target ? (
            <p className="text-sm text-ink-800">
              <span className="font-semibold">{target.full_name}</span> ({target.email}) —{' '}
              {tEnum('userRole', target.role)}
            </p>
          ) : null}
          <TextArea
            label={t('admin.decisionNote')}
            hint={t('admin.revokeNoteHint')}
            rows={3}
            value={note}
            onChange={(event) => setNote(event.target.value)}
          />
        </div>
        <div className="mt-6 flex justify-end gap-2">
          <Button variant="ghost" onClick={() => setTarget(null)}>
            {t('common.cancel')}
          </Button>
          <Button
            onClick={confirmRevoke}
            loading={revoke.pending}
            icon={<UserMinus className="h-4 w-4" aria-hidden />}
          >
            {t('admin.revoke')}
          </Button>
        </div>
      </Modal>
    </div>
  )
}
