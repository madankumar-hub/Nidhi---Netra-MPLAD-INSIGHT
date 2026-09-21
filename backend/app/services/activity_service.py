"""Append-only audit trail writer (NFR: Auditability)."""
from __future__ import annotations

from typing import List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import ActivityLog
from app.core.enums import ActivityType
from app.models.user import User


def log(
    db: Session,
    *,
    project_id: Optional[int],
    activity_type: ActivityType,
    summary: str,
    actor: Optional[User] = None,
    detail: Optional[str] = None,
    from_value: Optional[str] = None,
    to_value: Optional[str] = None,
    commit: bool = False,
) -> ActivityLog:
    entry = ActivityLog(
        project_id=project_id,
        actor_id=actor.id if actor else None,
        actor_name=actor.full_name if actor else "System",
        actor_role=actor.role.value if actor else "system",
        activity_type=activity_type,
        summary=summary[:400],
        detail=detail,
        from_value=from_value[:120] if from_value else None,
        to_value=to_value[:120] if to_value else None,
    )
    db.add(entry)
    if commit:
        db.commit()
        db.refresh(entry)
    else:
        db.flush()
    return entry


def list_for_project(db: Session, project_id: int, limit: int = 100) -> List[ActivityLog]:
    stmt = (
        select(ActivityLog)
        .where(ActivityLog.project_id == project_id)
        .order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def list_recent(
    db: Session, limit: int = 50, activity_types: Optional[Sequence[ActivityType]] = None
) -> List[ActivityLog]:
    stmt = select(ActivityLog).order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
    if activity_types:
        stmt = stmt.where(ActivityLog.activity_type.in_(list(activity_types)))
    return list(db.execute(stmt.limit(limit)).scalars().all())
