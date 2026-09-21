/**
 * Translations for values that arrive from the API as raw enum strings.
 *
 * The backend stores and transmits English domain vocabulary ("In Progress",
 * "Schedule Risk", "CRITICAL"). That is deliberate - it keeps the database and
 * the API stable and greppable. But it means the UI must never render those
 * values directly, or Hindi mode leaks English.
 *
 * Every map here is keyed on the exact wire value from `app/core/enums.py`.
 * A value with no entry falls through to itself, so a new backend enum degrades
 * to English rather than showing a blank or a key.
 */
import type { Language } from './index'
import {
  AGENCY_HI,
  BUCKET_HI,
  CATEGORY_HI,
  CONSTITUENCY_HI,
  DISTRICT_HI,
  RISK_FACTOR_TITLE_HI,
  STATE_HI,
} from './vocabulary'

type EnumMap = Record<string, string>

/** Execution status of a work (ProjectStatus). */
const PROJECT_STATUS_HI: EnumMap = {
  'Not Started': 'शुरू नहीं हुआ',
  'In Progress': 'प्रगति पर',
  Delayed: 'विलंबित',
  'On Hold': 'रोका गया',
  Completed: 'पूर्ण',
  Cancelled: 'रद्द',
}

/** Administrative review workflow state (ReviewStatus). */
const REVIEW_STATUS_HI: EnumMap = {
  'Pending Review': 'समीक्षा लंबित',
  Reviewed: 'समीक्षित',
  'On Track': 'सही दिशा में',
  Delayed: 'विलंबित',
  Escalated: 'उच्च स्तर पर भेजा गया',
  Resolved: 'समाधान हो गया',
}

/** Internal risk level (RiskLevel). */
const RISK_LEVEL_HI: EnumMap = {
  LOW: 'कम',
  MEDIUM: 'मध्यम',
  HIGH: 'उच्च',
  CRITICAL: 'अति गंभीर',
}

/** Risk category (RiskCategory). */
const RISK_CATEGORY_HI: EnumMap = {
  'Schedule Risk': 'समय-सारणी जोखिम',
  'Financial Risk': 'वित्तीय जोखिम',
  'Expenditure Risk': 'व्यय जोखिम',
  'Progress Risk': 'प्रगति जोखिम',
  'Implementation Risk': 'क्रियान्वयन जोखिम',
  'Completion Risk': 'पूर्णता जोखिम',
  'Duplication Risk': 'दोहराव जोखिम',
}

/** Which analysis layer produced a finding (AnalysisSource). */
const ANALYSIS_SOURCE_EN: EnumMap = {
  rule_based: 'Rule-based',
  statistical: 'Statistical',
  machine_learning: 'Machine learning',
  external_ai: 'External AI',
}

const ANALYSIS_SOURCE_HI: EnumMap = {
  rule_based: 'नियम-आधारित',
  statistical: 'सांख्यिकीय',
  machine_learning: 'मशीन लर्निंग',
  external_ai: 'बाहरी एआई',
}

/** Likelihood of a risk materialising (Likelihood). */
const LIKELIHOOD_HI: EnumMap = {
  Rare: 'दुर्लभ',
  Unlikely: 'असंभावित',
  Possible: 'संभव',
  Likely: 'संभावित',
  'Almost Certain': 'लगभग निश्चित',
}

/** Severity if a risk materialises (Impact). */
const IMPACT_HI: EnumMap = {
  Negligible: 'नगण्य',
  Minor: 'मामूली',
  Moderate: 'मध्यम',
  Major: 'बड़ा',
  Severe: 'गंभीर',
}

/** Lifecycle of a risk record (RiskStatus). */
const RISK_STATUS_HI: EnumMap = {
  Open: 'खुला',
  'Under Review': 'समीक्षाधीन',
  Mitigated: 'न्यूनीकृत',
  Accepted: 'स्वीकृत',
  Closed: 'बंद',
}

/** Mitigation action state (MitigationStatus). */
const MITIGATION_STATUS_HI: EnumMap = {
  Open: 'खुला',
  'In Progress': 'प्रगति पर',
  Resolved: 'समाधान हो गया',
}

/** Internal note classification (NoteType). */
const NOTE_TYPE_HI: EnumMap = {
  'Review Note': 'समीक्षा टिप्पणी',
  'Risk Note': 'जोखिम टिप्पणी',
  'Delay Note': 'विलंब टिप्पणी',
  'General Note': 'सामान्य टिप्पणी',
  'Action Note': 'कार्रवाई टिप्पणी',
}

/** Public-safe indicator shown to citizens (PublicRiskIndicator). */
const PUBLIC_INDICATOR_HI: EnumMap = {
  Normal: 'सामान्य',
  'Under Review': 'समीक्षाधीन',
}

/** Official-access request lifecycle (AccessRequestStatus). */
const ACCESS_REQUEST_STATUS_HI: EnumMap = {
  Pending: 'लंबित',
  Approved: 'स्वीकृत',
  Rejected: 'अस्वीकृत',
  Withdrawn: 'वापस लिया गया',
}

/** What a citizen is reporting (CitizenReportCategory). */
const REPORT_CATEGORY_HI: EnumMap = {
  'Work Not Started': 'कार्य शुरू नहीं हुआ',
  'Poor Quality of Work': 'कार्य की गुणवत्ता खराब',
  'Incomplete Work': 'अधूरा कार्य',
  'Wrong Location': 'गलत स्थान',
  'Information Incorrect': 'जानकारी गलत है',
  Other: 'अन्य',
}

