import { useState } from 'react'
import { projectsApi } from '@/api'
import { useMutation } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { SelectInput, TextArea } from '@/components/ui/Field'
import { InlineMessage } from '@/components/ui/States'
import { CITIZEN_REPORT_CATEGORIES } from '@/utils/constants'
import type { CitizenReport, CitizenReportCategory } from '@/types'

interface ReportIssueDialogProps {
  open: boolean
  projectId: number
  onClose: () => void
  onSubmitted: (report: CitizenReport) => void
}

export function ReportIssueDialog({ open, projectId, onClose, onSubmitted }: ReportIssueDialogProps) {
  const { t } = useI18n()
  const [category, setCategory] = useState<CitizenReportCategory>('Work Not Started')
  const [description, setDescription] = useState('')
  const [validation, setValidation] = useState<string | null>(null)
  const { run, pending, error } = useMutation(projectsApi.fileCitizenReport)

  const submit = async () => {
    if (description.trim().length < 10) {
      setValidation(t('report.descriptionHint'))
      return
    }
    setValidation(null)
    const report = await run(projectId, { category, description: description.trim() })
    if (report) {
      setDescription('')
      onSubmitted(report)
      onClose()
    }
  }

  return (
    <Modal
      open={open}
      title={t('report.title')}
      onClose={onClose}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            {t('common.cancel')}
          </Button>
          <Button onClick={submit} loading={pending}>
            {t('common.submit')}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {error ? <InlineMessage tone="warning">{error.message}</InlineMessage> : null}
        <SelectInput
          label={t('report.category')}
          value={category}
          options={CITIZEN_REPORT_CATEGORIES.map((item) => ({ label: item, value: item }))}
          onChange={(event) => setCategory(event.target.value as CitizenReportCategory)}
        />
        <TextArea
          label={t('report.description')}
          hint={t('report.descriptionHint')}
          error={validation}
          value={description}
          rows={5}
          maxLength={2000}
          onChange={(event) => setDescription(event.target.value)}
        />
      </div>
    </Modal>
  )
}
