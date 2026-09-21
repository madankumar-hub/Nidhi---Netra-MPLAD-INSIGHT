"""Granting official roles by administrator approval.

The rule this enforces: a role is never self-assigned. Public sign-up always
creates a Citizen, and the only route to Officer or Auditor is an existing
Administrator approving a request, which leaves a row and an audit entry
naming who decided and when.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.enums import ACCESS_REQUESTABLE_ROLES, AccessRequestStatus, ActivityType, UserRole
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.database.base import utcnow
from app.models.access_request import AccessRequest
from app.models.user import User
from app.services import activity_service


def _open_request(db: Session, user_id: int) -> Optional[AccessRequest]:
    stmt = (
        select(AccessRequest)
        .where(
            AccessRequest.user_id == user_id,
            AccessRequest.status == AccessRequestStatus.PENDING,
        )
        .order_by(AccessRequest.created_at.desc())
    )
    return db.execute(stmt).scalars().first()


def create_request(
    db: Session,
    user: User,
    *,
    requested_role: UserRole,
    designation: Optional[str],
    department: Optional[str],
    district: Optional[str],
    employee_id: Optional[str],
    justification: str,
) -> AccessRequest:
    if requested_role not in ACCESS_REQUESTABLE_ROLES:
        raise ValidationError(
            "Only the Officer and Auditor roles can be requested. Administrator "
            "accounts are provisioned directly by an existing administrator.",
            code="role_not_requestable",
        )
    if user.role != UserRole.CITIZEN:
        raise ConflictError("This account already holds an official role.")
    if _open_request(db, user.id) is not None:
        raise ConflictError("You already have a request awaiting a decision.")

    allowlisted = settings.is_official_email(user.email)
    if settings.official_allowlist_enforced and not allowlisted:
        raise ValidationError(
            "Official access can only be requested from a recognised government "
            "email address. Contact the ministry administrator if your address "
            "should be added.",
            code="email_not_allowlisted",
        )

    request = AccessRequest(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        requested_role=requested_role,
        designation=designation,
        department=department,
        district=district,
        employee_id=employee_id,
        justification=justification,
        status=AccessRequestStatus.PENDING,
        email_allowlisted=allowlisted,
    )
    db.add(request)
    activity_service.log(
        db,
        project_id=None,
        activity_type=ActivityType.ACCESS_REQUESTED,
        summary=f"{user.full_name} requested {requested_role.value} access.",
        actor=user,
        detail=justification[:500],
        to_value=requested_role.value,
    )
    db.commit()
    db.refresh(request)
    return request


def list_requests(
    db: Session, status: Optional[AccessRequestStatus] = None, limit: int = 200
) -> List[AccessRequest]:
    stmt = select(AccessRequest)
    if status:
        stmt = stmt.where(AccessRequest.status == status)
    stmt = stmt.order_by(AccessRequest.created_at.desc()).limit(limit)
    return list(db.execute(stmt).scalars().all())


def list_for_user(db: Session, user_id: int) -> List[AccessRequest]:
    stmt = (
        select(AccessRequest)
        .where(AccessRequest.user_id == user_id)
        .order_by(AccessRequest.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get_or_404(db: Session, request_id: int) -> AccessRequest:
    request = db.get(AccessRequest, request_id)
    if request is None:
        raise NotFoundError(f"Access request {request_id} was not found.")
    return request


def approve(
    db: Session,
    request: AccessRequest,
    admin: User,
    *,
    granted_role: Optional[UserRole] = None,
    note: Optional[str] = None,
) -> AccessRequest:
    if request.status != AccessRequestStatus.PENDING:
        raise ConflictError("This request has already been decided.")

    role = granted_role or request.requested_role
    if role not in ACCESS_REQUESTABLE_ROLES:
        raise ValidationError(
            "Only the Officer and Auditor roles can be granted this way.",
            code="role_not_grantable",
        )

    user = db.get(User, request.user_id)
    if user is None:
        raise NotFoundError("The account behind this request no longer exists.")

    previous_role = user.role
    user.role = role
    user.designation = request.designation or user.designation
    user.department = request.department or user.department
    user.district = request.district or user.district

    request.status = AccessRequestStatus.APPROVED
    request.granted_role = role
    request.decided_at = utcnow()
    request.decided_by_id = admin.id
    request.decided_by_name = admin.full_name
    request.decision_note = note

    activity_service.log(
        db,
        project_id=None,
        activity_type=ActivityType.ACCESS_APPROVED,
        summary=f"{admin.full_name} granted {role.value} access to {user.full_name}.",
        actor=admin,
        detail=note,
        from_value=previous_role.value,
        to_value=role.value,
    )
    db.commit()
    db.refresh(request)
    return request


def reject(
    db: Session, request: AccessRequest, admin: User, *, note: Optional[str] = None
) -> AccessRequest:
    if request.status != AccessRequestStatus.PENDING:
        raise ConflictError("This request has already been decided.")

    request.status = AccessRequestStatus.REJECTED
    request.decided_at = utcnow()
    request.decided_by_id = admin.id
    request.decided_by_name = admin.full_name
    request.decision_note = note

    activity_service.log(
        db,
        project_id=None,
        activity_type=ActivityType.ACCESS_REJECTED,
        summary=f"{admin.full_name} declined the access request from {request.full_name}.",
        actor=admin,
        detail=note,
        to_value=AccessRequestStatus.REJECTED.value,
    )
    db.commit()
    db.refresh(request)
    return request


def revoke_role(db: Session, user: User, admin: User, *, note: Optional[str] = None) -> User:
    """Return an official account to the Citizen role."""
    if user.id == admin.id:
        raise ValidationError("You cannot revoke your own access.", code="self_revoke")
    if user.role == UserRole.ADMIN:
        raise ValidationError(
            "Administrator accounts cannot be revoked from this screen.",
            code="admin_not_revocable",
        )
    previous = user.role
    user.role = UserRole.CITIZEN
    activity_service.log(
        db,
        project_id=None,
        activity_type=ActivityType.ROLE_CHANGED,
        summary=f"{admin.full_name} revoked {previous.value} access from {user.full_name}.",
        actor=admin,
        detail=note,
        from_value=previous.value,
        to_value=UserRole.CITIZEN.value,
    )
    db.commit()
    db.refresh(user)
    return user


def allowlist_info() -> dict:
    return {
        "enforced": settings.official_allowlist_enforced,
        "domains": settings.official_domains,
        "explicit_addresses": len(settings.official_emails),
    }
