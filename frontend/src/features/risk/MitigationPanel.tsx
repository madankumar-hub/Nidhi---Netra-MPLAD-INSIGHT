import { useState } from 'react'
import { CheckCircle2, ListChecks, Plus, UserCog } from 'lucide-react'
import { riskApi } from '@/api'
import { useApi, useMutation } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { Badge, MitigationBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { Modal } from '@/components/ui/Modal'
import { SelectInput, TextArea, TextInput } from '@/components/ui/Field'
import { SkeletonRows } from '@/components/ui/Spinner'
import { EmptyState, ErrorState, InlineMessage } from '@/components/ui/States'
import { formatDate, formatDateTime } from '@/utils/format'
import { MITIGATION_STATUSES } from '@/utils/constants'
import type { MitigationStatus } from '@/types'

const PRIORITIES = [
  { value: '1', key: 'mitigation.priority1' },
  { value: '2', key: 'mitigation.priority2' },
  { value: '3', key: 'mitigation.priority3' },
] as const

export function MitigationPanel({ projectId, canAct }: { projectId: number; canAct: boolean }) {
  const { t } = useI18n()
  const [version, setVersion] = useState(0)
  const [open, setOpen] = useState(false)
  const [action, setAction] = useState('')
  const [responsible, setResponsible] = useState('Executing Agency')
  const [priority, setPriority] = useState('2')
  const [dueDate, setDueDate] = useState('')
  const [notes, setNotes] = useState('')
  const [validation, setValidation] = useState<string | null>(null)

  const list = useApi((signal) => riskApi.listMitigation(projectId, signal), [projectId, version])
  const create = useMutation(riskApi.addMitigation)
  const update = useMutation(riskApi.updateMitigation)
  const resolve = useMutation(riskApi.resolveMitigation)

  const reload = () => setVersion((value) => value + 1)

  const submit = async () => {
    if (action.trim().length < 4) {
      setValidation(t('common.required'))
      return
    }
    setValidation(null)
    const created = await create.run(projectId, {
      action: action.trim(),
      responsible_party: responsible.trim(),
      priority: Number(priority),
      due_date: dueDate || undefined,
      notes: notes.trim() || undefined,
    })
    if (created) {
      setAction('')
      setNotes('')
      setDueDate('')
      setOpen(false)
      reload()
    }
  }

  const changeStatus = async (id: number, status: MitigationStatus) => {
    const result = await update.run(id, { status })
    if (result) reload()
  }

  const markResolved = async (id: number) => {
    const result = await resolve.run(id)
    if (result) reload()
  }

  return (
    <Card>
      <CardHeader
        title={t('mitigation.title')}
        description={t('mitigation.subtitle')}
        icon={<ListChecks className="h-4 w-4" aria-hidden />}
        actions={
          canAct ? (
            <Button size="sm" onClick={() => setOpen(true)} icon={<Plus className="h-3.5 w-3.5" aria-hidden />}>
              {t('mitigation.addAction')}
            </Button>
          ) : undefined
        }
      />
      <CardBody>
        {list.loading ? (
          <SkeletonRows rows={4} />
        ) : list.error ? (
          <ErrorState error={list.error} onRetry={list.reload} retryLabel={t('common.retry')} />
        ) : (list.data?.length ?? 0) === 0 ? (
          <EmptyState title={t('mitigation.none')} />
        ) : (
          <ul className="space-y-3">
            {list.data?.map((item) => (
              <li key={item.id} className="rounded-lg border border-ink-200 p-4">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <p className="min-w-0 flex-1 text-sm leading-relaxed text-ink-800">{item.action}</p>
                  <MitigationBadge status={item.status} />
                </div>

                <div className="mt-2.5 flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-ink-600">
                  <span className="inline-flex items-center gap-1.5">
                    <UserCog className="h-3.5 w-3.5 text-ink-400" aria-hidden />
                    {item.responsible_party || t('common.notRecorded')}
                  </span>
                  <span>
                    {t('mitigation.priority')}:{' '}
                    {t(`mitigation.priority${item.priority}` as 'mitigation.priority1')}
                  </span>
                  <span>
                    {t('mitigation.dueDate')}: {formatDate(item.due_date)}
                  </span>
                  {item.risk_factor_code ? (
                    <span className="font-mono text-[11px] text-ink-400">{item.risk_factor_code}</span>
                  ) : null}
                  {item.is_system_recommended ? (
                    <Badge tone="neutral">{t('mitigation.systemRecommended')}</Badge>
                  ) : null}
                </div>

                {item.notes ? (
                  <p className="mt-2 rounded bg-ink-50 px-2.5 py-2 text-xs leading-relaxed text-ink-700">
                    {item.notes}
                  </p>
                ) : null}

                {item.resolved_at ? (
                  <p className="mt-2 text-xs text-moss-700">
                    {t('mitigation.resolvedBy')} {item.resolved_by_name} ·{' '}
                    {formatDateTime(item.resolved_at)}
                  </p>
                ) : null}

                {canAct && item.status !== 'Resolved' ? (
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    {MITIGATION_STATUSES.filter(
                      (status) => status !== item.status && status !== 'Resolved',
                    ).map((status) => (
                      <Button
                        key={status}
                        variant="secondary"
                        size="sm"
                        loading={update.pending}
                        onClick={() => changeStatus(item.id, status)}
                      >
                        {status}
                      </Button>
                    ))}
                    <Button
                      variant="secondary"
                      size="sm"
                      loading={resolve.pending}
                      onClick={() => markResolved(item.id)}
                      icon={<CheckCircle2 className="h-3.5 w-3.5" aria-hidden />}
                    >
                      {t('mitigation.markResolved')}
                    </Button>
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </CardBody>

      <Modal
        open={open}
        title={t('mitigation.addAction')}
        onClose={() => setOpen(false)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setOpen(false)}>
              {t('common.cancel')}
            </Button>
            <Button onClick={submit} loading={create.pending}>
              {t('common.save')}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {create.error ? <InlineMessage tone="warning">{create.error.message}</InlineMessage> : null}
          <TextArea
            label={t('mitigation.action')}
            required
            error={validation}
            value={action}
            rows={3}
            onChange={(event) => setAction(event.target.value)}
          />
          <TextInput
            label={t('mitigation.responsible')}
            value={responsible}
            onChange={(event) => setResponsible(event.target.value)}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <SelectInput
              label={t('mitigation.priority')}
              value={priority}
              options={PRIORITIES.map((item) => ({ label: t(item.key), value: item.value }))}
              onChange={(event) => setPriority(event.target.value)}
            />
            <TextInput
              label={t('mitigation.dueDate')}
              type="date"
              value={dueDate}
              onChange={(event) => setDueDate(event.target.value)}
            />
          </div>
          <TextArea
            label={t('mitigation.notes')}
            value={notes}
            rows={2}
            onChange={(event) => setNotes(event.target.value)}
          />
        </div>
      </Modal>
    </Card>
  )
}
