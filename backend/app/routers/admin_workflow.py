"""Reviews, notes, activity trail and citizen-report triage. Internal only."""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_internal, require_reviewer
from app.database.session import get_db
from app.core.enums import CitizenReportStatus, NoteType
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.workflow import (
    ActivityOut,
    CitizenReportOut,
    CitizenReportTriage,
    NoteCreate,
    NoteOut,
    NoteUpdate,
    ReviewCreate,
    ReviewOut,
)
from app.services import (
    activity_service,
    citizen_report_service,
    note_service,
    project_service,
    review_service,
    risk_service,
)

router = APIRouter(prefix="/admin", tags=["Admin - Workflow"])


# ---------------------------------------------------------------------------
# Reviews (FR13)
# ---------------------------------------------------------------------------
@router.get("/projects/{project_id}/reviews", response_model=List[ReviewOut])
def list_reviews(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_internal),
) -> List[ReviewOut]:
    return [
        ReviewOut.model_validate(r, from_attributes=True)
        for r in review_service.list_for_project(db, project_id)
    ]


@router.post(
    "/projects/{project_id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED
)
def create_review(
    project_id: int,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> ReviewOut:
    project = project_service.get_project_or_404(db, project_id, with_details=True)
    review = review_service.create_review(db, project, payload, current_user)
    risk_service.run_assessment(db, project, actor=current_user)
    return ReviewOut.model_validate(review, from_attributes=True)


@router.get("/review-queue", response_model=List[ReviewOut])
def recent_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_internal),
    limit: int = Query(default=50, ge=1, le=200),
) -> List[ReviewOut]:
    from sqlalchemy import select

    from app.models.review import Review

    stmt = select(Review).order_by(Review.review_date.desc()).limit(limit)
    return [
        ReviewOut.model_validate(r, from_attributes=True) for r in db.execute(stmt).scalars().all()
    ]


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------
@router.get("/projects/{project_id}/notes", response_model=List[NoteOut])
def list_notes(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_internal),
    note_type: Optional[NoteType] = None,
) -> List[NoteOut]:
    return [
        NoteOut.model_validate(n, from_attributes=True)
        for n in note_service.list_for_project(db, project_id, note_type)
    ]


@router.post(
    "/projects/{project_id}/notes", response_model=NoteOut, status_code=status.HTTP_201_CREATED
)
def add_note(
    project_id: int,
    payload: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> NoteOut:
    project_service.get_project_or_404(db, project_id)
    note = note_service.create_note(db, project_id, payload, current_user)
    return NoteOut.model_validate(note, from_attributes=True)


@router.patch("/notes/{note_id}", response_model=NoteOut)
def update_note(
    note_id: int,
    payload: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> NoteOut:
    note = note_service.get_or_404(db, note_id)
    note = note_service.update_note(db, note, payload, current_user)
    return NoteOut.model_validate(note, from_attributes=True)


@router.delete("/notes/{note_id}", response_model=MessageResponse)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> MessageResponse:
    note = note_service.get_or_404(db, note_id)
    note_service.delete_note(db, note, current_user)
    return MessageResponse(message="Note deleted.")


# ---------------------------------------------------------------------------
# Activity / audit trail
# ---------------------------------------------------------------------------
@router.get("/projects/{project_id}/activity", response_model=List[ActivityOut])
def project_activity(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_internal),
    limit: int = Query(default=100, ge=1, le=500),
) -> List[ActivityOut]:
    return [
        ActivityOut.model_validate(a, from_attributes=True)
        for a in activity_service.list_for_project(db, project_id, limit)
    ]


@router.get("/activity", response_model=List[ActivityOut])
def recent_activity(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_internal),
    limit: int = Query(default=50, ge=1, le=200),
) -> List[ActivityOut]:
    return [
        ActivityOut.model_validate(a, from_attributes=True)
        for a in activity_service.list_recent(db, limit)
    ]


# ---------------------------------------------------------------------------
# Citizen report triage (FR7)
# ---------------------------------------------------------------------------
@router.get("/citizen-reports", response_model=List[CitizenReportOut])
def list_citizen_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_internal),
    project_id: Optional[int] = None,
    report_status: Optional[CitizenReportStatus] = Query(default=None, alias="status"),
) -> List[CitizenReportOut]:
    return [
        CitizenReportOut.model_validate(r, from_attributes=True)
        for r in citizen_report_service.list_reports(db, project_id, report_status)
    ]


@router.get("/projects/{project_id}/citizen-reports", response_model=List[CitizenReportOut])
def project_citizen_reports(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_internal),
) -> List[CitizenReportOut]:
    return [
        CitizenReportOut.model_validate(r, from_attributes=True)
        for r in citizen_report_service.list_reports(db, project_id)
    ]


@router.patch("/citizen-reports/{report_id}", response_model=CitizenReportOut)
def triage_citizen_report(
    report_id: int,
    payload: CitizenReportTriage,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> CitizenReportOut:
    report = citizen_report_service.get_or_404(db, report_id)
    report = citizen_report_service.triage(db, report, payload, current_user)
    return CitizenReportOut.model_validate(report, from_attributes=True)
