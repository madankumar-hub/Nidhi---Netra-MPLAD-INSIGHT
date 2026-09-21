from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.core.enums import UserRole


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, native_enum=False, length=32), nullable=False, default=UserRole.CITIZEN
    )
    designation: Mapped[Optional[str]] = mapped_column(String(160))
    department: Mapped[Optional[str]] = mapped_column(String(160))
    district: Mapped[Optional[str]] = mapped_column(String(120))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    reviews: Mapped[List["Review"]] = relationship(back_populates="reviewer")
    notes: Mapped[List["Note"]] = relationship(back_populates="author")

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<User {self.email} ({self.role})>"


class OtpCode(Base):
    """Lightweight email-OTP verification for citizen signup (FR1)."""

    __tablename__ = "otp_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(String(32), default="signup", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
