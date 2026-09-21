"""Shared FastAPI dependencies: DB session, current user, role guards."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import AppError, PermissionDeniedError
from app.core.security import TOKEN_TYPE_ACCESS, decode_token
from app.database.session import get_db
from app.core.enums import ELEVATED_ROLES, INTERNAL_ROLES, REVIEWER_ROLES, UserRole
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)
optional_bearer_scheme = HTTPBearer(auto_error=False)


class UnauthenticatedError(AppError):
    status_code = 401
    code = "unauthenticated"


def _user_from_token(db: Session, token: str) -> User:
    payload = decode_token(token)
    if payload is None or payload.get("type") != TOKEN_TYPE_ACCESS:
        raise UnauthenticatedError("Invalid or expired access token.")
    try:
        user_id = int(payload.get("sub", ""))
    except (TypeError, ValueError):
        raise UnauthenticatedError("Malformed access token.")

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise UnauthenticatedError("Account not found or deactivated.")
    return user


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise UnauthenticatedError("Authentication required.")
    return _user_from_token(db, credentials.credentials)


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    if credentials is None or not credentials.credentials:
        return None
    try:
        return _user_from_token(db, credentials.credentials)
    except UnauthenticatedError:
        return None


def require_internal(current_user: User = Depends(get_current_user)) -> User:
    """Officer / Auditor / Admin. Blocks the Citizen role from every
    internal endpoint (risk scores, notes, audit trail, mitigation)."""
    if current_user.role not in INTERNAL_ROLES:
        raise PermissionDeniedError(
            "This resource is restricted to authorised officials.",
            code="internal_only",
        )
    return current_user


def require_reviewer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in REVIEWER_ROLES:
        raise PermissionDeniedError(
            "Only Officers, Auditors and Administrators may perform review actions.",
            code="reviewer_only",
        )
    return current_user


def require_elevated(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in ELEVATED_ROLES:
        raise PermissionDeniedError(
            "This action requires Auditor or Administrator privileges.",
            code="elevated_only",
        )
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise PermissionDeniedError("Administrator privileges required.", code="admin_only")
    return current_user
