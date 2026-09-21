import { buildQuery, request } from './client'
import type { MessageResponse, Note, NoteType, Review, ReviewStatus } from '@/types'

export function listReviews(projectId: number, signal?: AbortSignal) {
  return request<Review[]>(`/admin/projects/${projectId}/reviews`, { signal })
}

export function createReview(
  projectId: number,
  payload: {
    status: ReviewStatus
    findings: string
    notes?: string
    action_required?: string
    escalated_to?: string
    follow_up_required?: boolean
  },
) {
  return request<Review>(`/admin/projects/${projectId}/reviews`, { method: 'POST', body: payload })
}

export function listRecentReviews(limit = 50, signal?: AbortSignal) {
  return request<Review[]>(`/admin/review-queue${buildQuery({ limit })}`, { signal })
}

export function listNotes(projectId: number, noteType?: NoteType | '', signal?: AbortSignal) {
  return request<Note[]>(
    `/admin/projects/${projectId}/notes${buildQuery({ note_type: noteType })}`,
    { signal },
  )
}

export function addNote(
  projectId: number,
  payload: { content: string; note_type: NoteType; is_pinned?: boolean },
) {
  return request<Note>(`/admin/projects/${projectId}/notes`, { method: 'POST', body: payload })
}

export function deleteNote(noteId: number) {
  return request<MessageResponse>(`/admin/notes/${noteId}`, { method: 'DELETE' })
}
