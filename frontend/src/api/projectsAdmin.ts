import { request } from './client'
import type { MessageResponse, ProjectAdminDetail, ProjectCreatePayload } from '@/types'

export function createProject(payload: ProjectCreatePayload) {
  return request<ProjectAdminDetail>('/admin/projects', { method: 'POST', body: payload })
}

export function deleteProject(projectId: number) {
  return request<MessageResponse>(`/admin/projects/${projectId}`, { method: 'DELETE' })
}

export function bulkImport(payload: ProjectCreatePayload[]) {
  return request<{ created: number; skipped: number; errors: string[] }>(
    '/admin/projects/bulk-import',
    { method: 'POST', body: payload },
  )
}
