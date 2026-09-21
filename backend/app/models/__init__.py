"""SQLAlchemy models. Importing this package registers every mapper."""
from app.models.access_request import AccessRequest
from app.models.activity import ActivityLog
from app.models.citizen_report import CitizenReport
from app.core.enums import (
    ACCESS_REQUESTABLE_ROLES,
    ACTIVE_STATUSES,
    AccessRequestStatus,
    ELEVATED_ROLES,
    INTERNAL_ROLES,
    REVIEWER_ROLES,
    RISK_LEVEL_ORDER,
    ActivityType,
    AnalysisSource,
    CitizenReportCategory,
    CitizenReportStatus,
    Impact,
    Likelihood,
    MitigationStatus,
    NoteType,
    ProjectStatus,
    PublicRiskIndicator,
    ReviewStatus,
    RiskCategory,
    RiskLevel,
    RiskStatus,
    UserRole,
)
from app.models.note import Note
from app.models.project import Project
from app.models.review import Review
from app.models.risk import MitigationAction, RiskAssessment, RiskFactor
from app.models.tracking import FundUpdate, ProgressUpdate
from app.models.user import OtpCode, User

__all__ = [
    "AccessRequest",
    "ActivityLog",
    "CitizenReport",
    "FundUpdate",
    "MitigationAction",
    "Note",
    "OtpCode",
    "Project",
    "ProgressUpdate",
    "Review",
    "RiskAssessment",
    "RiskFactor",
    "User",
    "ACCESS_REQUESTABLE_ROLES",
    "ACTIVE_STATUSES",
    "AccessRequestStatus",
    "ELEVATED_ROLES",
    "INTERNAL_ROLES",
    "REVIEWER_ROLES",
    "RISK_LEVEL_ORDER",
    "ActivityType",
    "AnalysisSource",
    "CitizenReportCategory",
    "CitizenReportStatus",
    "Impact",
    "Likelihood",
    "MitigationStatus",
    "NoteType",
    "ProjectStatus",
    "PublicRiskIndicator",
    "ReviewStatus",
    "RiskCategory",
    "RiskLevel",
    "RiskStatus",
    "UserRole",
]
