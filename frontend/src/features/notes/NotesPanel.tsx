import { useState } from 'react'
import { Pin, Plus, StickyNote, Trash2 } from 'lucide-react'
import { workflowApi } from '@/api'
import { useApi, useMutation } from '@/hooks/useApi'
import { useAuth } from '@/features/auth/AuthContext'
import { useI18n } from '@/i18n'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { Checkbox, SelectInput, TextArea } from '@/components/ui/Field'
import { SkeletonRows } from '@/components/ui/Spinner'
import { EmptyState, ErrorState, InlineMessage } from '@/components/ui/States'
import { formatDateTime } from '@/utils/format'
import { NOTE_TYPES } from '@/utils/constants'
import type { NoteType } from '@/types'

const TYPE_TONE: Record<NoteType, 'neutral' | 'info' | 'warning' | 'danger'> = {
  'Review Note': 'info',
  'Risk Note': 'danger',
  'Delay Note': 'warning',
  'Action Note': 'info',
  'General Note': 'neutral',
}

export function NotesPanel({ projectId, canAct }: { projectId: number; canAct: boolean }) {
  const { t, tEnum } = useI18n()
  const { user, isAdmin } = useAuth()
  const [version, setVersion] = useState(0)
  const [filter, setFilter] = useState<NoteType | ''>('')
  const [content, setContent] = useState('')
  const [noteType, setNoteType] = useState<NoteType>('General Note')
  const [pinned, setPinned] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [validation, setValidation] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const list = useApi(
    (signal) => workflowApi.listNotes(projectId, filter, signal),
    [projectId, filter, version],
  )
  const create = useMutation(workflowApi.addNote)
  const remove = useMutation(workflowApi.deleteNote)

  const submit = async () => {
    if (content.trim().length < 2) {
      setValidation(t('common.required'))
      return
    }
    setValidation(null)
    const note = await create.run(projectId, {
      content: content.trim(),
      note_type: noteType,
      is_pinned: pinned,
    })
    if (note) {
      setContent('')
      setPinned(false)
      setShowForm(false)
      setMessage(t('notes.added'))
      setVersion((value) => value + 1)
    }
  }

  const handleDelete = async (id: number) => {
    const result = await remove.run(id)
    if (result) setVersion((value) => value + 1)
  }

  return (
    <Card>
      <CardHeader
        title={t('notes.title')}
        description={t('notes.subtitle')}
        icon={<StickyNote className="h-4 w-4" aria-hidden />}
        actions={
          canAct ? (
            <Button
              size="sm"
              onClick={() => setShowForm((open) => !open)}
              icon={<Plus className="h-3.5 w-3.5" aria-hidden />}
            >
              {t('notes.add')}
            </Button>
          ) : undefined
        }
      />
      <CardBody>
        {showForm && canAct ? (
          <div className="mb-5 rounded-lg border border-ink-200 bg-ink-50/60 p-4">
            {create.error ? (
              <div className="mb-3">
                <InlineMessage tone="warning">{create.error.message}</InlineMessage>
              </div>
            ) : null}
            <div className="grid gap-3 sm:grid-cols-3">
              <SelectInput
                label={t('notes.type')}
                value={noteType}
                options={NOTE_TYPES.map((item) => ({ label: item, value: item }))}
                onChange={(event) => setNoteType(event.target.value as NoteType)}
              />
            </div>
            <div className="mt-3">
              <TextArea
                label={t('notes.content')}
                required
                error={validation}
                value={content}
                rows={3}
                maxLength={4000}
                onChange={(event) => setContent(event.target.value)}
              />
            </div>
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
              <Checkbox label={t('notes.pin')} checked={pinned} onChange={setPinned} />
              <div className="flex gap-2">
                <Button variant="secondary" size="sm" onClick={() => setShowForm(false)}>
                  {t('common.cancel')}
                </Button>
                <Button size="sm" onClick={submit} loading={create.pending}>
                  {t('common.save')}
                </Button>
              </div>
            </div>
          </div>
        ) : null}

        {message ? (
          <div className="mb-4">
            <InlineMessage tone="success">{message}</InlineMessage>
          </div>
        ) : null}

        <div className="mb-4 max-w-xs">
          <SelectInput
            label={t('notes.type')}
            value={filter}
            placeholder={t('common.all')}
            options={NOTE_TYPES.map((item) => ({ label: item, value: item }))}
            onChange={(event) => setFilter(event.target.value as NoteType | '')}
          />
        </div>

        {list.loading ? (
          <SkeletonRows rows={3} />
        ) : list.error ? (
          <ErrorState error={list.error} onRetry={list.reload} retryLabel={t('common.retry')} />
        ) : (list.data?.length ?? 0) === 0 ? (
          <EmptyState title={t('notes.none')} />
        ) : (
          <ul className="space-y-3">
            {list.data?.map((note) => (
              <li key={note.id} className="rounded-lg border border-ink-200 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Badge tone={TYPE_TONE[note.note_type]}>{tEnum('noteType', note.note_type)}</Badge>
                    {note.is_pinned ? (
                      <Pin className="h-3.5 w-3.5 text-saffron-700" aria-label={t('a11y.pinned')} />
                    ) : null}
                  </div>
                  <span className="text-xs text-ink-500">{formatDateTime(note.created_at)}</span>
                </div>
                <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-ink-800">
                  {note.content}
                </p>
                <div className="mt-2.5 flex items-center justify-between gap-2">
                  <p className="text-xs text-ink-500">
                    {t('notes.by')} {note.author_name} ({note.author_role})
                  </p>
                  {canAct && (note.author_id === user?.id || isAdmin) ? (
                    <Button
                      variant="ghost"
                      size="sm"
                      loading={remove.pending}
                      onClick={() => handleDelete(note.id)}
                      icon={<Trash2 className="h-3.5 w-3.5" aria-hidden />}
                    >
                      {t('notes.delete')}
                    </Button>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardBody>
    </Card>
  )
}
