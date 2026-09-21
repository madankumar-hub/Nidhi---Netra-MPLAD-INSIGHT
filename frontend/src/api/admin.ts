import { buildQuery, downloadFile, request } from './client'
import type {
  AccessPolicy,
  AccessRequest,
  AccessRequestStatus,
  ActivityEntry,
  AdminAnalytics,
  CitizenReport,
  CitizenReportStatus,
  FilterOptions,
  FundUpdate,
  Page,
  ProgressUpdate,
  ProjectAdminDetail,
  ProjectAdminSummary,
  ProjectQuery,
  ProjectStatus,
  User,
  UserRole,
} from '@/types'

export function getAnalytics(signal?: AbortSignal) {
  return request<AdminAnalytics>('/admin/analytics', { signal })
}

export function listAdminProjects(query: ProjectQuery, signal?: AbortSignal) {
  const qs = buildQuery({
    search: query.search,
    mp: query.mp,
    district: query.district,
    state: query.state,
    category: query.category,
    agency: query.agency,
    year: query.year,
    status: query.status,
    review_status: query.review_status,
    risk_level: query.risk_level,
    overdue_only: query.overdue_only,
    sort_by: query.sort_by,
    sort_dir: query.sort_dir,
    page: query.page,
    page_size: query.page_size,
  })
  return request<Page<ProjectAdminSummary>>(`/admin/projects${qs}`, { signal })
}

export function getAdminFilters(signal?: AbortSignal) {
  return request<FilterOptions>('/admin/projects/filters', { signal })
}

export function getAdminProject(id: number, signal?: AbortSignal) {
  return request<ProjectAdminDetail>(`/admin/projects/${id}`, { signal })
}

export function updateProject(id: number, payload: Record<string, unknown>) {
  return request<ProjectAdminDetail>(`/admin/projects/${id}`, { method: 'PATCH', body: payload })
}

export function changeProjectStatus(id: number, status: ProjectStatus, reason: string) {
  return request<ProjectAdminDetail>(`/admin/projects/${id}/status`, {
    method: 'POST',
    body: { status, reason },
  })
}

export function listDelayedProjects(signal?: AbortSignal) {
  return request<ProjectAdminSummary[]>('/admin/delayed-projects', { signal })
}

export function listPendingReview(signal?: AbortSignal) {
  return request<ProjectAdminSummary[]>('/admin/pending-review', { signal })
}

export function addFundUpdate(
  projectId: number,
  payload: {
    updated_on: string
    installment_no?: number
    released_amount: number
    expenditure_amount: number
    voucher_reference?: string
    remarks?: string
  },
) {
  return request<FundUpdate>(`/admin/projects/${projectId}/fund-updates`, {
    method: 'POST',
    body: payload,
  })
}

export function addProgressUpdate(
  projectId: number,
  payload: {
    updated_on: string
    progress_percent: number
    planned_progress_percent?: number
    milestone?: string
    remarks?: string
  },
) {
  return request<ProgressUpdate>(`/admin/projects/${projectId}/progress`, {
    method: 'POST',
    body: payload,
  })
}

export function listRecentActivity(limit = 50, signal?: AbortSignal) {
  return request<ActivityEntry[]>(`/admin/activity${buildQuery({ limit })}`, { signal })
}

export function listProjectActivity(projectId: number, signal?: AbortSignal) {
  return request<ActivityEntry[]>(`/admin/projects/${projectId}/activity`, { signal })
}

export function listCitizenReports(
  params: { project_id?: number; status?: CitizenReportStatus | '' } = {},
  signal?: AbortSignal,
) {
  return request<CitizenReport[]>(`/admin/citizen-reports${buildQuery(params)}`, { signal })
}

export function listProjectCitizenReports(projectId: number, signal?: AbortSignal) {
  return request<CitizenReport[]>(`/admin/projects/${projectId}/citizen-reports`, { signal })
}

export function triageCitizenReport(
  reportId: number,
  payload: { status: CitizenReportStatus; official_response?: string },
) {
  return request<CitizenReport>(`/admin/citizen-reports/${reportId}`, {
    method: 'PATCH',
    body: payload,
  })
}

export interface ExportParams {
  search?: string
  district?: string
  category?: string
  status?: string
  review_status?: string
  flagged_only?: boolean
}

/**
 * FR12 - export the current selection.
 *
 * CSV is for working with the numbers; PDF is the printable report an officer
 * forwards or files. The server decides the filename, but the browser needs
 * one up front for the download attribute.
 */
export function exportProjects(params: ExportParams, format: 'csv' | 'pdf' = 'csv') {
  const filename =
    format === 'pdf'
      ? params.flagged_only
        ? 'mplad-flagged-works.pdf'
        : 'mplad-works.pdf'
      : 'mplad-projects.csv'
  return downloadFile(`/admin/projects/export${buildQuery({ ...params, format })}`, filename)
}

// --- Access control (Administrator only) ----------------------------------

export function listAccessRequests(
  params: { status?: AccessRequestStatus | '' } = {},
  signal?: AbortSignal,
) {
  return request<AccessRequest[]>(`/admin/access-requests${buildQuery(params)}`, { signal })
}

export function getAccessPolicy(signal?: AbortSignal) {
  return request<AccessPolicy>('/admin/access-policy', { signal })
}

export function decideAccessRequest(
  requestId: number,
  payload: { approve: boolean; granted_role?: UserRole; note?: string },
) {
  return request<AccessRequest>(`/admin/access-requests/${requestId}/decide`, {
    method: 'POST',
    body: payload,
  })
}

export function listUsers(params: { role?: UserRole | '' } = {}, signal?: AbortSignal) {
  return request<User[]>(`/admin/users${buildQuery(params)}`, { signal })
}

export function revokeOfficialRole(userId: number, note?: string) {
  return request<User>(`/admin/users/${userId}/revoke`, { method: 'POST', body: { note } })
}
