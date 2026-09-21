/**
 * Type definitions mirroring the FastAPI response schemas.
 * Keep these in step with `backend/app/schemas/*`.
 */

// --- Enumerations (string values match the backend exactly) ---------------
export type UserRole = 'citizen' | 'officer' | 'auditor' | 'admin'

export type AccessRequestStatus = 'Pending' | 'Approved' | 'Rejected' | 'Withdrawn'

export type ProjectStatus =
  | 'Not Started'
  | 'In Progress'
  | 'Delayed'
  | 'On Hold'
  | 'Completed'
  | 'Cancelled'

export type ReviewStatus =
  | 'Pending Review'
  | 'Reviewed'
  | 'On Track'
  | 'Delayed'
  | 'Escalated'
  | 'Resolved'

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export type RiskCategory =
  | 'Schedule Risk'
  | 'Financial Risk'
  | 'Expenditure Risk'
  | 'Progress Risk'
  | 'Implementation Risk'
  | 'Completion Risk'
  | 'Duplication Risk'

export type AnalysisSource =
  | 'rule_based'
  | 'statistical'
  | 'machine_learning'
  | 'external_ai'

export type Likelihood = 'Rare' | 'Unlikely' | 'Possible' | 'Likely' | 'Almost Certain'

export type Impact = 'Negligible' | 'Minor' | 'Moderate' | 'Major' | 'Severe'

export type RiskStatus = 'Open' | 'Under Review' | 'Mitigated' | 'Accepted' | 'Closed'

export type MitigationStatus = 'Open' | 'In Progress' | 'Resolved'

export type NoteType =
  | 'Review Note'
  | 'Risk Note'
  | 'Delay Note'
  | 'General Note'
  | 'Action Note'

export type PublicRiskIndicator = 'Normal' | 'Under Review'

export type CitizenReportCategory =
  | 'Work Not Started'
  | 'Poor Quality of Work'
  | 'Incomplete Work'
  | 'Wrong Location'
  | 'Information Incorrect'
  | 'Other'

export type CitizenReportStatus = 'Submitted' | 'Under Review' | 'Action Taken' | 'Closed'

export type ActivityType =
  | 'project_created'
  | 'project_updated'
  | 'status_changed'
  | 'review_status_changed'
  | 'project_reviewed'
  | 'risk_assessed'
  | 'risk_level_changed'
  | 'risk_status_changed'
  | 'note_added'
  | 'mitigation_added'
  | 'mitigation_updated'
  | 'mitigation_resolved'
  | 'progress_updated'
  | 'fund_updated'
  | 'report_exported'
  | 'citizen_report_filed'
  | 'citizen_report_triaged'

// --- Common ---------------------------------------------------------------
export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface MessageResponse {
  message: string
  detail?: string | null
}

export interface OptionCount {
  label: string
  value: string
  count: number
}

export interface FilterOptions {
  mps: OptionCount[]
  districts: OptionCount[]
  states: OptionCount[]
  categories: OptionCount[]
  agencies: OptionCount[]
  years: OptionCount[]
  statuses: OptionCount[]
}

// --- Auth -----------------------------------------------------------------
export interface User {
  id: number
  email: string
  full_name: string
  role: UserRole
  designation?: string | null
  department?: string | null
  district?: string | null
  is_active: boolean
  is_verified: boolean
  last_login_at?: string | null
  created_at: string
}

export interface AccessRequest {
  id: number
  user_id: number
  email: string
  full_name: string
  requested_role: UserRole
  designation?: string | null
  department?: string | null
  district?: string | null
  employee_id?: string | null
  justification: string
  status: AccessRequestStatus
  email_allowlisted: boolean
  decided_at?: string | null
  decided_by_name?: string | null
  decision_note?: string | null
  granted_role?: UserRole | null
  created_at: string
}

export interface AccessPolicy {
  enforced: boolean
  domains: string[]
  explicit_addresses: number
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in_minutes: number
  user: User
}

export interface OtpRequested {
  message: string
  email: string
  expires_in_minutes: number
  dev_otp?: string | null
}

// --- Tracking -------------------------------------------------------------
export interface FundUpdate {
  id: number
  updated_on: string
  installment_no?: number | null
  released_amount: number
  expenditure_amount: number
  cumulative_spent: number
  voucher_reference?: string | null
  remarks?: string | null
}

export interface ProgressUpdate {
  id: number
  updated_on: string
  progress_percent: number
  planned_progress_percent?: number | null
  milestone?: string | null
  remarks?: string | null
}

