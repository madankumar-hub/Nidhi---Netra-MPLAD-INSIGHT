from __future__ import annotations

from typing import Optional

from sqlalchemy import Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.core.enums import ActivityType


class ActivityLog(Base, TimestampMixin):
    """Append-only audit trail (NFR: Auditability). Internal roles only."""

    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    actor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    actor_name: Mapped[str] = mapped_column(String(160), default="System", nullable=False)
    actor_role: Mapped[str] = mapped_column(String(32), default="system", nullable=False)

    activity_type: Mapped[ActivityType] = mapped_column(
        SAEnum(ActivityType, native_enum=False, length=40), nullable=False, index=True
    )
    summary: Mapped[str] = mapped_column(String(400), nullable=False)
    detail: Mapped[Optional[str]] = mapped_column(Text)
    from_value: Mapped[Optional[str]] = mapped_column(String(120))
    to_value: Mapped[Optional[str]] = mapped_column(String(120))

    project: Mapped[Optional["Project"]] = relationship(back_populates="activities")
