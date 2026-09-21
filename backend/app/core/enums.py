"""Domain enumerations (shared vocabulary; no ORM dependency).

Terminology follows the SRS (SIH26102). String values are stored in the
database and travel unchanged to the API and the frontend.
"""
from __future__ import annotations

from enum import Enum


class UserRole(str, Enum):
    """SRS 2.2 / FR2 - RBAC user classes."""

    CITIZEN = "citizen"
    OFFICER = "officer"          # Field / District Officer
    AUDITOR = "auditor"          # Auditor
    ADMIN = "admin"              # MPLAD Admin


#: Roles allowed to see internal risk scores, notes, audit trail, mitigation.
INTERNAL_ROLES = {UserRole.OFFICER, UserRole.AUDITOR, UserRole.ADMIN}
#: Roles allowed to perform administrative write actions.
REVIEWER_ROLES = {UserRole.OFFICER, UserRole.AUDITOR, UserRole.ADMIN}
#: Roles allowed to manage users / delete records.
ELEVATED_ROLES = {UserRole.AUDITOR, UserRole.ADMIN}
#: Roles a citizen may ask to be granted. Administrator is deliberately not on
#: this list - it is provisioned directly by an existing administrator only.
ACCESS_REQUESTABLE_ROLES = {UserRole.OFFICER, UserRole.AUDITOR}


class ProjectStatus(str, Enum):
    """Execution status of an MPLAD work."""

    NOT_STARTED = "Not Started"
    IN_PROGRESS = "In Progress"
    DELAYED = "Delayed"
    ON_HOLD = "On Hold"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"


#: Statuses that count as "active" on dashboards.
ACTIVE_STATUSES = {ProjectStatus.NOT_STARTED, ProjectStatus.IN_PROGRESS, ProjectStatus.DELAYED}


class ReviewStatus(str, Enum):
    """Administrative review workflow state (FR13)."""

    PENDING_REVIEW = "Pending Review"
    REVIEWED = "Reviewed"
    ON_TRACK = "On Track"
    DELAYED = "Delayed"
    ESCALATED = "Escalated"
    RESOLVED = "Resolved"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


RISK_LEVEL_ORDER = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}


class RiskCategory(str, Enum):
    SCHEDULE = "Schedule Risk"
    FINANCIAL = "Financial Risk"
    EXPENDITURE = "Expenditure Risk"
    PROGRESS = "Progress Risk"
    IMPLEMENTATION = "Implementation Risk"
    COMPLETION = "Completion Risk"
    DUPLICATION = "Duplication Risk"


class AnalysisSource(str, Enum):
    """Which layer produced a finding. Kept explicit so the UI never claims
    an external model was involved when only deterministic rules ran."""

    RULE_BASED = "rule_based"
    STATISTICAL = "statistical"
    MACHINE_LEARNING = "machine_learning"
    EXTERNAL_AI = "external_ai"


class Likelihood(str, Enum):
    RARE = "Rare"
    UNLIKELY = "Unlikely"
    POSSIBLE = "Possible"
    LIKELY = "Likely"
    ALMOST_CERTAIN = "Almost Certain"


class Impact(str, Enum):
    NEGLIGIBLE = "Negligible"
    MINOR = "Minor"
    MODERATE = "Moderate"
    MAJOR = "Major"
    SEVERE = "Severe"


class RiskStatus(str, Enum):
    OPEN = "Open"
    UNDER_REVIEW = "Under Review"
    MITIGATED = "Mitigated"
    ACCEPTED = "Accepted"
    CLOSED = "Closed"


class MitigationStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"


class NoteType(str, Enum):
    REVIEW = "Review Note"
    RISK = "Risk Note"
    DELAY = "Delay Note"
    GENERAL = "General Note"
    ACTION = "Action Note"


class ActivityType(str, Enum):
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    STATUS_CHANGED = "status_changed"
    REVIEW_STATUS_CHANGED = "review_status_changed"
    PROJECT_REVIEWED = "project_reviewed"
    RISK_ASSESSED = "risk_assessed"
    RISK_LEVEL_CHANGED = "risk_level_changed"
    RISK_STATUS_CHANGED = "risk_status_changed"
    NOTE_ADDED = "note_added"
    MITIGATION_ADDED = "mitigation_added"
    MITIGATION_UPDATED = "mitigation_updated"
    MITIGATION_RESOLVED = "mitigation_resolved"
    PROGRESS_UPDATED = "progress_updated"
    FUND_UPDATED = "fund_updated"
    REPORT_EXPORTED = "report_exported"
    CITIZEN_REPORT_FILED = "citizen_report_filed"
    CITIZEN_REPORT_TRIAGED = "citizen_report_triaged"
    ACCESS_REQUESTED = "access_requested"
    ACCESS_APPROVED = "access_approved"
    ACCESS_REJECTED = "access_rejected"
    ROLE_CHANGED = "role_changed"


class PublicRiskIndicator(str, Enum):
    """FR6 - public-safe indicator. Citizens never see raw scores."""

    NORMAL = "Normal"
    UNDER_REVIEW = "Under Review"


class AccessRequestStatus(str, Enum):
    """Lifecycle of a request to be granted an official role."""

    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    WITHDRAWN = "Withdrawn"


class CitizenReportCategory(str, Enum):
    WORK_NOT_STARTED = "Work Not Started"
    POOR_QUALITY = "Poor Quality of Work"
    INCOMPLETE_WORK = "Incomplete Work"
    WRONG_LOCATION = "Wrong Location"
    INFORMATION_INCORRECT = "Information Incorrect"
    OTHER = "Other"


class CitizenReportStatus(str, Enum):
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    ACTION_TAKEN = "Action Taken"
    CLOSED = "Closed"
