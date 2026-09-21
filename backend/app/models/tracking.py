"""Fund and physical-progress update trails."""
from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import Date, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class FundUpdate(Base, TimestampMixin):
    __tablename__ = "fund_updates"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    updated_on: Mapped[date] = mapped_column(Date, nullable=False)
    installment_no: Mapped[Optional[int]]
    released_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    expenditure_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cumulative_spent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    voucher_reference: Mapped[Optional[str]] = mapped_column(String(80))
    remarks: Mapped[Optional[str]] = mapped_column(Text)
    recorded_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    project: Mapped["Project"] = relationship(back_populates="fund_updates")


class ProgressUpdate(Base, TimestampMixin):
    __tablename__ = "progress_updates"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    updated_on: Mapped[date] = mapped_column(Date, nullable=False)
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    planned_progress_percent: Mapped[Optional[float]] = mapped_column(Float)
    milestone: Mapped[Optional[str]] = mapped_column(String(200))
    remarks: Mapped[Optional[str]] = mapped_column(Text)
    recorded_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))

    project: Mapped["Project"] = relationship(back_populates="progress_updates")