export interface TimelinePoint {
  period: string
  allocated: number
  spent: number
  cumulative_spent: number
  utilization_percent: number
}

export interface ProgressPoint {
  period: string
  actual: number
  planned?: number | null
}

// --- Projects: citizen view ----------------------------------------------
export interface ProjectPublicSummary {
  id: number
  project_code: string
  title: string
  mp_name: string
  constituency?: string | null
  state: string
  district: string
  category: string
  executing_agency: string
  sanction_year: number
  start_date?: string | null
  planned_end_date?: string | null
  allocated_amount: number
  spent_amount: number
  remaining_amount: number
  utilization_percent: number
  progress_percent: number
  status: ProjectStatus
  public_indicator: PublicRiskIndicator
  latitude?: number | null
  longitude?: number | null
}

export interface ProjectPublicDetail extends ProjectPublicSummary {
  description: string
  house: string
  block?: string | null
  location?: string | null
  latitude?: number | null
  longitude?: number | null
  contractor?: string | null
  sanction_date?: string | null
  actual_end_date?: string | null
  estimated_cost?: number | null
  beneficiaries?: number | null
  photo_url?: string | null
  document_url?: string | null
  fund_updates: FundUpdate[]
  progress_updates: ProgressUpdate[]
  spending_timeline: TimelinePoint[]
  progress_timeline: ProgressPoint[]
  days_remaining?: number | null
  is_overdue: boolean
}

// --- Projects: admin view -------------------------------------------------
export interface ProjectAdminSummary extends ProjectPublicSummary {
  review_status: ReviewStatus
  planned_progress_percent?: number | null
  risk_level?: RiskLevel | null
  risk_score?: number | null
  open_risk_factors: number
  open_mitigations: number
  is_overdue: boolean
  days_remaining?: number | null
  schedule_variance?: number | null
  last_reviewed_at?: string | null
}

export interface ProjectAdminDetail extends ProjectAdminSummary {
  description: string
  house: string
  block?: string | null
  location?: string | null
  latitude?: number | null
  longitude?: number | null
  contractor?: string | null
  sanction_date?: string | null
  actual_end_date?: string | null
  estimated_cost?: number | null
  beneficiaries?: number | null
  photo_url?: string | null
  document_url?: string | null
  remarks?: string | null
  created_at: string
  updated_at: string
  fund_updates: FundUpdate[]
  progress_updates: ProgressUpdate[]
  spending_timeline: TimelinePoint[]
  progress_timeline: ProgressPoint[]
  expected_progress_percent?: number | null
  expected_utilization_percent?: number | null
  citizen_report_count: number
}

// --- Risk -----------------------------------------------------------------
export interface RiskFactor {
  id: number
  code: string
  title: string
  category: RiskCategory
  severity: RiskLevel
  source: AnalysisSource
  contribution: number
  weight: number
  detected_indicator: string
  evidence: string
  explanation: string
  recommended_action: string
  metric_name?: string | null
  metric_value?: number | null
  threshold_value?: number | null
  reference_project_code?: string | null
}

export interface MitigationAction {
  id: number
  assessment_id: number
  project_id: number
  risk_factor_code?: string | null
  action: string
  responsible_party: string
  status: MitigationStatus
  priority: number
  due_date?: string | null
  notes?: string | null
  created_by_name: string
  created_at: string
  resolved_at?: string | null
  resolved_by_name?: string | null
  is_system_recommended: boolean
}

export interface RiskAssessment {
  id: number
  project_id: number
  risk_score: number
  risk_level: RiskLevel
  likelihood: Likelihood
  impact: Impact
  primary_category?: RiskCategory | null
  status: RiskStatus
  summary: string
  explanation: string
  recommended_actions: string
  analysis_sources: AnalysisSource[]
  engine_version: string
  ai_model_used?: string | null
  ai_narrative?: string | null
  data_completeness_percent: number
  assessed_at: string
  is_current: boolean
  factors: RiskFactor[]
  mitigations: MitigationAction[]
}

export interface MachineLearningInfo {
  available: boolean
  model: string
  algorithm: string
  trees: number
  subsample_size: number
  features: number
  feature_names: string[]
  trained_on_records: number
  flag_threshold: number
  flag_percentile: number
  contamination: number
  minimum_cohort: number
  supervised: boolean
  notes: string
}

export interface RiskEngineInfo {
  engine_version: string
  rule_based_enabled: boolean
  statistical_enabled: boolean
  machine_learning_enabled: boolean
  machine_learning?: MachineLearningInfo | null
  duplicate_detection_backend: string
  external_ai_enabled: boolean
  external_ai_provider?: string | null
  external_ai_model?: string | null
  notes: string
}

