"""Project querying, filtering and presentation helpers."""
from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Dict, List, Optional, Sequence, Tuple

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundError
from app.models.citizen_report import CitizenReport
from app.core.enums import (
    CitizenReportStatus,
    ProjectStatus,
    PublicRiskIndicator,
    ReviewStatus,
    RiskLevel,
)
from app.models.project import Project
from app.models.review import Review
from app.models.risk import MitigationAction, RiskAssessment
from app.core.enums import MitigationStatus
from app.schemas.common import FilterOptions, OptionCount
from app.schemas.project import (
    ProgressPoint,
    ProjectAdminDetail,
    ProjectAdminSummary,
    ProjectPublicDetail,
    ProjectPublicSummary,
    TimelinePoint,
)

SORTABLE_FIELDS = {
    "project_code": Project.project_code,
    "title": Project.title,
    "district": Project.district,
    "category": Project.category,
    "mp_name": Project.mp_name,
    "allocated_amount": Project.allocated_amount,
    "spent_amount": Project.spent_amount,
    "progress_percent": Project.progress_percent,
    "sanction_year": Project.sanction_year,
    "status": Project.status,
    "updated_at": Project.updated_at,
}


# ---------------------------------------------------------------------------
# Query building
# ---------------------------------------------------------------------------
def build_project_query(
    *,
    search: Optional[str] = None,
    mp: Optional[str] = None,
    district: Optional[str] = None,
    state: Optional[str] = None,
    category: Optional[str] = None,
    agency: Optional[str] = None,
    year: Optional[int] = None,
    status: Optional[ProjectStatus] = None,
    review_status: Optional[ReviewStatus] = None,
    min_allocation: Optional[float] = None,
    max_allocation: Optional[float] = None,
    overdue_only: bool = False,
) -> Select:
    stmt = select(Project)
    if search:
        term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Project.project_code).like(term),
                func.lower(Project.title).like(term),
                func.lower(Project.description).like(term),
                func.lower(Project.mp_name).like(term),
                func.lower(Project.district).like(term),
                func.lower(Project.category).like(term),
                func.lower(Project.executing_agency).like(term),
                func.lower(Project.location).like(term),
            )
        )
    if mp:
        stmt = stmt.where(Project.mp_name == mp)
    if district:
        stmt = stmt.where(Project.district == district)
    if state:
        stmt = stmt.where(Project.state == state)
    if category:
        stmt = stmt.where(Project.category == category)
    if agency:
        stmt = stmt.where(Project.executing_agency == agency)
    if year:
        stmt = stmt.where(Project.sanction_year == year)
    if status:
        stmt = stmt.where(Project.status == status)
    if review_status:
        stmt = stmt.where(Project.review_status == review_status)
    if min_allocation is not None:
        stmt = stmt.where(Project.allocated_amount >= min_allocation)
    if max_allocation is not None:
        stmt = stmt.where(Project.allocated_amount <= max_allocation)
    if overdue_only:
        stmt = stmt.where(
            Project.planned_end_date < date.today(),
            Project.status.notin_([ProjectStatus.COMPLETED, ProjectStatus.CANCELLED]),
        )
    return stmt


def apply_sort(stmt: Select, sort_by: str, sort_dir: str) -> Select:
    column = SORTABLE_FIELDS.get(sort_by, Project.updated_at)
    return stmt.order_by(column.desc() if sort_dir == "desc" else column.asc())


def paginate(db: Session, stmt: Select, page: int, page_size: int) -> Tuple[List[Project], int]:
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).scalars().unique().all()
    return list(rows), int(total)


def get_project_or_404(db: Session, project_id: int, *, with_details: bool = False) -> Project:
    stmt = select(Project).where(Project.id == project_id)
    if with_details:
        stmt = stmt.options(
            selectinload(Project.fund_updates),
            selectinload(Project.progress_updates),
            selectinload(Project.risk_assessments).selectinload(RiskAssessment.factors),
            selectinload(Project.risk_assessments).selectinload(RiskAssessment.mitigations),
        )
    project = db.execute(stmt).scalars().unique().one_or_none()
    if project is None:
        raise NotFoundError(f"Project {project_id} was not found.")
    return project