/** Triage state of a citizen report (CitizenReportStatus). */
const REPORT_STATUS_HI: EnumMap = {
  Submitted: 'प्रस्तुत',
  'Under Review': 'समीक्षाधीन',
  'Action Taken': 'कार्रवाई की गई',
  Closed: 'बंद',
}

/** User roles (UserRole) - wire values are lowercase. */
const USER_ROLE_EN: EnumMap = {
  citizen: 'Citizen',
  officer: 'Field / District Officer',
  auditor: 'Auditor',
  admin: 'MPLAD Administrator',
}

const USER_ROLE_HI: EnumMap = {
  citizen: 'नागरिक',
  officer: 'क्षेत्र / जिला अधिकारी',
  auditor: 'लेखा परीक्षक',
  admin: 'एमपीलैड प्रशासक',
}

/**
 * Activity-log verbs (ActivityType). These are snake_case on the wire and have
 * never been human-readable, so English needs a map too.
 */
const ACTIVITY_TYPE_EN: EnumMap = {
  project_created: 'Work created',
  project_updated: 'Work updated',
  status_changed: 'Status changed',
  review_status_changed: 'Review status changed',
  project_reviewed: 'Work reviewed',
  risk_assessed: 'Risk assessed',
  risk_level_changed: 'Risk level changed',
  risk_status_changed: 'Risk status changed',
  note_added: 'Note added',
  mitigation_added: 'Mitigation added',
  mitigation_updated: 'Mitigation updated',
  mitigation_resolved: 'Mitigation resolved',
  progress_updated: 'Progress updated',
  fund_updated: 'Funds updated',
  report_exported: 'Report exported',
  citizen_report_filed: 'Citizen report filed',
  citizen_report_triaged: 'Citizen report triaged',
  access_requested: 'Official access requested',
  access_approved: 'Official access approved',
  access_rejected: 'Official access rejected',
  role_changed: 'Role changed',
}

const ACTIVITY_TYPE_HI: EnumMap = {
  project_created: 'कार्य बनाया गया',
  project_updated: 'कार्य अद्यतन',
  status_changed: 'स्थिति बदली',
  review_status_changed: 'समीक्षा स्थिति बदली',
  project_reviewed: 'कार्य की समीक्षा हुई',
  risk_assessed: 'जोखिम आकलन हुआ',
  risk_level_changed: 'जोखिम स्तर बदला',
  risk_status_changed: 'जोखिम स्थिति बदली',
  note_added: 'टिप्पणी जोड़ी गई',
  mitigation_added: 'न्यूनीकरण जोड़ा गया',
  mitigation_updated: 'न्यूनीकरण अद्यतन',
  mitigation_resolved: 'न्यूनीकरण पूर्ण',
  progress_updated: 'प्रगति अद्यतन',
  fund_updated: 'निधि अद्यतन',
  report_exported: 'रिपोर्ट निर्यात हुई',
  citizen_report_filed: 'नागरिक शिकायत दर्ज',
  citizen_report_triaged: 'नागरिक शिकायत पर कार्रवाई',
  access_requested: 'आधिकारिक पहुँच का अनुरोध',
  access_approved: 'आधिकारिक पहुँच स्वीकृत',
  access_rejected: 'आधिकारिक पहुँच अस्वीकृत',
  role_changed: 'भूमिका बदली',
}

/**
 * Every enum family the UI can render. `en` is omitted where the wire value is
 * already the English label we want to show.
 */
const REGISTRY = {
  projectStatus: { hi: PROJECT_STATUS_HI },
  reviewStatus: { hi: REVIEW_STATUS_HI },
  riskLevel: { hi: RISK_LEVEL_HI },
  riskCategory: { hi: RISK_CATEGORY_HI },
  analysisSource: { en: ANALYSIS_SOURCE_EN, hi: ANALYSIS_SOURCE_HI },
  likelihood: { hi: LIKELIHOOD_HI },
  impact: { hi: IMPACT_HI },
  riskStatus: { hi: RISK_STATUS_HI },
  mitigationStatus: { hi: MITIGATION_STATUS_HI },
  noteType: { hi: NOTE_TYPE_HI },
  publicIndicator: { hi: PUBLIC_INDICATOR_HI },
  accessRequestStatus: { hi: ACCESS_REQUEST_STATUS_HI },
  reportCategory: { hi: REPORT_CATEGORY_HI },
  reportStatus: { hi: REPORT_STATUS_HI },
  userRole: { en: USER_ROLE_EN, hi: USER_ROLE_HI },
  activityType: { en: ACTIVITY_TYPE_EN, hi: ACTIVITY_TYPE_HI },

  // Controlled vocabularies that arrive as data rather than as enums. See
  // `vocabulary.ts` for why these belong here and what is deliberately left out.
  state: { hi: STATE_HI },
  district: { hi: DISTRICT_HI },
  constituency: { hi: CONSTITUENCY_HI },
  category: { hi: CATEGORY_HI },
  agency: { hi: AGENCY_HI },
  riskFactorTitle: { hi: RISK_FACTOR_TITLE_HI },
  bucket: { hi: BUCKET_HI },
} satisfies Record<string, { en?: EnumMap; hi?: EnumMap }>

export type EnumFamily = keyof typeof REGISTRY

/**
 * Translate one wire value.
 *
 * Falls back to the English map, then to the raw value, so an enum the backend
 * adds tomorrow still renders as readable text instead of disappearing.
 */
export function translateEnum(
  family: EnumFamily,
  value: string | null | undefined,
  language: Language,
): string {
  if (value === null || value === undefined || value === '') return ''
  const maps = REGISTRY[family] as { en?: EnumMap; hi?: EnumMap }
  if (language === 'hi') {
    const hindi = maps.hi?.[value]
    if (hindi) return hindi
  }
  return maps.en?.[value] ?? value
}