export interface FlaggedProject {
  project_id: number
  project_code: string
  title: string
  district: string
  category: string
  mp_name: string
  allocated_amount: number
  spent_amount: number
  progress_percent: number
  risk_score: number
  risk_level: RiskLevel
  primary_category?: RiskCategory | null
  top_factors: string[]
  review_status: string
}

// --- Workflow -------------------------------------------------------------
export interface Review {
  id: number
  project_id: number
  reviewer_id?: number | null
  reviewer_name: string
  reviewer_role: string
  review_date: string
  previous_status?: ReviewStatus | null
  status: ReviewStatus
  findings: string
  notes?: string | null
  action_required?: string | null
  escalated_to?: string | null
  follow_up_required: boolean
  created_at: string
}

export interface Note {
  id: number
  project_id: number
  author_id?: number | null
  author_name: string
  author_role: string
  note_type: NoteType
  content: string
  is_pinned: boolean
  created_at: string
  updated_at: string
}

export interface ActivityEntry {
  id: number
  project_id?: number | null
  actor_name: string
  actor_role: string
  activity_type: ActivityType
  summary: string
  detail?: string | null
  from_value?: string | null
  to_value?: string | null
  created_at: string
}

export interface CitizenReport {
  id: number
  project_id: number
  reporter_name: string
  category: CitizenReportCategory
  description: string
  status: CitizenReportStatus
  official_response?: string | null
  created_at: string
}

// --- Analytics ------------------------------------------------------------
export interface KeyValueCount {
  label: string
  value: number
}

export interface KeyValueAmount {
  label: string
  allocated: number
  spent: number
  utilization_percent: number
  count: number
}

export interface TrendPoint {
  period: string
  allocated: number
  spent: number
  projects: number
  avg_progress: number
}

export interface DashboardSummary {
  total_projects: number
  active_projects: number
  completed_projects: number
  delayed_projects: number
  not_started_projects: number
  pending_review_projects: number
  escalated_projects: number
  projects_with_open_risks: number
  high_risk_projects: number
  critical_risk_projects: number
  open_mitigations: number
  overdue_projects: number
  citizen_reports_open: number
  total_allocated: number
  total_spent: number
  total_remaining: number
  utilization_percent: number
  average_progress: number
  average_risk_score: number
}

export interface PublicSummary {
  total_projects: number
  completed_projects: number
  ongoing_projects: number
  districts_covered: number
  categories_covered: number
  total_allocated: number
  total_spent: number
  utilization_percent: number
  average_progress: number
}

export interface AdminAnalytics {
  summary: DashboardSummary
  by_status: KeyValueCount[]
  by_review_status: KeyValueCount[]
  by_risk_level: KeyValueCount[]
  by_category: KeyValueAmount[]
  by_district: KeyValueAmount[]
  by_agency: KeyValueAmount[]
  by_mp: KeyValueAmount[]
  progress_distribution: KeyValueCount[]
  utilization_distribution: KeyValueCount[]
  yearly_trend: TrendPoint[]
  spending_trend: TrendPoint[]
  risk_category_distribution: KeyValueCount[]
  top_risk_factors: KeyValueCount[]
  generated_at: string
}

export interface PublicAnalytics {
  summary: PublicSummary
  by_status: KeyValueCount[]
  by_category: KeyValueAmount[]
  by_district: KeyValueAmount[]
  yearly_trend: TrendPoint[]
  generated_at: string
}

// --- Write payloads -------------------------------------------------------
export interface ProjectCreatePayload {
  project_code?: string
  title: string
  description: string
  mp_name: string
  constituency?: string
  house: string
  state: string
  district: string
  block?: string
  location?: string
  category: string
  executing_agency: string
  contractor?: string
  sanction_year: number
  sanction_date?: string
  start_date?: string
  planned_end_date?: string
  allocated_amount: number
  spent_amount?: number
  estimated_cost?: number
  progress_percent?: number
  status: ProjectStatus
  beneficiaries?: number
  remarks?: string
}

// --- Query parameter shapes ----------------------------------------------
export interface ProjectQuery {
  search?: string
  mp?: string
  district?: string
  state?: string
  category?: string
  agency?: string
  year?: number | string
  status?: ProjectStatus | ''
  review_status?: ReviewStatus | ''
  risk_level?: RiskLevel | ''
  overdue_only?: boolean
  sort_by?: string
  sort_dir?: 'asc' | 'desc'
  page?: number
  page_size?: number
}
