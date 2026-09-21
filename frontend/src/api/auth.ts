import { request } from './client'
import type {
  AccessPolicy,
  AccessRequest,
  MessageResponse,
  OtpRequested,
  TokenResponse,
  User,
  UserRole,
} from '@/types'

export function login(email: string, password: string) {
  return request<TokenResponse>('/auth/login', {
    method: 'POST',
    body: { email, password },
    auth: false,
  })
}

export function requestSignupOtp(email: string, fullName: string) {
  return request<OtpRequested>('/auth/signup/request-otp', {
    method: 'POST',
    body: { email, full_name: fullName },
    auth: false,
  })
}

export function completeSignup(payload: {
  email: string
  full_name: string
  otp: string
  password: string
}) {
  return request<TokenResponse>('/auth/signup/verify', {
    method: 'POST',
    body: payload,
    auth: false,
  })
}

export function me() {
  return request<User>('/auth/me')
}

export function logout() {
  return request<MessageResponse>('/auth/logout', { method: 'POST' })
}

// --- Official access: requested by the user, granted by an administrator ---

export function getAccessPolicy(signal?: AbortSignal) {
  return request<AccessPolicy>('/auth/access-policy', { signal, auth: false })
}

export function getRequestableRoles(signal?: AbortSignal) {
  return request<UserRole[]>('/auth/requestable-roles', { signal, auth: false })
}

export function requestOfficialAccess(payload: {
  requested_role: UserRole
  designation?: string
  department?: string
  district?: string
  employee_id?: string
  justification: string
}) {
  return request<AccessRequest>('/auth/request-official-access', {
    method: 'POST',
    body: payload,
  })
}

export function listMyAccessRequests(signal?: AbortSignal) {
  return request<AccessRequest[]>('/auth/my-access-requests', { signal })
}