def get_by_code(db: Session, code: str) -> Optional[Project]:
    return db.execute(select(Project).where(Project.project_code == code)).scalars().first()


# ---------------------------------------------------------------------------
# Derived data
# ---------------------------------------------------------------------------
def current_assessment(db: Session, project_id: int) -> Optional[RiskAssessment]:
    stmt = (
        select(RiskAssessment)
        .where(RiskAssessment.project_id == project_id, RiskAssessment.is_current.is_(True))
        .options(selectinload(RiskAssessment.factors), selectinload(RiskAssessment.mitigations))
        .order_by(RiskAssessment.assessed_at.desc())
    )
    return db.execute(stmt).scalars().first()


def current_assessments_map(db: Session, project_ids: Sequence[int]) -> Dict[int, RiskAssessment]:
    if not project_ids:
        return {}
    stmt = (
        select(RiskAssessment)
        .where(
            RiskAssessment.project_id.in_(list(project_ids)),
            RiskAssessment.is_current.is_(True),
        )
        .options(selectinload(RiskAssessment.factors))
    )
    out: Dict[int, RiskAssessment] = {}
    for assessment in db.execute(stmt).scalars().unique().all():
        out[assessment.project_id] = assessment
    return out


def open_mitigation_counts(db: Session, project_ids: Sequence[int]) -> Dict[int, int]:
    if not project_ids:
        return {}
    stmt = (
        select(MitigationAction.project_id, func.count())
        .where(
            MitigationAction.project_id.in_(list(project_ids)),
            MitigationAction.status != MitigationStatus.RESOLVED,
        )
        .group_by(MitigationAction.project_id)
    )
    return {pid: int(count) for pid, count in db.execute(stmt).all()}


def last_review_map(db: Session, project_ids: Sequence[int]) -> Dict[int, "date"]:
    if not project_ids:
        return {}
    stmt = (
        select(Review.project_id, func.max(Review.review_date))
        .where(Review.project_id.in_(list(project_ids)))
        .group_by(Review.project_id)
    )
    return {pid: value for pid, value in db.execute(stmt).all()}


def open_citizen_report_count(db: Session, project_id: int) -> int:
    stmt = select(func.count()).where(
        CitizenReport.project_id == project_id,
        CitizenReport.status.in_([CitizenReportStatus.SUBMITTED, CitizenReportStatus.UNDER_REVIEW]),
    )
    return int(db.execute(stmt).scalar_one())


def public_indicator(project: Project, assessment: Optional[RiskAssessment]) -> PublicRiskIndicator:
    """FR6 - a public-safe indicator. Raw scores never leave the admin API."""
    if project.review_status in (ReviewStatus.ESCALATED, ReviewStatus.DELAYED):
        return PublicRiskIndicator.UNDER_REVIEW
    if project.status == ProjectStatus.DELAYED:
        return PublicRiskIndicator.UNDER_REVIEW
    if assessment and assessment.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
        return PublicRiskIndicator.UNDER_REVIEW
    return PublicRiskIndicator.NORMAL


def build_spending_timeline(project: Project) -> List[TimelinePoint]:
    buckets: Dict[str, Dict[str, float]] = defaultdict(lambda: {"spent": 0.0, "released": 0.0})
    for update in sorted(project.fund_updates, key=lambda u: u.updated_on):
        period = update.updated_on.strftime("%Y-%m")
        buckets[period]["spent"] += float(update.expenditure_amount or 0.0)
        buckets[period]["released"] += float(update.released_amount or 0.0)

    points: List[TimelinePoint] = []
    cumulative = 0.0
    allocated = float(project.allocated_amount or 0.0)
    for period in sorted(buckets):
        spent = round(buckets[period]["spent"], 2)
        cumulative = round(cumulative + spent, 2)
        points.append(
            TimelinePoint(
                period=period,
                allocated=allocated,
                spent=spent,
                cumulative_spent=cumulative,
                utilization_percent=round(cumulative / allocated * 100, 2) if allocated else 0.0,
            )
        )
    return points


