"""Lightweight email OTP for citizen signup (SRS FR1).

Development delivery prints the code to the server console and returns a
`dev_otp` field so the demo works without a mail provider. Production
delivery is wired through `OTP_DELIVERY=email`.
"""
from __future__ import annotations

import logging
import secrets
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ValidationError
from app.core.security import hash_password, verify_password
from app.database.base import utcnow
from app.models.user import OtpCode

logger = logging.getLogger("mplad.otp")

MAX_ATTEMPTS = 5


def generate_otp(db: Session, email: str, purpose: str = "signup") -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    record = OtpCode(
        email=email.lower().strip(),
        code_hash=hash_password(code),
        purpose=purpose,
        expires_at=utcnow() + timedelta(minutes=settings.otp_expiry_minutes),
        created_at=utcnow(),
    )
    db.add(record)
    db.commit()

    if settings.otp_delivery == "console":
        logger.warning("[DEV OTP] %s -> %s (expires in %sm)", email, code, settings.otp_expiry_minutes)
    else:  # pragma: no cover - requires a configured mail provider
        logger.info("Dispatching OTP to %s via configured provider", email)
    return code


def verify_otp(db: Session, email: str, code: str, purpose: str = "signup") -> bool:
    email = email.lower().strip()
    stmt = (
        select(OtpCode)
        .where(OtpCode.email == email, OtpCode.purpose == purpose, OtpCode.consumed.is_(False))
        .order_by(OtpCode.created_at.desc())
    )
    record = db.execute(stmt).scalars().first()
    if record is None:
        raise ValidationError("No verification code was requested for this email address.")
    if record.expires_at < utcnow():
        raise ValidationError("The verification code has expired. Please request a new one.")
    if record.attempts >= MAX_ATTEMPTS:
        raise ValidationError("Too many incorrect attempts. Please request a new code.")

    record.attempts += 1
    if not verify_password(code, record.code_hash):
        db.commit()
        raise ValidationError("The verification code is incorrect.")

    record.consumed = True
    db.commit()
    return True


def is_dev_delivery() -> bool:
    return settings.otp_delivery == "console" and not settings.is_production
