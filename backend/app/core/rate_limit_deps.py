"""FastAPI wiring for the rate limiter.

Why this is a separate module
-----------------------------
`rate_limit.py` holds the counting logic and imports no web framework, so it can
be unit-tested in an environment with nothing installed.

The dependency below must do the opposite: it needs a REAL, runtime-resolvable
`Request` annotation. FastAPI inspects the signature at import time to decide
what each parameter is. An annotation it cannot resolve to a class - a string
left behind by `from __future__ import annotations`, or a name imported only
under `TYPE_CHECKING` - is not recognised as the Starlette request, and FastAPI
falls back to treating the parameter as an ordinary required query parameter.
Every guarded endpoint then rejects valid input with "Request is required".

So: no `from __future__ import annotations` in this file, and `Request` is
imported for real. `tests/test_rate_limit.py` asserts both.
"""
from fastapi import HTTPException, Request, status

from app.core.rate_limit import RateLimit, check


def rate_limit(limit: RateLimit, scope: str):
    """Build a dependency that enforces `limit` for `scope`.

    Usage:
        @router.post(
            "/login",
            dependencies=[Depends(rate_limit(LOGIN_LIMIT, "login"))],
        )
    """

    def dependency(request: Request) -> None:
        allowed, retry_after = check(request, limit, scope)
        if allowed:
            return

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Too many attempts. Please wait "
                f"{retry_after} second{'s' if retry_after != 1 else ''} and try again."
            ),
            headers={"Retry-After": str(retry_after)},
        )

    return dependency
