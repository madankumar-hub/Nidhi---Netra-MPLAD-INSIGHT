import { buildQuery, request } from './client'
import type {
  FlaggedProject,
  MessageResponse,
  MitigationAction,
  MitigationStatus,
  RiskAssessment,
  RiskEngineInfo,
  RiskStatus,
} from '@/types'

export function getRiskEngineInfo(signal?: AbortSignal) {
  return request<RiskEngineInfo>('/admin/risk-engine', { signal })
}

export function getRiskAssessment(projectId: number, signal?: AbortSignal) {
  return request<RiskAssessment>(`/admin/projects/${projectId}/risk`, { signal })
}

export function recomputeRisk(projectId: number, useExternalAi = false) {
  return request<RiskAssessment>(`/admin/projects/${projectId}/risk/recompute`, {
    method: 'POST',
    body: { use_external_ai: useExternalAi },
  })
}

export function updateRiskStatus(projectId: number, status: RiskStatus, reason?: string) {
  return request<RiskAssessment>(`/admin/projects/${projectId}/risk/status`, {
    method: 'PATCH',
    body: { status, reason },
  })
}

export function listFlaggedProjects(limit = 25, minScore = 25, signal?: AbortSignal) {
  return request<FlaggedProject[]>(
    `/admin/projects/flagged${buildQuery({ limit, min_score: minScore })}`,
    { signal },
  )
}

export function listMitigation(projectId: number, signal?: AbortSignal) {
  return request<MitigationAction[]>(`/admin/projects/${projectId}/mitigation`, { signal })
}

export function addMitigation(
  projectId: number,
  payload: {
    action: string
    responsible_party: string
    risk_factor_code?: string
    priority?: number
    due_date?: string
    notes?: string
    status?: MitigationStatus
  },
) {
  return request<MitigationAction>(`/admin/projects/${projectId}/mitigation`, {
    method: 'POST',
    body: payload,
  })
}

export function updateMitigation(
  mitigationId: number,
  payload: {
    action?: string
    responsible_party?: string
    status?: MitigationStatus
    priority?: number
    due_date?: string
    notes?: string
  },
) {
  return request<MitigationAction>(`/admin/mitigation/${mitigationId}`, {
    method: 'PATCH',
    body: payload,
  })
}

export function resolveMitigation(mitigationId: number) {
  return request<MitigationAction>(`/admin/mitigation/${mitigationId}/resolve`, { method: 'POST' })
}

export function recomputeAllRisk() {
  return request<MessageResponse>('/admin/risk/recompute-all', { method: 'POST' })
}