def build_progress_timeline(project: Project) -> List[ProgressPoint]:
    points: List[ProgressPoint] = []
    for update in sorted(project.progress_updates, key=lambda u: u.updated_on):
        points.append(
            ProgressPoint(
                period=update.updated_on.strftime("%Y-%m"),
                actual=round(float(update.progress_percent or 0.0), 2),
                planned=(
                    round(float(update.planned_progress_percent), 2)
                    if update.planned_progress_percent is not None
                    else None
                ),
            )
        )
    return points


def _days_remaining(project: Project) -> Optional[int]:
    if not project.planned_end_date:
        return None
    return (project.planned_end_date - date.today()).days


def _is_overdue(project: Project) -> bool:
    if not project.planned_end_date:
        return False
    return (
        project.planned_end_date < date.today()
        and project.status not in (ProjectStatus.COMPLETED, ProjectStatus.CANCELLED)
    )


# ---------------------------------------------------------------------------
# Serialisation - citizen (public-safe)
# ---------------------------------------------------------------------------
def to_public_summary(project: Project, assessment: Optional[RiskAssessment]) -> ProjectPublicSummary:
    return ProjectPublicSummary(
        id=project.id,
        project_code=project.project_code,
        title=project.title,
        mp_name=project.mp_name,
        constituency=project.constituency,
        state=project.state,
        district=project.district,
        category=project.category,
        executing_agency=project.executing_agency,
        sanction_year=project.sanction_year,
        start_date=project.start_date,
        planned_end_date=project.planned_end_date,
        allocated_amount=round(float(project.allocated_amount or 0), 2),
        spent_amount=round(float(project.spent_amount or 0), 2),
        remaining_amount=project.remaining_amount,
        utilization_percent=project.utilization_percent,
        progress_percent=round(float(project.progress_percent or 0), 2),
        status=project.status,
        public_indicator=public_indicator(project, assessment),
        latitude=project.latitude,
        longitude=project.longitude,
    )


def to_public_detail(project: Project, assessment: Optional[RiskAssessment]) -> ProjectPublicDetail:
    base = to_public_summary(project, assessment)
    return ProjectPublicDetail(
        **base.model_dump(),
        description=project.description or "",
        house=project.house,
        block=project.block,
        location=project.location,
        # latitude / longitude arrive via **base.model_dump(); passing them
        # again here is a duplicate keyword argument at runtime.
        contractor=project.contractor,
        sanction_date=project.sanction_date,
        actual_end_date=project.actual_end_date,
        estimated_cost=project.estimated_cost,
        beneficiaries=project.beneficiaries,
        photo_url=project.photo_url,
        document_url=project.document_url,
        fund_updates=[u for u in sorted(project.fund_updates, key=lambda x: x.updated_on)],
        progress_updates=[u for u in sorted(project.progress_updates, key=lambda x: x.updated_on)],
        spending_timeline=build_spending_timeline(project),
        progress_timeline=build_progress_timeline(project),
        days_remaining=_days_remaining(project),
        is_overdue=_is_overdue(project),
    )


# ---------------------------------------------------------------------------
# Serialisation - admin (internal)
# ---------------------------------------------------------------------------
def to_admin_summary(
    project: Project,
    assessment: Optional[RiskAssessment],
    open_mitigations: int = 0,
    last_reviewed=None,
) -> ProjectAdminSummary:
    base = to_public_summary(project, assessment)
    expected = None
    if project.start_date and project.planned_end_date and project.planned_end_date > project.start_date:
        duration = (project.planned_end_date - project.start_date).days
        elapsed = max((date.today() - project.start_date).days, 0)
        expected = round(min(elapsed / duration * 100, 100.0), 2)
    variance = (
        round(float(project.progress_percent or 0) - expected, 2) if expected is not None else None
    )
    return ProjectAdminSummary(
        **base.model_dump(),
        review_status=project.review_status,
        planned_progress_percent=project.planned_progress_percent,
        risk_level=assessment.risk_level if assessment else None,
        risk_score=round(assessment.risk_score, 2) if assessment else None,
        open_risk_factors=len(assessment.factors) if assessment else 0,
        open_mitigations=open_mitigations,
        is_overdue=_is_overdue(project),
        days_remaining=_days_remaining(project),
        schedule_variance=variance,
        last_reviewed_at=last_reviewed,
    )


