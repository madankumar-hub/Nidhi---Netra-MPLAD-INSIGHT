"""Persisted review workflow (FR13) and project status transitions."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.base import utcnow
from app.core.enums import ActivityType, ProjectStatus, ReviewStatus
from app.models.project import Project
from app.models.review import Review
from app.models.user import User
from app.schemas.workflow import ReviewCreate
from app.services import activity_service


def list_for_project(db: Session, project_id: int) -> List[Review]:
    stmt = (
        select(Review)
        .where(Review.project_id == project_id)
        .order_by(Review.review_date.desc(), Review.id.desc())
    )
    return list(db.execute(stmt).scalars().all())


def create_review(db: Session, project: Project, payload: ReviewCreate, actor: User) -> Review:
    previous = project.review_status
    review = Review(
        project_id=project.id,
        reviewer_id=actor.id,
        reviewer_name=actor.full_name,
        reviewer_role=actor.role.value,
        review_date=utcnow(),
        previous_status=previous,
        status=payload.status,
        findings=payload.findings,
        notes=payload.notes,
        action_required=payload.action_required,
        escalated_to=payload.escalated_to,
        follow_up_required=payload.follow_up_required,
    )
    db.add(review)

    project.review_status = payload.status
    activity_service.log(
        db,
        project_id=project.id,
        activity_type=ActivityType.PROJECT_REVIEWED,
        summary=f"Project reviewed by {actor.full_name} - outcome: {payload.status.value}.",
        actor=actor,
        detail=payload.findings,
    )
    if previous != payload.status:
        activity_service.log(
            db,
            project_id=project.id,
            activity_type=ActivityType.REVIEW_STATUS_CHANGED,
            summary=f"Review status changed: {previous.value} -> {payload.status.value}.",
            actor=actor,
            from_value=previous.value,
            to_value=payload.status.value,
        )

    # Keep execution status and review outcome consistent for the two
    # outcomes where the SRS workflow implies a state change.
    if payload.status == ReviewStatus.DELAYED and project.status not in (
        ProjectStatus.COMPLETED,
        ProjectStatus.CANCELLED,
    ):
        change_status(db, project, ProjectStatus.DELAYED, "Set by review outcome", actor, commit=False)

    db.commit()
    db.refresh(review)
    return review


def change_status(
    db: Session,
    project: Project,
    new_status: ProjectStatus,
    reason: str,
    actor: Optional[User],
    *,
    commit: bool = True,
) -> Project:
    previous = project.status
    if previous == new_status:
        return project
    project.status = new_status
    if new_status == ProjectStatus.COMPLETED and project.actual_end_date is None:
        project.actual_end_date = utcnow().date()

    activity_service.log(
        db,
        project_id=project.id,
        activity_type=ActivityType.STATUS_CHANGED,
        summary=f"Project status changed: {previous.value} -> {new_status.value}.",
        actor=actor,
        detail=reason,
        from_value=previous.value,
        to_value=new_status.value,
    )
    if commit:
        db.commit()
        db.refresh(project)
    return project


def change_review_status(
    db: Session, project: Project, new_status: ReviewStatus, reason: str, actor: User
) -> Project:
    previous = project.review_status
    if previous == new_status:
        return project
    project.review_status = new_status
    activity_service.log(
        db,
        project_id=project.id,
        activity_type=ActivityType.REVIEW_STATUS_CHANGED,
        summary=f"Review status changed: {previous.value} -> {new_status.value}.",
        actor=actor,
        detail=reason,
        from_value=previous.value,
        to_value=new_status.value,
    )
    db.commit()
    db.refresh(project)
    return project
