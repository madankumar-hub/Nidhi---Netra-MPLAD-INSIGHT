import { useState } from 'react'
import { adminApi } from '@/api'
import { useMutation } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { SelectInput, TextArea } from '@/components/ui/Field'
import { InlineMessage } from '@/components/ui/States'
import { PROJECT_STATUSES } from '@/utils/constants'
import type { ProjectStatus } from '@/types'

export function StatusChangeDialog({
  open,
  projectId,
  currentStatus,
  onClose,
  onChanged,
}: {
  open: boolean
  projectId: number
  currentStatus: ProjectStatus
  onClose: () => void
  onChanged: () => void
}) {
  const { t } = useI18n()
  const [status, setStatus] = useState<ProjectStatus>(currentStatus)
  const [reason, setReason] = useState('')
  const [validation, setValidation] = useState<string | null>(null)
  const change = useMutation(adminApi.changeProjectStatus)

  const submit = async () => {
    if (reason.trim().length < 3) {
      setValidation(t('common.required'))
      return
    }
    if (status === currentStatus) {
      setValidation('Select a different status.')
      return
    }
    setValidation(null)
    const result = await change.run(projectId, status, reason.trim())
    if (result) {
      setReason('')
      onChanged()
      onClose()
    }
  }

  return (
    <Modal
      open={open}
      title={t('status.change')}
      onClose={onClose}
      size="sm"
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            {t('common.cancel')}
          </Button>
          <Button onClick={submit} loading={change.pending}>
            {t('common.save')}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {change.error ? <InlineMessage tone="warning">{change.error.message}</InlineMessage> : null}
        <p className="text-sm text-ink-600">
          {t('field.status')}: <span className="font-medium text-ink-900">{currentStatus}</span>
        </p>
        <SelectInput
          label={t('status.newStatus')}
          value={status}
          options={PROJECT_STATUSES.map((item) => ({ label: item, value: item }))}
          onChange={(event) => setStatus(event.target.value as ProjectStatus)}
        />
        <TextArea
          label={t('status.reason')}
          required
          error={validation}
          rows={3}
          value={reason}
          onChange={(event) => setReason(event.target.value)}
        />
      </div>
    </Modal>
  )
}
