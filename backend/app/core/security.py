"""Password hashing and JWT creation / verification.

Uses `bcrypt` and `PyJWT` directly rather than the `passlib` / `python-jose`
wrappers. Both of those are unmaintained and break against current releases of
`cryptography`, and passlib additionally fails to read the version of modern
bcrypt builds. Calling the two libraries directly is fewer moving parts and
keeps the project installable on every current Python version.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
import jwt
from jwt import InvalidTokenError

from app.core.config import settings

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"

#: bcrypt refuses inputs longer than this, so passwords are truncated first.
BCRYPT_MAX_BYTES = 72


def _prepare(raw_password: str) -> bytes:
    return raw_password.encode("utf-8")[:BCRYPT_MAX_BYTES]


def hash_password(raw_password: str) -> str:
    return bcrypt.hashpw(_prepare(raw_password), bcrypt.gensalt()).decode("utf-8")


def verify_password(raw_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_prepare(raw_password), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        # Malformed or truncated hash in the database - treat as a failed match
        # rather than surfacing a 500 to the caller.
        return False


def _create_token(
    subject: str,
    token_type: str,
    expires_minutes: int,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    now = datetime.now(tz=timezone.utc)
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    # PyJWT 1.x returned bytes; 2.x returns str. Normalise defensively.
    return token.decode("utf-8") if isinstance(token, bytes) else token


def create_access_token(subject: str, role: str, email: str) -> str:
    return _create_token(
        subject,
        TOKEN_TYPE_ACCESS,
        settings.access_token_expire_minutes,
        # `role` is a convenience claim only. The API NEVER trusts it for
        # authorization - the role is always re-read from the database.
        {"role": role, "email": email},
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(subject, TOKEN_TYPE_REFRESH, settings.refresh_token_expire_minutes)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Returns the claims, or None when the token is invalid or expired."""
    try:
        return jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except InvalidTokenError:
        return None
