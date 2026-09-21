import type {
  CitizenReportCategory,
  CitizenReportStatus,
  MitigationStatus,
  NoteType,
  ProjectStatus,
  ReviewStatus,
  RiskLevel,
  RiskStatus,
} from '@/types'

export const PROJECT_STATUSES: ProjectStatus[] = [
  'Not Started',
  'In Progress',
  'Delayed',
  'On Hold',
  'Completed',
  'Cancelled',
]

export const REVIEW_STATUSES: ReviewStatus[] = [
  'Pending Review',
  'Reviewed',
  'On Track',
  'Delayed',
  'Escalated',
  'Resolved',
]

export const RISK_LEVELS: RiskLevel[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

/** Lifecycle of a risk record, in the order a reviewer moves through it. */
export const RISK_STATUSES: RiskStatus[] = [
  'Open',
  'Under Review',
  'Mitigated',
  'Accepted',
  'Closed',
]

export const NOTE_TYPES: NoteType[] = [
  'Review Note',
  'Risk Note',
  'Delay Note',
  'Action Note',
  'General Note',
]

export const MITIGATION_STATUSES: MitigationStatus[] = ['Open', 'In Progress', 'Resolved']

export const CITIZEN_REPORT_CATEGORIES: CitizenReportCategory[] = [
  'Work Not Started',
  'Poor Quality of Work',
  'Incomplete Work',
  'Wrong Location',
  'Information Incorrect',
  'Other',
]

export const CITIZEN_REPORT_STATUSES: CitizenReportStatus[] = [
  'Submitted',
  'Under Review',
  'Action Taken',
  'Closed',
]

/**
 * Chart palette.
 *
 * These are the validated categorical slots from the data-visualisation
 * reference palette, assigned in fixed order and never cycled. They passed the
 * palette validator on the light chart surface: adjacent-pair CVD separation,
 * chroma floor, lightness band and contrast. The navy/saffron identity in the
 * page chrome is deliberately kept out of the series colours so that a chart
 * series is never mistaken for a UI state.
 */
export const CHART_COLORS = [
  '#2a78d6', // 1 blue
  '#eb6834', // 2 orange
  '#1baf7a', // 3 aqua
  '#eda100', // 4 yellow
  '#e87ba4', // 5 magenta
  '#008300', // 6 green
  '#4a3aa7', // 7 violet
  '#e34948', // 8 red
]

/** Single-hue ramp for magnitude-only charts (one series, light to dark). */
export const SEQUENTIAL_BLUE = [
  '#86b6ef',
  '#6da7ec',
  '#5598e7',
  '#3987e5',
  '#2a78d6',
  '#256abf',
  '#1c5cab',
  '#184f95',
]

export const SERIES = {
  allocated: CHART_COLORS[0],
  spent: CHART_COLORS[1],
  actual: CHART_COLORS[0],
  planned: CHART_COLORS[2],
  works: CHART_COLORS[6],
}

/** Reserved status colours - never reused as a series colour. */
export const STATUS_PALETTE = {
  good: '#0ca30c',
  warning: '#fab219',
  serious: '#ec835a',
  critical: '#d03b3b',
  neutral: '#898781',
}

export const RISK_COLORS: Record<RiskLevel, string> = {
  LOW: STATUS_PALETTE.good,
  MEDIUM: STATUS_PALETTE.warning,
  HIGH: STATUS_PALETTE.serious,
  CRITICAL: STATUS_PALETTE.critical,
}

export const STATUS_COLORS: Record<ProjectStatus, string> = {
  'Not Started': STATUS_PALETTE.neutral,
  'In Progress': CHART_COLORS[0],
  Delayed: STATUS_PALETTE.serious,
  'On Hold': STATUS_PALETTE.warning,
  Completed: STATUS_PALETTE.good,
  Cancelled: '#c3c2b7',
}

export const REVIEW_STATUS_COLORS: Record<string, string> = {
  'Pending Review': STATUS_PALETTE.neutral,
  Reviewed: CHART_COLORS[0],
  'On Track': STATUS_PALETTE.good,
  Delayed: STATUS_PALETTE.serious,
  Escalated: STATUS_PALETTE.critical,
  Resolved: '#008300',
}

/** Chart chrome. */
export const CHART_INK = {
  grid: '#e1e0d9',
  axis: '#c3c2b7',
  muted: '#898781',
  secondary: '#52514e',
}

export const PAGE_SIZE_OPTIONS = [12, 24, 48]
