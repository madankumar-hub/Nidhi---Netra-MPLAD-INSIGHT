import { useState } from 'react'
import { adminApi, projectsAdminApi } from '@/api'
import { useMutation } from '@/hooks/useApi'
import { useI18n } from '@/i18n'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { SelectInput, TextArea, TextInput } from '@/components/ui/Field'
import { InlineMessage } from '@/components/ui/States'
import { PROJECT_STATUSES } from '@/utils/constants'
import type { ProjectAdminDetail, ProjectCreatePayload, ProjectStatus } from '@/types'

interface ProjectFormDialogProps {
  open: boolean
  /** Omit to create a new record; supply to edit an existing one. */
  project?: ProjectAdminDetail | null
  onClose: () => void
  onSaved: () => void
}

const EMPTY: ProjectCreatePayload = {
  title: '',
  description: '',
  mp_name: '',
  constituency: '',
  house: 'Lok Sabha',
  state: '',
  district: '',
  block: '',
  location: '',
  category: '',
  executing_agency: '',
  contractor: '',
  sanction_year: new Date().getFullYear(),
  sanction_date: '',
  start_date: '',
  planned_end_date: '',
  allocated_amount: 0,
  spent_amount: 0,
  estimated_cost: undefined,
  progress_percent: 0,
  status: 'Not Started',
  beneficiaries: undefined,
  remarks: '',
}

