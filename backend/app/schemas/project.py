from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import ProjectStatus, PublicRiskIndicator, ReviewStatus, RiskLevel


# --------------------------------------------------------------------------
# Shared building blocks
# --------------------------------------------------------------------------
class FundUpdateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_on: date
    installment_no: Optional[int] = None
    released_amount: float
    expenditure_amount: float
    cumulative_spent: float
    voucher_reference: Optional[str] = None
    remarks: Optional[str] = None


class FundUpdateCreate(BaseModel):
    updated_on: date
    installment_no: Optional[int] = None
    released_amount: float = Field(ge=0)
    expenditure_amount: float = Field(ge=0)
    voucher_reference: Optional[str] = Field(default=None, max_length=80)
    remarks: Optional[str] = None


class ProgressUpdateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_on: date
    progress_percent: float
    planned_progress_percent: Optional[float] = None
    milestone: Optional[str] = None
    remarks: Optional[str] = None


class ProgressUpdateCreate(BaseModel):
    updated_on: date
    progress_percent: float = Field(ge=0, le=100)
    planned_progress_percent: Optional[float] = Field(default=None, ge=0, le=100)
    milestone: Optional[str] = Field(default=None, max_length=200)
    remarks: Optional[str] = None


class TimelinePoint(BaseModel):
    period: str
    allocated: float
    spent: float
    cumulative_spent: float
    utilization_percent: float


class ProgressPoint(BaseModel):
    period: str
    actual: float
    planned: Optional[float] = None


# --------------------------------------------------------------------------
# CITIZEN-FACING (public-safe) shapes - FR4, FR5, FR6, FR7a
# No risk score, no internal notes, no audit trail, no mitigation.
# --------------------------------------------------------------------------
class ProjectPublicSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_code: str
    title: str
    mp_name: str
    constituency: Optional[str] = None
    state: str
    district: str
    category: str
    executing_agency: str
    sanction_year: int
    start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    allocated_amount: float
    spent_amount: float
    remaining_amount: float
    utilization_percent: float
    progress_percent: float
    status: ProjectStatus
    public_indicator: PublicRiskIndicator
    # Coordinates are public information - a citizen is entitled to know where
    # a sanctioned work is. They are on the summary (not only the detail) so
    # the map view can plot a whole filtered result set in one request.
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ProjectPublicDetail(ProjectPublicSummary):
    description: str
    house: str
    block: Optional[str] = None
    location: Optional[str] = None
    # latitude / longitude are inherited from ProjectPublicSummary.
    contractor: Optional[str] = None
    sanction_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    estimated_cost: Optional[float] = None
    beneficiaries: Optional[int] = None
    photo_url: Optional[str] = None
    document_url: Optional[str] = None
    fund_updates: List[FundUpdateOut] = Field(default_factory=list)
    progress_updates: List[ProgressUpdateOut] = Field(default_factory=list)
    spending_timeline: List[TimelinePoint] = Field(default_factory=list)
    progress_timeline: List[ProgressPoint] = Field(default_factory=list)
    days_remaining: Optional[int] = None
    is_overdue: bool = False


# --------------------------------------------------------------------------
# ADMIN-FACING shapes - FR7b, FR11
# --------------------------------------------------------------------------
class ProjectAdminSummary(ProjectPublicSummary):
    review_status: ReviewStatus
    planned_progress_percent: Optional[float] = None
    risk_level: Optional[RiskLevel] = None
    risk_score: Optional[float] = None
    open_risk_factors: int = 0
    open_mitigations: int = 0
    is_overdue: bool = False
    days_remaining: Optional[int] = None
    schedule_variance: Optional[float] = None
    last_reviewed_at: Optional[datetime] = None


class ProjectAdminDetail(ProjectAdminSummary):
    description: str
    house: str
    block: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contractor: Optional[str] = None
    sanction_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    estimated_cost: Optional[float] = None
    beneficiaries: Optional[int] = None
    photo_url: Optional[str] = None
    document_url: Optional[str] = None
    remarks: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    fund_updates: List[FundUpdateOut] = Field(default_factory=list)
    progress_updates: List[ProgressUpdateOut] = Field(default_factory=list)
    spending_timeline: List[TimelinePoint] = Field(default_factory=list)
    progress_timeline: List[ProgressPoint] = Field(default_factory=list)
    expected_progress_percent: Optional[float] = None
    expected_utilization_percent: Optional[float] = None
    citizen_report_count: int = 0


class ProjectCreate(BaseModel):
    project_code: Optional[str] = Field(default=None, max_length=40)
    title: str = Field(min_length=4, max_length=300)
    description: str = ""
    mp_name: str = Field(min_length=2, max_length=160)
    constituency: Optional[str] = Field(default=None, max_length=160)
    house: str = "Lok Sabha"
    state: str = Field(min_length=2, max_length=120)
    district: str = Field(min_length=2, max_length=120)
    block: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category: str = Field(min_length=2, max_length=120)
    executing_agency: str = Field(min_length=2, max_length=200)
    contractor: Optional[str] = None
    sanction_year: int = Field(ge=1993, le=2100)
    sanction_date: Optional[date] = None
    start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    allocated_amount: float = Field(ge=0)
    spent_amount: float = Field(default=0, ge=0)
    estimated_cost: Optional[float] = Field(default=None, ge=0)
    progress_percent: float = Field(default=0, ge=0, le=100)
    planned_progress_percent: Optional[float] = Field(default=None, ge=0, le=100)
    status: ProjectStatus = ProjectStatus.NOT_STARTED
    beneficiaries: Optional[int] = Field(default=None, ge=0)
    photo_url: Optional[str] = None
    document_url: Optional[str] = None
    remarks: Optional[str] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=4, max_length=300)
    description: Optional[str] = None
    mp_name: Optional[str] = None
    constituency: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    block: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    category: Optional[str] = None
    executing_agency: Optional[str] = None
    contractor: Optional[str] = None
    sanction_date: Optional[date] = None
    start_date: Optional[date] = None
    planned_end_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    allocated_amount: Optional[float] = Field(default=None, ge=0)
    spent_amount: Optional[float] = Field(default=None, ge=0)
    estimated_cost: Optional[float] = Field(default=None, ge=0)
    progress_percent: Optional[float] = Field(default=None, ge=0, le=100)
    planned_progress_percent: Optional[float] = Field(default=None, ge=0, le=100)
    status: Optional[ProjectStatus] = None
    beneficiaries: Optional[int] = Field(default=None, ge=0)
    photo_url: Optional[str] = None
    document_url: Optional[str] = None
    remarks: Optional[str] = None


class StatusChangeRequest(BaseModel):
    status: ProjectStatus
    reason: str = Field(min_length=3, max_length=1000)


class BulkImportResult(BaseModel):
    created: int
    skipped: int
    errors: List[str] = Field(default_factory=list)
