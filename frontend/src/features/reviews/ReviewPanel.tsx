import { useState } from 'react'
import { ClipboardCheck, Plus } from 'lucide-react'
import { workflowApi } from '@/api'
import { useApi, useMutation } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { Badge, ReviewStatusBadge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { Modal } from '@/components/ui/Modal'
import { Checkbox, SelectInput, TextArea, TextInput } from '@/components/ui/Field'
import { SkeletonRows } from '@/components/ui/Spinner'
import { EmptyState, ErrorState, InlineMessage } from '@/components/ui/States'
import { formatDateTime } from '@/utils/format'
import { REVIEW_STATUSES } from '@/utils/constants'
import type { ReviewStatus } from '@/types'

export function ReviewPanel({
  projectId,
  canAct,
  onReviewed,
}: {
  projectId: number
  canAct: boolean
  onReviewed?: () => void
}) {
  const { t } = useI18n()
  const [version, setVersion] = useState(0)
  const [open, setOpen] = useState(false)
  const [status, setStatus] = useState<ReviewStatus>('Reviewed')
  const [findings, setFindings] = useState('')
  const [notes, setNotes] = useState('')
  const [actionRequired, setActionRequired] = useState('')
  const [escalatedTo, setEscalatedTo] = useState('')
  const [followUp, setFollowUp] = useState(false)
  const [validation, setValidation] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const list = useApi((signal) => workflowApi.listReviews(projectId, signal), [projectId, version])
  const create = useMutation(workflowApi.createReview)

  const submit = async () => {
    if (findings.trim().length < 3) {
      setValidation(t('common.required'))
      return
    }
    setValidation(null)
    const review = await create.run(projectId, {
      status,
      findings: findings.trim(),
      notes: notes.trim() || undefined,
      action_required: actionRequired.trim() || undefined,
      escalated_to: escalatedTo.trim() || undefined,
      follow_up_required: followUp,
    })
    if (review) {
      setFindings('')
      setNotes('')
      setActionRequired('')
      setEscalatedTo('')
      setFollowUp(false)
      setOpen(false)
      setMessage(t('review.submitted'))
      setVersion((value) => value + 1)
      onReviewed?.()
    }
  }

  return (
    <Card>
      <CardHeader
        title={t('review.title')}
        description={t('review.subtitle')}
        icon={<ClipboardCheck className="h-4 w-4" aria-hidden />}
        actions={
          canAct ? (
            <Button size="sm" onClick={() => setOpen(true)} icon={<Plus className="h-3.5 w-3.5" aria-hidden />}>
              {t('review.recordReview')}
            </Button>
          ) : undefined
        }
      />
      <CardBody>
        {message ? (
          <div className="mb-4">
            <InlineMessage tone="success">{message}</InlineMessage>
          </div>
        ) : null}

        {list.loading ? (
          <SkeletonRows rows={3} />
        ) : list.error ? (
          <ErrorState error={list.error} onRetry={list.reload} retryLabel={t('common.retry')} />
        ) : (list.data?.length ?? 0) === 0 ? (
          <EmptyState title={t('review.none')} />
        ) : (
          <ol className="space-y-3">
            {list.data?.map((review) => (
              <li key={review.id} className="rounded-lg border border-ink-200 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <ReviewStatusBadge status={review.status} />
                    {review.previous_status && review.previous_status !== review.status ? (
                      <span className="text-xs text-ink-500">
                        {review.previous_status} → {review.status}
                      </span>
                    ) : null}
                    {review.follow_up_required ? (
                      <Badge tone="warning">{t('review.followUp')}</Badge>
                    ) : null}
                  </div>
                  <span className="text-xs text-ink-500">{formatDateTime(review.review_date)}</span>
                </div>

                <p className="mt-2 text-sm leading-relaxed text-ink-800">{review.findings}</p>

                {review.action_required ? (
                  <p className="mt-2 rounded bg-ink-50 px-2.5 py-2 text-xs leading-relaxed text-ink-700">
                    <span className="font-semibold">{t('review.actionRequired')}: </span>
                    {review.action_required}
                  </p>
                ) : null}
                {review.notes ? (
                  <p className="mt-2 text-xs leading-relaxed text-ink-600">{review.notes}</p>
                ) : null}

                <p className="mt-2.5 text-xs text-ink-500">
                  {t('review.reviewer')}: {review.reviewer_name} ({review.reviewer_role})
                  {review.escalated_to ? ` · ${t('review.escalatedTo')}: ${review.escalated_to}` : ''}
                </p>
              </li>
            ))}
          </ol>
        )}
      </CardBody>

      <Modal
        open={open}
        title={t('review.recordReview')}
        onClose={() => setOpen(false)}
        footer={
          <>
            <Button variant="secondary" onClick={() => setOpen(false)}>
              {t('common.cancel')}
            </Button>
            <Button onClick={submit} loading={create.pending}>
              {t('common.submit')}
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          {create.error ? <InlineMessage tone="warning">{create.error.message}</InlineMessage> : null}
          <SelectInput
            label={t('review.outcome')}
            value={status}
            options={REVIEW_STATUSES.map((item) => ({ label: item, value: item }))}
            onChange={(event) => setStatus(event.target.value as ReviewStatus)}
          />
          <TextArea
            label={t('review.findings')}
            required
            error={validation}
            value={findings}
            rows={4}
            onChange={(event) => setFindings(event.target.value)}
          />
          <TextArea
            label={t('review.actionRequired')}
            value={actionRequired}
            rows={2}
            onChange={(event) => setActionRequired(event.target.value)}
          />
          <TextArea
            label={t('review.notes')}
            value={notes}
            rows={2}
            onChange={(event) => setNotes(event.target.value)}
          />
          {status === 'Escalated' ? (
            <TextInput
              label={t('review.escalatedTo')}
              value={escalatedTo}
              placeholder={t('admin.designationPlaceholder')}
              onChange={(event) => setEscalatedTo(event.target.value)}
            />
          ) : null}
          <Checkbox label={t('review.followUp')} checked={followUp} onChange={setFollowUp} />
        </div>
      </Modal>
    </Card>
  )
}