export function ProjectFormDialog({ open, project, onClose, onSaved }: ProjectFormDialogProps) {
  const { t } = useI18n()
  const editing = Boolean(project)
  const [form, setForm] = useState<ProjectCreatePayload>(
    project
      ? {
          title: project.title,
          description: project.description,
          mp_name: project.mp_name,
          constituency: project.constituency ?? '',
          house: project.house,
          state: project.state,
          district: project.district,
          block: project.block ?? '',
          location: project.location ?? '',
          category: project.category,
          executing_agency: project.executing_agency,
          contractor: project.contractor ?? '',
          sanction_year: project.sanction_year,
          sanction_date: project.sanction_date ?? '',
          start_date: project.start_date ?? '',
          planned_end_date: project.planned_end_date ?? '',
          allocated_amount: project.allocated_amount,
          spent_amount: project.spent_amount,
          estimated_cost: project.estimated_cost ?? undefined,
          progress_percent: project.progress_percent,
          status: project.status,
          beneficiaries: project.beneficiaries ?? undefined,
          remarks: project.remarks ?? '',
        }
      : EMPTY,
  )
  const [validation, setValidation] = useState<string | null>(null)

  const create = useMutation(projectsAdminApi.createProject)
  const update = useMutation(adminApi.updateProject)

  const set = <K extends keyof ProjectCreatePayload>(key: K, value: ProjectCreatePayload[K]) =>
    setForm((current) => ({ ...current, [key]: value }))

  const submit = async () => {
    if (form.title.trim().length < 4) {
      setValidation('A title of at least 4 characters is required.')
      return
    }
    for (const key of ['mp_name', 'state', 'district', 'category', 'executing_agency'] as const) {
      if (!String(form[key] ?? '').trim()) {
        setValidation('All starred fields are required.')
        return
      }
    }
    setValidation(null)

    // Drop blank optional fields so the API keeps its own defaults.
    const payload: Record<string, unknown> = {}
    Object.entries(form).forEach(([key, value]) => {
      if (value !== '' && value !== undefined && value !== null) payload[key] = value
    })

    const result = project
      ? await update.run(project.id, payload)
      : await create.run(payload as unknown as ProjectCreatePayload)
    if (result) {
      onSaved()
      onClose()
    }
  }

  const error = create.error ?? update.error

  return (
    <Modal
      open={open}
      size="lg"
      title={editing ? 'Edit work record' : 'New work record'}
      onClose={onClose}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            {t('common.cancel')}
          </Button>
          <Button onClick={submit} loading={create.pending || update.pending}>
            {t('common.save')}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        {error ? <InlineMessage tone="warning">{error.message}</InlineMessage> : null}
        {validation ? <InlineMessage tone="warning">{validation}</InlineMessage> : null}

        <TextInput
          label={t('field.title')}
          required
          value={form.title}
          onChange={(event) => set('title', event.target.value)}
        />
        <TextArea
          label={t('field.description')}
          rows={3}
          value={form.description}
          onChange={(event) => set('description', event.target.value)}
        />

        <div className="grid gap-4 sm:grid-cols-2">
          <TextInput
            label={t('field.mp')}
            required
            value={form.mp_name}
            onChange={(event) => set('mp_name', event.target.value)}
          />
          <TextInput
            label={t('field.constituency')}
            value={form.constituency ?? ''}
            onChange={(event) => set('constituency', event.target.value)}
          />
          <SelectInput
            label={t('field.house')}
            value={form.house}
            options={[
              { label: 'Lok Sabha', value: 'Lok Sabha' },
              { label: 'Rajya Sabha', value: 'Rajya Sabha' },
            ]}
            onChange={(event) => set('house', event.target.value)}
          />
          <TextInput
            label={t('field.state')}
            required
            value={form.state}
            onChange={(event) => set('state', event.target.value)}
          />
          <TextInput
            label={t('field.district')}
            required
            value={form.district}
            onChange={(event) => set('district', event.target.value)}
          />
          <TextInput
            label={t('field.block')}
            value={form.block ?? ''}
            onChange={(event) => set('block', event.target.value)}
          />
          <TextInput
            label={t('field.location')}
            value={form.location ?? ''}
            onChange={(event) => set('location', event.target.value)}
          />
          <TextInput
            label={t('field.category')}
            required
            value={form.category}
            onChange={(event) => set('category', event.target.value)}
          />
          <TextInput
            label={t('field.agency')}
            required
            value={form.executing_agency}
            onChange={(event) => set('executing_agency', event.target.value)}
          />
          <TextInput
            label={t('field.contractor')}
            value={form.contractor ?? ''}
            onChange={(event) => set('contractor', event.target.value)}
          />
          <TextInput
            label={t('field.sanctionYear')}
            type="number"
            min="1993"
            max="2100"
            required
            value={String(form.sanction_year)}
            onChange={(event) => set('sanction_year', Number(event.target.value))}
          />
          <TextInput
            label={t('field.sanctionDate')}
            type="date"
            value={form.sanction_date ?? ''}
            onChange={(event) => set('sanction_date', event.target.value)}
          />
          <TextInput
            label={t('field.startDate')}
            type="date"
            value={form.start_date ?? ''}
            onChange={(event) => set('start_date', event.target.value)}
          />
          <TextInput
            label={t('field.endDate')}
            type="date"
            value={form.planned_end_date ?? ''}
            onChange={(event) => set('planned_end_date', event.target.value)}
          />
          <TextInput
            label={`${t('field.allocated')} (₹ lakh)`}
            type="number"
            step="0.01"
            min="0"
            required
            value={String(form.allocated_amount)}
            onChange={(event) => set('allocated_amount', Number(event.target.value))}
          />
          <TextInput
            label={`${t('field.estimatedCost')} (₹ lakh)`}
            type="number"
            step="0.01"
            min="0"
            value={form.estimated_cost === undefined ? '' : String(form.estimated_cost)}
            onChange={(event) =>
              set('estimated_cost', event.target.value ? Number(event.target.value) : undefined)
            }
          />
          <SelectInput
            label={t('field.status')}
            value={form.status}
            options={PROJECT_STATUSES.map((item) => ({ label: item, value: item }))}
            onChange={(event) => set('status', event.target.value as ProjectStatus)}
          />
          <TextInput
            label={t('field.beneficiaries')}
            type="number"
            min="0"
            value={form.beneficiaries === undefined ? '' : String(form.beneficiaries)}
            onChange={(event) =>
              set('beneficiaries', event.target.value ? Number(event.target.value) : undefined)
            }
          />
        </div>

        <TextArea
          label={t('admin.remarks')}
          rows={2}
          value={form.remarks ?? ''}
          onChange={(event) => set('remarks', event.target.value)}
        />
      </div>
    </Modal>
  )
}