def to_admin_detail(
    db: Session,
    project: Project,
    assessment: Optional[RiskAssessment],
    open_mitigations: int = 0,
    last_reviewed=None,
) -> ProjectAdminDetail:
    summary = to_admin_summary(project, assessment, open_mitigations, last_reviewed)

    time_elapsed_percent = None
    if project.start_date and project.planned_end_date and project.planned_end_date > project.start_date:
        duration = (project.planned_end_date - project.start_date).days
        elapsed = max((date.today() - project.start_date).days, 0)
        time_elapsed_percent = round(min(elapsed / duration * 100, 100.0), 2)

    expected_utilization = time_elapsed_percent
    expected_progress = (
        float(project.planned_progress_percent)
        if project.planned_progress_percent is not None
        else time_elapsed_percent
    )

    return ProjectAdminDetail(
        **summary.model_dump(),
        description=project.description or "",
        house=project.house,
        block=project.block,
        location=project.location,
        # latitude / longitude arrive via **base.model_dump(); passing them
        # again here is a duplicate keyword argument at runtime.
        contractor=project.contractor,
        sanction_date=project.sanction_date,
        actual_end_date=project.actual_end_date,
        estimated_cost=project.estimated_cost,
        beneficiaries=project.beneficiaries,
        photo_url=project.photo_url,
        document_url=project.document_url,
        remarks=project.remarks,
        created_at=project.created_at,
        updated_at=project.updated_at,
        fund_updates=[u for u in sorted(project.fund_updates, key=lambda x: x.updated_on)],
        progress_updates=[u for u in sorted(project.progress_updates, key=lambda x: x.updated_on)],
        spending_timeline=build_spending_timeline(project),
        progress_timeline=build_progress_timeline(project),
        expected_progress_percent=expected_progress,
        expected_utilization_percent=expected_utilization,
        citizen_report_count=open_citizen_report_count(db, project.id),
    )


# ---------------------------------------------------------------------------
# Filter option facets
# ---------------------------------------------------------------------------
def _facet(db: Session, column) -> List[OptionCount]:
    stmt = select(column, func.count()).group_by(column).order_by(func.count().desc())
    out: List[OptionCount] = []
    for value, count in db.execute(stmt).all():
        if value is None:
            continue
        out.append(OptionCount(label=str(value), value=str(value), count=int(count)))
    return out


def filter_options(db: Session) -> FilterOptions:
    years = _facet(db, Project.sanction_year)
    years.sort(key=lambda o: o.value, reverse=True)
    return FilterOptions(
        mps=_facet(db, Project.mp_name),
        districts=_facet(db, Project.district),
        states=_facet(db, Project.state),
        categories=_facet(db, Project.category),
        agencies=_facet(db, Project.executing_agency),
        years=years,
        statuses=_facet(db, Project.status),
    )


def recalculate_totals(project: Project) -> None:
    """Keep the denormalised spent figure consistent with the fund trail."""
    if project.fund_updates:
        project.spent_amount = round(
            sum(float(u.expenditure_amount or 0.0) for u in project.fund_updates), 2
        )
    if project.progress_updates:
        latest = max(project.progress_updates, key=lambda u: u.updated_on)
        project.progress_percent = float(latest.progress_percent or 0.0)
        if latest.planned_progress_percent is not None:
            project.planned_progress_percent = float(latest.planned_progress_percent)
