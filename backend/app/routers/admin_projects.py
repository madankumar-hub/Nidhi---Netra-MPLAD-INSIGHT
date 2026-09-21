"""Administrative project APIs (FR7b, FR11, FR14, FR15).

Every route here is behind `require_internal` - the Citizen role receives
HTTP 403 even with a valid token. This is enforced server-side; frontend
route guards are a convenience only.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_elevated, require_internal, require_reviewer
from app.core.exceptions import ConflictError
from app.database.session import get_db
from app.core.enums import ActivityType, ProjectStatus, ReviewStatus, RiskLevel
from app.models.project import Project
from app.models.risk import RiskAssessment
from app.models.tracking import FundUpdate, ProgressUpdate
from app.models.user import User
from app.schemas.common import FilterOptions, MessageResponse, Page
from app.schemas.project import (
    BulkImportResult,
    FundUpdateCreate,
    FundUpdateOut,
    ProgressUpdateCreate,
    ProgressUpdateOut,
    ProjectAdminDetail,
    ProjectAdminSummary,
    ProjectCreate,
    ProjectUpdate,
    StatusChangeRequest,
)
from app.schemas.risk import FlaggedProject
from app.services import activity_service, export_service, project_service, review_service, risk_service

router = APIRouter(prefix="/admin/projects", tags=["Admin - Projects"])


def _decorate(db: Session, rows: List[Project]) -> List[ProjectAdminSummary]:
    ids = [p.id for p in rows]
    assessments = project_service.current_assessments_map(db, ids)
    mitigations = project_service.open_mitigation_counts(db, ids)
    reviews = project_service.last_review_map(db, ids)
    return [
        project_service.to_admin_summary(
            p, assessments.get(p.id), mitigations.get(p.id, 0), reviews.get(p.id)
        )
        for p in rows
    ]


@router.get("", response_model=Page[ProjectAdminSummary])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_internal),
    search: Optional[str] = Query(default=None, max_length=200),
    mp: Optional[str] = None,
    district: Optional[str] = None,
    state: Optional[str] = None,
    category: Optional[str] = None,
    agency: Optional[str] = None,
    year: Optional[int] = None,
    project_status: Optional[ProjectStatus] = Query(default=None, alias="status"),
    review_status: Optional[ReviewStatus] = None,
    risk_level: Optional[RiskLevel] = None,
    overdue_only: bool = False,
    min_allocation: Optional[float] = None,
    max_allocation: Optional[float] = None,
    sort_by: str = Query(default="updated_at"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
) -> Page[ProjectAdminSummary]:
    stmt = project_service.build_project_query(
        search=search,
        mp=mp,
        district=district,
        state=state,
        category=category,
        agency=agency,
        year=year,
        status=project_status,
        review_status=review_status,
        min_allocation=min_allocation,
        max_allocation=max_allocation,
        overdue_only=overdue_only,
    )
    if risk_level is not None:
        stmt = stmt.join(
            RiskAssessment,
            (RiskAssessment.project_id == Project.id) & (RiskAssessment.is_current.is_(True)),
        ).where(RiskAssessment.risk_level == risk_level)
    stmt = project_service.apply_sort(stmt, sort_by, sort_dir)
    rows, total = project_service.paginate(db, stmt, page, page_size)
    return Page[ProjectAdminSummary](
        items=_decorate(db, rows),
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max((total + page_size - 1) // page_size, 1),
    )


@router.get("/filters", response_model=FilterOptions)
def filters(
    db: Session = Depends(get_db), current_user: User = Depends(require_internal)
) -> FilterOptions:
    return project_service.filter_options(db)


@router.get("/flagged", response_model=List[FlaggedProject])
def flagged_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_internal),
    limit: int = Query(default=25, ge=1, le=200),
    min_score: float = Query(default=25.0, ge=0, le=100),
) -> List[FlaggedProject]:
    """FR10 - ranked list of works flagged for investigation.

    These are indicators requiring verification, not findings of wrongdoing.
    """
    stmt = (
        select(Project, RiskAssessment)
        .join(RiskAssessment, RiskAssessment.project_id == Project.id)
        .where(RiskAssessment.is_current.is_(True), RiskAssessment.risk_score >= min_score)
        .order_by(RiskAssessment.risk_score.desc())
        .limit(limit)
    )
    out: List[FlaggedProject] = []
    for project, assessment in db.execute(stmt).all():
        out.append(
            FlaggedProject(
                project_id=project.id,
                project_code=project.project_code,
                title=project.title,
                district=project.district,
                category=project.category,
                mp_name=project.mp_name,
                allocated_amount=round(project.allocated_amount, 2),
                spent_amount=round(project.spent_amount, 2),
                progress_percent=round(project.progress_percent, 2),
                risk_score=round(assessment.risk_score, 2),
                risk_level=assessment.risk_level,
                primary_category=assessment.primary_category,
                top_factors=[f.title for f in assessment.factors[:3]],
                review_status=project.review_status.value,
            )
        )
    return out


@router.get("/export", response_class=Response)
def export_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_internal),
    search: Optional[str] = None,
    district: Optional[str] = None,
    category: Optional[str] = None,
    project_status: Optional[ProjectStatus] = Query(default=None, alias="status"),
    review_status: Optional[ReviewStatus] = None,
    flagged_only: bool = False,
    export_format: str = Query(
        default="csv", alias="format", pattern="^(csv|pdf)$",
        description="csv for analysis, pdf for a printable report",
    ),
) -> Response:
    """FR12 - export the current selection as CSV or PDF."""
    stmt = project_service.build_project_query(
        search=search, district=district, category=category,
        status=project_status, review_status=review_status,
    )
    if flagged_only:
        stmt = stmt.join(
            RiskAssessment,
            (RiskAssessment.project_id == Project.id) & (RiskAssessment.is_current.is_(True)),
        ).where(RiskAssessment.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL]))
    rows = list(db.execute(stmt).scalars().unique().all())
    assessments = project_service.current_assessments_map(db, [p.id for p in rows])

    if export_format == "pdf":
        content: bytes | str = export_service.projects_to_pdf(rows, assessments, flagged_only)
        media_type = "application/pdf"
        filename = "mplad-flagged-works.pdf" if flagged_only else "mplad-works.pdf"
    else:
        content = export_service.projects_to_csv(rows, assessments)
        media_type = "text/csv"
        filename = "mplad-projects.csv"

    # Every export is auditable: who took what, when, in which format.
    activity_service.log(
        db,
        project_id=None,
        activity_type=ActivityType.REPORT_EXPORTED,
        summary=(
            f"{len(rows)} project record(s) exported to {export_format.upper()}."
        ),
        actor=current_user,
        commit=True,
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("", response_model=ProjectAdminDetail, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> ProjectAdminDetail:
    code = payload.project_code or _next_code(db)
    if project_service.get_by_code(db, code) is not None:
        raise ConflictError(f"A project with code {code} already exists.")
    data = payload.model_dump(exclude={"project_code"})
    project = Project(project_code=code, **data)
    db.add(project)
    db.flush()
    activity_service.log(
        db,
        project_id=project.id,
        activity_type=ActivityType.PROJECT_CREATED,
        summary=f"Project {code} created.",
        actor=current_user,
    )
    db.commit()
    db.refresh(project)
    risk_service.run_assessment(db, project, actor=current_user)
    return _detail(db, project)


def _next_code(db: Session) -> str:
    count = db.execute(select(Project.id)).scalars().all()
    return f"MPLAD-{2026}-{len(count) + 1:05d}"


def _detail(db: Session, project: Project) -> ProjectAdminDetail:
    assessment = project_service.current_assessment(db, project.id)
    mitigations = project_service.open_mitigation_counts(db, [project.id]).get(project.id, 0)
    last_review = project_service.last_review_map(db, [project.id]).get(project.id)
    return project_service.to_admin_detail(db, project, assessment, mitigations, last_review)


@router.get("/{project_id}", response_model=ProjectAdminDetail)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_internal),
) -> ProjectAdminDetail:
    project = project_service.get_project_or_404(db, project_id, with_details=True)
    return _detail(db, project)


@router.patch("/{project_id}", response_model=ProjectAdminDetail)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> ProjectAdminDetail:
    project = project_service.get_project_or_404(db, project_id, with_details=True)
    changes = payload.model_dump(exclude_unset=True)
    status_change = changes.pop("status", None)
    for field, value in changes.items():
        setattr(project, field, value)
    if changes:
        activity_service.log(
            db,
            project_id=project.id,
            activity_type=ActivityType.PROJECT_UPDATED,
            summary=f"Project record updated ({', '.join(sorted(changes))}).",
            actor=current_user,
        )
    if status_change is not None:
        review_service.change_status(
            db, project, status_change, "Updated from the project record form", current_user, commit=False
        )
    db.commit()
    db.refresh(project)
    risk_service.run_assessment(db, project, actor=current_user)
    return _detail(db, project)


@router.delete("/{project_id}", response_model=MessageResponse)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_elevated),
) -> MessageResponse:
    project = project_service.get_project_or_404(db, project_id)
    code = project.project_code
    db.delete(project)
    db.commit()
    return MessageResponse(message=f"Project {code} deleted.")


@router.post("/{project_id}/status", response_model=ProjectAdminDetail)
def change_status(
    project_id: int,
    payload: StatusChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> ProjectAdminDetail:
    """Persisted execution-status transition, e.g. On Track -> Delayed."""
    project = project_service.get_project_or_404(db, project_id, with_details=True)
    review_service.change_status(db, project, payload.status, payload.reason, current_user)
    risk_service.run_assessment(db, project, actor=current_user)
    return _detail(db, project)


# ---------------------------------------------------------------------------
# Fund and progress trails
# ---------------------------------------------------------------------------
@router.get("/{project_id}/fund-updates", response_model=List[FundUpdateOut])
def list_fund_updates(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_internal),
) -> List[FundUpdateOut]:
    project = project_service.get_project_or_404(db, project_id, with_details=True)
    return [
        FundUpdateOut.model_validate(u, from_attributes=True)
        for u in sorted(project.fund_updates, key=lambda x: x.updated_on)
    ]


@router.post(
    "/{project_id}/fund-updates", response_model=FundUpdateOut, status_code=status.HTTP_201_CREATED
)
def add_fund_update(
    project_id: int,
    payload: FundUpdateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> FundUpdateOut:
    project = project_service.get_project_or_404(db, project_id, with_details=True)
    cumulative = sum(float(u.expenditure_amount or 0) for u in project.fund_updates)
    entry = FundUpdate(
        project_id=project.id,
        updated_on=payload.updated_on,
        installment_no=payload.installment_no,
        released_amount=payload.released_amount,
        expenditure_amount=payload.expenditure_amount,
        cumulative_spent=round(cumulative + payload.expenditure_amount, 2),
        voucher_reference=payload.voucher_reference,
        remarks=payload.remarks,
        recorded_by_id=current_user.id,
    )
    db.add(entry)
    db.flush()
    db.refresh(project)
    project_service.recalculate_totals(project)
    activity_service.log(
        db,
        project_id=project.id,
        activity_type=ActivityType.FUND_UPDATED,
        summary=(
            f"Expenditure of Rs {payload.expenditure_amount:,.2f} lakh recorded "
            f"({payload.updated_on})."
        ),
        actor=current_user,
        detail=payload.remarks,
    )
    db.commit()
    db.refresh(entry)
    db.refresh(project)
    risk_service.run_assessment(db, project, actor=current_user)
    return FundUpdateOut.model_validate(entry, from_attributes=True)


@router.get("/{project_id}/progress", response_model=List[ProgressUpdateOut])
def list_progress_updates(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_internal),
) -> List[ProgressUpdateOut]:
    project = project_service.get_project_or_404(db, project_id, with_details=True)
    return [
        ProgressUpdateOut.model_validate(u, from_attributes=True)
        for u in sorted(project.progress_updates, key=lambda x: x.updated_on)
    ]


@router.post(
    "/{project_id}/progress", response_model=ProgressUpdateOut, status_code=status.HTTP_201_CREATED
)
def add_progress_update(
    project_id: int,
    payload: ProgressUpdateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> ProgressUpdateOut:
    project = project_service.get_project_or_404(db, project_id, with_details=True)
    previous = project.progress_percent
    entry = ProgressUpdate(
        project_id=project.id,
        updated_on=payload.updated_on,
        progress_percent=payload.progress_percent,
        planned_progress_percent=payload.planned_progress_percent,
        milestone=payload.milestone,
        remarks=payload.remarks,
        recorded_by_id=current_user.id,
    )
    db.add(entry)
    db.flush()
    db.refresh(project)
    project_service.recalculate_totals(project)
    activity_service.log(
        db,
        project_id=project.id,
        activity_type=ActivityType.PROGRESS_UPDATED,
        summary=f"Physical progress updated: {previous:.1f}% -> {payload.progress_percent:.1f}%.",
        actor=current_user,
        detail=payload.milestone,
        from_value=f"{previous:.1f}%",
        to_value=f"{payload.progress_percent:.1f}%",
    )
    db.commit()
    db.refresh(entry)
    db.refresh(project)
    risk_service.run_assessment(db, project, actor=current_user)
    return ProgressUpdateOut.model_validate(entry, from_attributes=True)


# ---------------------------------------------------------------------------
# Bulk import (FR15)
# ---------------------------------------------------------------------------
@router.post("/bulk-import", response_model=BulkImportResult)
def bulk_import(
    payload: List[ProjectCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_elevated),
) -> BulkImportResult:
    created = 0
    skipped = 0
    errors: List[str] = []
    for index, item in enumerate(payload):
        code = item.project_code or _next_code(db)
        if project_service.get_by_code(db, code) is not None:
            skipped += 1
            continue
        try:
            db.add(Project(project_code=code, **item.model_dump(exclude={"project_code"})))
            db.flush()
            created += 1
        except Exception as exc:  # noqa: BLE001 - reported back to the caller
            db.rollback()
            errors.append(f"Row {index + 1}: {exc}")
    activity_service.log(
        db,
        project_id=None,
        activity_type=ActivityType.PROJECT_CREATED,
        summary=f"Bulk import: {created} created, {skipped} skipped.",
        actor=current_user,
    )
    db.commit()
    return BulkImportResult(created=created, skipped=skipped, errors=errors)
