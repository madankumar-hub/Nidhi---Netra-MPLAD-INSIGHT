"""Administrative analytics (FR11). Internal roles only."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import require_internal
from app.database.session import get_db
from app.core.enums import ProjectStatus, ReviewStatus
from app.models.user import User
from app.schemas.analytics import AdminAnalytics, DashboardSummary
from app.schemas.project import ProjectAdminSummary
from app.services import analytics_service, project_service

router = APIRouter(prefix="/admin", tags=["Admin - Analytics"])


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(
    db: Session = Depends(get_db), current_user: User = Depends(require_internal)
) -> DashboardSummary:
    return analytics_service.dashboard_summary(db)


@router.get("/analytics", response_model=AdminAnalytics)
def analytics(
    db: Session = Depends(get_db), current_user: User = Depends(require_internal)
) -> AdminAnalytics:
    return analytics_service.admin_analytics(db)


@router.get("/delayed-projects", response_model=List[ProjectAdminSummary])
def delayed_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_internal),
    limit: int = Query(default=50, ge=1, le=200),
) -> List[ProjectAdminSummary]:
    stmt = project_service.build_project_query(status=ProjectStatus.DELAYED)
    stmt = project_service.apply_sort(stmt, "progress_percent", "asc").limit(limit)
    rows = list(db.execute(stmt).scalars().unique().all())
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


@router.get("/pending-review", response_model=List[ProjectAdminSummary])
def pending_review(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_internal),
    limit: int = Query(default=50, ge=1, le=200),
) -> List[ProjectAdminSummary]:
    stmt = project_service.build_project_query(review_status=ReviewStatus.PENDING_REVIEW)
    stmt = project_service.apply_sort(stmt, "allocated_amount", "desc").limit(limit)
    rows = list(db.execute(stmt).scalars().unique().all())
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
