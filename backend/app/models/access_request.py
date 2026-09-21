from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum as SAEnum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import AccessRequestStatus, UserRole
from app.database.base import Base, TimestampMixin


class AccessRequest(Base, TimestampMixin):
    """A signed-in citizen asking to be granted an official role.

    Nobody can self-assign a role. Public sign-up always produces a Citizen;
    elevation happens only when an existing Administrator approves one of these
    rows, which is recorded with who decided, when, and why.
    """

    __tablename__ = "access_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)

    requested_role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, native_enum=False, length=32), nullable=False
    )
    designation: Mapped[Optional[str]] = mapped_column(String(160))
    department: Mapped[Optional[str]] = mapped_column(String(160))
    district: Mapped[Optional[str]] = mapped_column(String(120))
    employee_id: Mapped[Optional[str]] = mapped_column(String(80))
    justification: Mapped[str] = mapped_column(Text, nullable=False, default="")

    status: Mapped[AccessRequestStatus] = mapped_column(
        SAEnum(AccessRequestStatus, native_enum=False, length=24),
        default=AccessRequestStatus.PENDING,
        nullable=False,
        index=True,
    )
    #: True when the address matched the configured official allowlist.
    email_allowlisted: Mapped[bool] = mapped_column(default=False, nullable=False)

    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    decided_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    decided_by_name: Mapped[Optional[str]] = mapped_column(String(160))
    decision_note: Mapped[Optional[str]] = mapped_column(Text)
    granted_role: Mapped[Optional[UserRole]] = mapped_column(
        SAEnum(UserRole, native_enum=False, length=32)
    )
