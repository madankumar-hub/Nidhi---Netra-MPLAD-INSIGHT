from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.core.enums import NoteType


class Note(Base, TimestampMixin):
    """Internal administrative note. Never exposed to the citizen role."""

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    author_name: Mapped[str] = mapped_column(String(160), nullable=False)
    author_role: Mapped[str] = mapped_column(String(32), nullable=False)

    note_type: Mapped[NoteType] = mapped_column(
        SAEnum(NoteType, native_enum=False, length=32), default=NoteType.GENERAL, nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="notes")
    author: Mapped[Optional["User"]] = relationship(back_populates="notes")
