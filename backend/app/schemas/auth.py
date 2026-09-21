from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.enums import AccessRequestStatus, UserRole


class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    designation: Optional[str] = None
    department: Optional[str] = None
    district: Optional[str] = None
    is_active: bool
    is_verified: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserPublic


class RefreshRequest(BaseModel):
    refresh_token: str


class CitizenSignupStart(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=160)


class OtpRequested(BaseModel):
    message: str
    email: EmailStr
    expires_in_minutes: int
    #: Present ONLY in non-production console-delivery mode so the demo works
    #: without a mail provider. Never returned when ENVIRONMENT=production.
    dev_otp: Optional[str] = None


class CitizenSignupComplete(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=160)
    otp: str = Field(min_length=4, max_length=8)
    password: str = Field(min_length=8, max_length=128)


class OfficialCreate(BaseModel):
    """Admin-only creation of Officer / Auditor / Admin accounts (FR2)."""

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
    designation: Optional[str] = Field(default=None, max_length=160)
    department: Optional[str] = Field(default=None, max_length=160)
    district: Optional[str] = Field(default=None, max_length=120)


class AccessRequestCreate(BaseModel):
    """A signed-in citizen asking to be granted an official role."""

    requested_role: UserRole
    designation: Optional[str] = Field(default=None, max_length=160)
    department: Optional[str] = Field(default=None, max_length=160)
    district: Optional[str] = Field(default=None, max_length=120)
    employee_id: Optional[str] = Field(default=None, max_length=80)
    justification: str = Field(min_length=20, max_length=2000)


class AccessRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    email: EmailStr
    full_name: str
    requested_role: UserRole
    designation: Optional[str] = None
    department: Optional[str] = None
    district: Optional[str] = None
    employee_id: Optional[str] = None
    justification: str
    status: AccessRequestStatus
    email_allowlisted: bool
    decided_at: Optional[datetime] = None
    decided_by_name: Optional[str] = None
    decision_note: Optional[str] = None
    granted_role: Optional[UserRole] = None
    created_at: datetime


class AccessRequestDecision(BaseModel):
    approve: bool
    #: Optional override - an administrator may grant Officer where Auditor
    #: was asked for, or the reverse.
    granted_role: Optional[UserRole] = None
    note: Optional[str] = Field(default=None, max_length=2000)


class AccessPolicyInfo(BaseModel):
    """What the sign-in and request screens tell the user up front."""

    enforced: bool
    domains: list[str] = Field(default_factory=list)
    explicit_addresses: int = 0


class RoleRevoke(BaseModel):
    note: Optional[str] = Field(default=None, max_length=2000)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
