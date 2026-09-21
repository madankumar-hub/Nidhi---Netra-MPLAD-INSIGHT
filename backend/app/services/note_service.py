"""Persisted internal notes (never exposed to the citizen role)."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, PermissionDeniedError
from app.core.enums import ActivityType, ELEVATED_ROLES, NoteType
from app.models.note import Note
from app.models.user import User
from app.schemas.workflow import NoteCreate, NoteUpdate
from app.services import activity_service


def list_for_project(db: Session, project_id: int, note_type: Optional[NoteType] = None) -> List[Note]:
    stmt = select(Note).where(Note.project_id == project_id)
    if note_type:
        stmt = stmt.where(Note.note_type == note_type)
    stmt = stmt.order_by(Note.is_pinned.desc(), Note.created_at.desc(), Note.id.desc())
    return list(db.execute(stmt).scalars().all())


def create_note(db: Session, project_id: int, payload: NoteCreate, actor: User) -> Note:
    note = Note(
        project_id=project_id,
        author_id=actor.id,
        author_name=actor.full_name,
        author_role=actor.role.value,
        note_type=payload.note_type,
        content=payload.content,
        is_pinned=payload.is_pinned,
    )
    db.add(note)
    activity_service.log(
        db,
        project_id=project_id,
        activity_type=ActivityType.NOTE_ADDED,
        summary=f"{payload.note_type.value} added by {actor.full_name}.",
        actor=actor,
        detail=payload.content[:500],
    )
    db.commit()
    db.refresh(note)
    return note


def get_or_404(db: Session, note_id: int) -> Note:
    note = db.get(Note, note_id)
    if note is None:
        raise NotFoundError(f"Note {note_id} was not found.")
    return note


def update_note(db: Session, note: Note, payload: NoteUpdate, actor: User) -> Note:
    if note.author_id != actor.id and actor.role not in ELEVATED_ROLES:
        raise PermissionDeniedError("You can only edit notes that you authored.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(note, field, value)
    db.commit()
    db.refresh(note)
    return note


def delete_note(db: Session, note: Note, actor: User) -> None:
    if note.author_id != actor.id and actor.role not in ELEVATED_ROLES:
        raise PermissionDeniedError("You can only delete notes that you authored.")
    project_id = note.project_id
    db.delete(note)
    activity_service.log(
        db,
        project_id=project_id,
        activity_type=ActivityType.NOTE_ADDED,
        summary=f"Note deleted by {actor.full_name}.",
        actor=actor,
    )
    db.commit()
