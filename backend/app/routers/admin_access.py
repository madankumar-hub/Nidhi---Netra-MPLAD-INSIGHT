"""Administrator review of official-access requests, and user administration.

Every route here is Administrator-only. This is the screen that answers
"how does someone become an officer?" - by an existing administrator deciding,
on the record.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_admin
from app.core.enums import AccessRequestStatus, UserRole
from app.core.exceptions import NotFoundError
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import (
    AccessPolicyInfo,
    AccessRequestDecision,
    AccessRequestOut,
    RoleRevoke,
    UserPublic,
)
from app.services import access_request_service

router = APIRouter(prefix="/admin", tags=["Admin - Access control"])


@router.get("/access-requests", response_model=List[AccessRequestOut])
def list_access_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    request_status: Optional[AccessRequestStatus] = Query(default=None, alias="status"),
) -> List[AccessRequestOut]:
    return [
        AccessRequestOut.model_validate(item, from_attributes=True)
        for item in access_request_service.list_requests(db, request_status)
    ]


@router.get("/access-policy", response_model=AccessPolicyInfo)
def access_policy(current_user: User = Depends(require_admin)) -> AccessPolicyInfo:
    return AccessPolicyInfo(**access_request_service.allowlist_info())


@router.post("/access-requests/{request_id}/decide", response_model=AccessRequestOut)
def decide_access_request(
    request_id: int,
    payload: AccessRequestDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> AccessRequestOut:
    """Approve (granting the role) or decline. Either way it is audited."""
    request = access_request_service.get_or_404(db, request_id)
    if payload.approve:
        request = access_request_service.approve(
            db, request, current_user, granted_role=payload.granted_role, note=payload.note
        )
    else:
        request = access_request_service.reject(db, request, current_user, note=payload.note)
    return AccessRequestOut.model_validate(request, from_attributes=True)


@router.get("/users", response_model=List[UserPublic])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    role: Optional[UserRole] = None,
) -> List[UserPublic]:
    stmt = select(User)
    if role:
        stmt = stmt.where(User.role == role)
    stmt = stmt.order_by(User.created_at.desc())
    return [
        UserPublic.model_validate(user, from_attributes=True)
        for user in db.execute(stmt).scalars().all()
    ]


@router.post("/users/{user_id}/revoke", response_model=UserPublic)
def revoke_official_role(
    user_id: int,
    payload: RoleRevoke,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> UserPublic:
    """Return an official account to the Citizen role."""
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError(f"User {user_id} was not found.")
    user = access_request_service.revoke_role(db, user, current_user, note=payload.note)
    return UserPublic.model_validate(user, from_attributes=True)
