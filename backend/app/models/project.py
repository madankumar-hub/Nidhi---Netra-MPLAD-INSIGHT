from __future__ import annotations

from datetime import date
from typing import List, Optional

from sqlalchemy import Date, Enum as SAEnum, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.core.enums import ProjectStatus, ReviewStatus


class Project(Base, TimestampMixin):
    """Core MPLAD work record (SRS section 7 - Project entity)."""

    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_district_category", "district", "category"),
        Index("ix_projects_status_year", "status", "sanction_year"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    project_code: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    mp_name: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    constituency: Mapped[Optional[str]] = mapped_column(String(160))
    house: Mapped[str] = mapped_column(String(32), default="Lok Sabha", nullable=False)
    state: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    block: Mapped[Optional[str]] = mapped_column(String(160))
    location: Mapped[Optional[str]] = mapped_column(String(240))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)

    category: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    executing_agency: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    contractor: Mapped[Optional[str]] = mapped_column(String(200))

    sanction_year: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    sanction_date: Mapped[Optional[date]] = mapped_column(Date)
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    planned_end_date: Mapped[Optional[date]] = mapped_column(Date)
    actual_end_date: Mapped[Optional[date]] = mapped_column(Date)

    allocated_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    spent_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    estimated_cost: Mapped[Optional[float]] = mapped_column(Float)

    progress_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    planned_progress_percent: Mapped[Optional[float]] = mapped_column(Float)

    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus, native_enum=False, length=32),
        default=ProjectStatus.NOT_STARTED,
        nullable=False,
        index=True,
    )
    review_status: Mapped[ReviewStatus] = mapped_column(
        SAEnum(ReviewStatus, native_enum=False, length=32),
        default=ReviewStatus.PENDING_REVIEW,
        nullable=False,
        index=True,
    )

    beneficiaries: Mapped[Optional[int]] = mapped_column(Integer)
    photo_url: Mapped[Optional[str]] = mapped_column(String(400))
    document_url: Mapped[Optional[str]] = mapped_column(String(400))
    remarks: Mapped[Optional[str]] = mapped_column(Text)

    fund_updates: Mapped[List["FundUpdate"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="FundUpdate.updated_on"
    )
    progress_updates: Mapped[List["ProgressUpdate"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="ProgressUpdate.updated_on"
    )
    reviews: Mapped[List["Review"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="Review.review_date.desc()"
    )
    notes: Mapped[List["Note"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="Note.created_at.desc()"
    )
    risk_assessments: Mapped[List["RiskAssessment"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="RiskAssessment.assessed_at.desc()",
    )
    activities: Mapped[List["ActivityLog"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ActivityLog.created_at.desc()",
    )
    citizen_reports: Mapped[List["CitizenReport"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )

    # --- Derived helpers --------------------------------------------------
    @property
    def remaining_amount(self) -> float:
        return round(max(self.allocated_amount - self.spent_amount, 0.0), 2)

    @property
    def utilization_percent(self) -> float:
        if not self.allocated_amount:
            return 0.0
        return round(min(self.spent_amount / self.allocated_amount * 100.0, 999.0), 2)

    @property
    def latest_risk(self) -> Optional["RiskAssessment"]:
        return self.risk_assessments[0] if self.risk_assessments else None
