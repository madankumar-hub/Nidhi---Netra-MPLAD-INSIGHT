import { buildQuery, request } from './client'
import type {
  CitizenReport,
  CitizenReportCategory,
  FilterOptions,
  Page,
  ProjectPublicDetail,
  ProjectPublicSummary,
  ProjectQuery,
  PublicAnalytics,
} from '@/types'

/** Citizen portal: search and filter works (FR4). Runs entirely server-side. */
export function listPublicProjects(query: ProjectQuery, signal?: AbortSignal) {
  const qs = buildQuery({
    search: query.search,
    mp: query.mp,
    district: query.district,
    state: query.state,
    category: query.category,
    agency: query.agency,
    year: query.year,
    status: query.status,
    sort_by: query.sort_by,
    sort_dir: query.sort_dir,
    page: query.page,
    page_size: query.page_size,
  })
  return request<Page<ProjectPublicSummary>>(`/projects${qs}`, { signal, auth: false })
}

export function getPublicProject(id: number, signal?: AbortSignal) {
  return request<ProjectPublicDetail>(`/projects/${id}`, { signal, auth: false })
}

export function getPublicFilters(signal?: AbortSignal) {
  return request<FilterOptions>('/projects/filters', { signal, auth: false })
}

export function getPublicStatistics(signal?: AbortSignal) {
  return request<PublicAnalytics>('/projects/statistics', { signal, auth: false })
}

export function fileCitizenReport(
  projectId: number,
  payload: { category: CitizenReportCategory; description: string },
) {
  return request<CitizenReport>(`/projects/${projectId}/reports`, {
    method: 'POST',
    body: payload,
  })
}

export function listMyReports(projectId: number, signal?: AbortSignal) {
  return request<CitizenReport[]>(`/projects/${projectId}/my-reports`, { signal })
}
