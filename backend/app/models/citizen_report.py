from __future__ import annotations

from typing import Optional

from sqlalchemy import Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.core.enums import CitizenReportCategory, CitizenReportStatus


class CitizenReport(Base, TimestampMixin):
    """FR7 - community feedback / report filed by a logged-in citizen."""

    __tablename__ = "citizen_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    reporter_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reporter_name: Mapped[str] = mapped_column(String(160), default="Citizen", nullable=False)

    category: Mapped[CitizenReportCategory] = mapped_column(
        SAEnum(CitizenReportCategory, native_enum=False, length=48), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[CitizenReportStatus] = mapped_column(
        SAEnum(CitizenReportStatus, native_enum=False, length=24),
        default=CitizenReportStatus.SUBMITTED,
        nullable=False,
        index=True,
    )
    official_response: Mapped[Optional[str]] = mapped_column(Text)

    project: Mapped["Project"] = relationship(back_populates="citizen_reports")
