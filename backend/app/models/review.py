from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.core.enums import ReviewStatus


class Review(Base, TimestampMixin):
    """Persisted administrative review of a project (FR13)."""

    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    reviewer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reviewer_name: Mapped[str] = mapped_column(String(160), nullable=False)
    reviewer_role: Mapped[str] = mapped_column(String(32), nullable=False)

    review_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    previous_status: Mapped[Optional[ReviewStatus]] = mapped_column(
        SAEnum(ReviewStatus, native_enum=False, length=32)
    )
    status: Mapped[ReviewStatus] = mapped_column(
        SAEnum(ReviewStatus, native_enum=False, length=32), nullable=False
    )
    findings: Mapped[str] = mapped_column(Text, nullable=False, default="")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    action_required: Mapped[Optional[str]] = mapped_column(Text)
    escalated_to: Mapped[Optional[str]] = mapped_column(String(160))
    follow_up_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    project: Mapped["Project"] = relationship(back_populates="reviews")
    reviewer: Mapped[Optional["User"]] = relationship(back_populates="reviews")
