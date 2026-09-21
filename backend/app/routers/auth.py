"""Authentication and account endpoints (FR1, FR2)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import otp
from app.core.config import settings
from app.core.deps import get_current_user, require_admin
from app.core.rate_limit import (
    ACCESS_REQUEST_LIMIT,
    LOGIN_LIMIT,
    OTP_REQUEST_LIMIT,
    SIGNUP_LIMIT,
)
from app.core.rate_limit_deps import rate_limit
from app.core.enums import ACCESS_REQUESTABLE_ROLES
from app.core.exceptions import ConflictError, ValidationError
from app.core.security import (
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.database.base import utcnow
from app.database.session import get_db
from app.core.enums import UserRole
from app.models.user import User
from app.schemas.auth import (
    AccessPolicyInfo,
    AccessRequestCreate,
    AccessRequestOut,
    CitizenSignupComplete,
    CitizenSignupStart,
    LoginRequest,
    OfficialCreate,
    OtpRequested,
    PasswordChange,
    RefreshRequest,
    TokenResponse,
    UserPublic,
)
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _issue_tokens(db: Session, user: User) -> TokenResponse:
    user.last_login_at = utcnow()
    db.commit()
    db.refresh(user)
    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role.value, user.email),
        refresh_token=create_refresh_token(str(user.id)),
        expires_in_minutes=settings.access_token_expire_minutes,
        user=UserPublic.model_validate(user, from_attributes=True),
    )


def _get_user_by_email(db: Session, email: str) -> User | None:
    return db.execute(select(User).where(User.email == email.lower().strip())).scalars().first()


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit(LOGIN_LIMIT, "login"))],
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = _get_user_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        # Deliberately identical message for unknown email and wrong password.
        raise ValidationError("Invalid email address or password.", status_code=401, code="invalid_credentials")
    if not user.is_active:
        raise ValidationError("This account has been deactivated.", status_code=403, code="account_disabled")
    return _issue_tokens(db, user)


@router.post(
    "/signup/request-otp",
    response_model=OtpRequested,
    dependencies=[Depends(rate_limit(OTP_REQUEST_LIMIT, "signup-otp"))],
)
def request_signup_otp(payload: CitizenSignupStart, db: Session = Depends(get_db)) -> OtpRequested:
    """Step 1 of lightweight citizen signup (FR1). No KYC, email + OTP only."""
    if not settings.otp_enabled:
        raise ValidationError("OTP signup is disabled on this deployment.")
    if _get_user_by_email(db, payload.email) is not None:
        raise ConflictError("An account already exists for this email address.")
    code = otp.generate_otp(db, payload.email, purpose="signup")
    return OtpRequested(
        message="A verification code has been sent to your email address.",
        email=payload.email,
        expires_in_minutes=settings.otp_expiry_minutes,
        dev_otp=code if otp.is_dev_delivery() else None,
    )


@router.post(
    "/signup/verify",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(SIGNUP_LIMIT, "signup-verify"))],
)
def complete_signup(payload: CitizenSignupComplete, db: Session = Depends(get_db)) -> TokenResponse:
    """Step 2 of citizen signup: verify the OTP and create the account."""
    if _get_user_by_email(db, payload.email) is not None:
        raise ConflictError("An account already exists for this email address.")
    otp.verify_otp(db, payload.email, payload.otp, purpose="signup")

    user = User(
        email=payload.email.lower().strip(),
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role=UserRole.CITIZEN,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_tokens(db, user)


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    claims = decode_token(payload.refresh_token)
    if claims is None or claims.get("type") != TOKEN_TYPE_REFRESH:
        raise ValidationError("Invalid or expired refresh token.", status_code=401, code="invalid_token")
    user = db.get(User, int(claims.get("sub", 0) or 0))
    if user is None or not user.is_active:
        raise ValidationError("Account not found or deactivated.", status_code=401, code="invalid_token")
    return _issue_tokens(db, user)


@router.post("/logout", response_model=MessageResponse)
def logout(current_user: User = Depends(get_current_user)) -> MessageResponse:
    """Tokens are stateless; the client discards them. Recorded for audit clarity."""
    return MessageResponse(message="Signed out successfully.")


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic.model_validate(current_user, from_attributes=True)


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    if not verify_password(payload.current_password, current_user.password_hash):
        raise ValidationError("The current password is incorrect.")
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return MessageResponse(message="Password updated successfully.")


# ---------------------------------------------------------------------------
# Official access: requested by the user, granted only by an administrator
# ---------------------------------------------------------------------------
@router.get("/access-policy", response_model=AccessPolicyInfo)
def access_policy() -> AccessPolicyInfo:
    """Public: what the sign-in screen tells people about official access."""
    from app.services import access_request_service

    return AccessPolicyInfo(**access_request_service.allowlist_info())


@router.post(
    "/request-official-access",
    response_model=AccessRequestOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit(ACCESS_REQUEST_LIMIT, "access-request"))],
)
def request_official_access(
    payload: AccessRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AccessRequestOut:
    """Ask to be granted the Officer or Auditor role.

    This only creates a request. The role is not changed until an existing
    administrator approves it - there is no code path by which a user can
    raise their own privileges.
    """
    from app.services import access_request_service

    request = access_request_service.create_request(
        db,
        current_user,
        requested_role=payload.requested_role,
        designation=payload.designation,
        department=payload.department,
        district=payload.district,
        employee_id=payload.employee_id,
        justification=payload.justification,
    )
    return AccessRequestOut.model_validate(request, from_attributes=True)


@router.get("/my-access-requests", response_model=list[AccessRequestOut])
def my_access_requests(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[AccessRequestOut]:
    from app.services import access_request_service

    return [
        AccessRequestOut.model_validate(item, from_attributes=True)
        for item in access_request_service.list_for_user(db, current_user.id)
    ]


@router.get("/requestable-roles", response_model=list[UserRole])
def requestable_roles() -> list[UserRole]:
    """Administrator is deliberately absent from this list."""
    return sorted(ACCESS_REQUESTABLE_ROLES, key=lambda role: role.value)


@router.post("/officials", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def create_official(
    payload: OfficialCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserPublic:
    """Administrator-only provisioning of Officer / Auditor / Admin accounts."""
    if _get_user_by_email(db, payload.email) is not None:
        raise ConflictError("An account already exists for this email address.")
    user = User(
        email=payload.email.lower().strip(),
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role=payload.role,
        designation=payload.designation,
        department=payload.department,
        district=payload.district,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserPublic.model_validate(user, from_attributes=True)


@router.get("/officials", response_model=list[UserPublic])
def list_officials(
    current_user: User = Depends(require_admin), db: Session = Depends(get_db)
) -> list[UserPublic]:
    users = db.execute(select(User).order_by(User.created_at.desc())).scalars().all()
    return [UserPublic.model_validate(u, from_attributes=True) for u in users]
