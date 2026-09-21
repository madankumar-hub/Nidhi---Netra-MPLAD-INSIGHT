"""Citizen-facing project APIs (FR4, FR5, FR6, FR7, FR7a).

Everything in this module is public-safe. Raw risk scores, risk factors,
internal notes, mitigation actions, reviews and the audit trail are NOT
reachable from here under any circumstances - not even for an admin token.
Internal data lives exclusively under `/api/admin/...`.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.rate_limit import REPORT_LIMIT
from app.core.rate_limit_deps import rate_limit
from app.core.enums import ProjectStatus
from app.models.user import User
from app.schemas.analytics import PublicAnalytics
from app.schemas.common import FilterOptions, Page
from app.schemas.project import ProjectPublicDetail, ProjectPublicSummary
from app.schemas.workflow import CitizenReportCreate, CitizenReportOut
from app.database.session import get_db
from app.services import analytics_service, project_service
from app.services.citizen_report_service import create_report, list_reports_for_user

router = APIRouter(prefix="/projects", tags=["Citizen Portal"])


@router.get("", response_model=Page[ProjectPublicSummary])
def list_projects(
    db: Session = Depends(get_db),
    search: Optional[str] = Query(default=None, max_length=200),
    mp: Optional[str] = None,
    district: Optional[str] = None,
    state: Optional[str] = None,
    category: Optional[str] = None,
    agency: Optional[str] = None,
    year: Optional[int] = None,
    project_status: Optional[ProjectStatus] = Query(default=None, alias="status"),
    sort_by: str = Query(default="updated_at"),
    sort_dir: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    # The cap is 500 rather than 100 so the map view can plot a whole filtered
    # result set in one request instead of one page of twelve. This is a public
    # transparency portal - bulk reading of published data is the point.
    page_size: int = Query(default=12, ge=1, le=500),
) -> Page[ProjectPublicSummary]:
    """Search and filter MPLAD works. Backend-driven - no client-side faking."""
    stmt = project_service.build_project_query(
        search=search,
        mp=mp,
        district=district,
        state=state,
        category=category,
        agency=agency,
        year=year,
        status=project_status,
    )
    stmt = project_service.apply_sort(stmt, sort_by, sort_dir)
    rows, total = project_service.paginate(db, stmt, page, page_size)
    assessments = project_service.current_assessments_map(db, [p.id for p in rows])
    items = [project_service.to_public_summary(p, assessments.get(p.id)) for p in rows]
    return Page[ProjectPublicSummary](
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=max((total + page_size - 1) // page_size, 1),
    )


@router.get("/filters", response_model=FilterOptions)
def get_filters(db: Session = Depends(get_db)) -> FilterOptions:
    return project_service.filter_options(db)


@router.get("/statistics", response_model=PublicAnalytics)
def public_statistics(db: Session = Depends(get_db)) -> PublicAnalytics:
    """Aggregate figures safe for the public portal."""
    return analytics_service.public_analytics(db)


@router.get("/{project_id}", response_model=ProjectPublicDetail)
def get_project(project_id: int, db: Session = Depends(get_db)) -> ProjectPublicDetail:
    """Citizen scheme detail page (FR7a): funds, timeline, agency, progress."""
    project = project_service.get_project_or_404(db, project_id, with_details=True)
    assessment = project_service.current_assessment(db, project_id)
    return project_service.to_public_detail(project, assessment)


@router.post(
    "/{project_id}/reports",
    response_model=CitizenReportOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(REPORT_LIMIT, "citizen-report"))],
)
def file_report(
    project_id: int,
    payload: CitizenReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CitizenReportOut:
    """FR7 - a logged-in citizen flags a work for community feedback."""
    project_service.get_project_or_404(db, project_id)
    report = create_report(db, project_id, payload, current_user)
    return CitizenReportOut.model_validate(report, from_attributes=True)


@router.get("/{project_id}/my-reports", response_model=List[CitizenReportOut])
def my_reports(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[CitizenReportOut]:
    """A citizen may see the reports they themselves filed - nobody else's."""
    reports = list_reports_for_user(db, project_id, current_user.id)
    return [CitizenReportOut.model_validate(r, from_attributes=True) for r in reports]
