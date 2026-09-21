"""Role-based access control helpers.

The role is ALWAYS re-read from the database inside `get_current_user`;
the `role` claim in the JWT is treated as a hint for the UI only.
"""
from __future__ import annotations

from typing import Iterable, Set

from app.core.exceptions import PermissionDeniedError
from app.core.enums import UserRole
from app.models.user import User


class RequireRoles:
    """FastAPI dependency factory enforcing a role allow-list."""

    def __init__(self, *roles: UserRole):
        self.allowed: Set[UserRole] = set(roles)

    def __call__(self, current_user: User) -> User:  # pragma: no cover - wired in deps
        if current_user.role not in self.allowed:
            raise PermissionDeniedError(
                "Your role does not have permission to access this resource.",
                code="insufficient_role",
            )
        return current_user


def assert_role(user: User, allowed: Iterable[UserRole], *, action: str = "perform this action") -> None:
    if user.role not in set(allowed):
        raise PermissionDeniedError(
            f"Role '{user.role.value}' is not permitted to {action}.",
            code="insufficient_role",
        )
