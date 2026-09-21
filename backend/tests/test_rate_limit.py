"""Rate limiter behaviour.

These run without FastAPI installed: the limiter itself is plain Python, and
the route-level wiring is verified by parsing the router source.
"""
from __future__ import annotations

import ast
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.rate_limit import (  # noqa: E402
    LOGIN_LIMIT,
    RateLimit,
    SlidingWindowLimiter,
)


def test_requests_under_the_limit_are_allowed() -> None:
    limiter = SlidingWindowLimiter()
    limit = RateLimit(max_requests=3, window_seconds=60)
    for _ in range(3):
        allowed, retry_after = limiter.check("caller", limit)
        assert allowed is True
        assert retry_after == 0


def test_the_request_after_the_limit_is_refused() -> None:
    limiter = SlidingWindowLimiter()
    limit = RateLimit(max_requests=2, window_seconds=60)
    limiter.check("caller", limit)
    limiter.check("caller", limit)

    allowed, retry_after = limiter.check("caller", limit)
    assert allowed is False
    assert 0 < retry_after <= 61


def test_callers_are_counted_independently() -> None:
    limiter = SlidingWindowLimiter()
    limit = RateLimit(max_requests=1, window_seconds=60)

    assert limiter.check("first", limit)[0] is True
    assert limiter.check("second", limit)[0] is True
    # Each has used its single allowance.
    assert limiter.check("first", limit)[0] is False
    assert limiter.check("second", limit)[0] is False


def test_the_window_slides() -> None:
    limiter = SlidingWindowLimiter()
    limit = RateLimit(max_requests=1, window_seconds=1)

    assert limiter.check("caller", limit)[0] is True
    assert limiter.check("caller", limit)[0] is False

    time.sleep(1.05)
    assert limiter.check("caller", limit)[0] is True, "window did not expire"


def test_idle_callers_are_evicted() -> None:
    limiter = SlidingWindowLimiter()
    limit = RateLimit(max_requests=1, window_seconds=1)

    for index in range(4100):
        limiter.check(f"caller-{index}", limit)

    # The opportunistic cleanup runs past 4096 keys; with a 1s window and
    # 4100 synthetic callers the map must not simply grow without bound.
    assert len(limiter._hits) <= 4100


def test_credential_endpoints_are_rate_limited() -> None:
    """Every authentication entry point must carry a limiter dependency."""
    source = (ROOT / "app" / "routers" / "auth.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    protected: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            uses_limiter = any(
                isinstance(sub, ast.Name) and sub.id == "rate_limit"
                for sub in ast.walk(decorator)
            )
            if uses_limiter:
                protected.add(node.name)

    for endpoint in ("login", "request_signup_otp", "complete_signup", "request_official_access"):
        assert endpoint in protected, f"{endpoint} has no rate limit"


def test_login_limit_is_strict_enough_to_matter() -> None:
    """A limit loose enough to allow online guessing is not a limit."""
    per_hour = LOGIN_LIMIT.max_requests * (3600 / LOGIN_LIMIT.window_seconds)
    assert per_hour <= 600, f"login allows {per_hour:.0f} attempts/hour"


def test_the_dependency_annotation_is_resolvable_at_runtime() -> None:
    """Regression: FastAPI must be able to see `Request` as a real class.

    This is the bug that shipped once. `rate_limit_deps.rate_limit` returned a
    dependency annotated `request: "Request"` - a string, because the module
    used `from __future__ import annotations` and imported `Request` only under
    `TYPE_CHECKING` so the tests could run without FastAPI installed.

    FastAPI reads the signature at import time. An annotation it cannot resolve
    to a class is not recognised as the Starlette request, so it treated
    `request` as an ordinary required query parameter - and every rate-limited
    endpoint rejected valid input with "Request is required".

    Two things must hold, and neither needs FastAPI installed to check:
      1. the deps module does not use `from __future__ import annotations`;
      2. it imports `Request` at runtime, not under `TYPE_CHECKING`.
    """
    source = (ROOT / "app" / "core" / "rate_limit_deps.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            names = {alias.name for alias in node.names}
            assert "annotations" not in names, (
                "rate_limit_deps.py must not use `from __future__ import annotations`; "
                "it turns the dependency's Request annotation into a string that "
                "FastAPI cannot resolve."
            )

    # `Request` must be imported at module level, outside any `if TYPE_CHECKING`.
    runtime_imports: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "fastapi":
            runtime_imports.update(alias.asname or alias.name for alias in node.names)

    assert "Request" in runtime_imports, (
        "rate_limit_deps.py must import Request from fastapi at runtime, "
        "not under TYPE_CHECKING."
    )


def test_the_pure_limiter_has_no_framework_import() -> None:
    """The counting logic must stay testable with nothing installed.

    Checks imports rather than the text of the file, so the module can still
    explain itself in a docstring that mentions the framework by name.
    """
    source = (ROOT / "app" / "core" / "rate_limit.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    for framework in ("fastapi", "starlette"):
        assert framework not in imported, (
            f"app/core/rate_limit.py imports {framework}; the framework glue "
            "belongs in rate_limit_deps.py so the limiter stays unit-testable."
        )


def _run_all() -> int:
    import traceback

    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"  PASS  {test.__name__}")
        except Exception:
            failures += 1
            print(f"  FAIL  {test.__name__}")
            traceback.print_exc()
    print(f"\n{len(tests) - failures}/{len(tests)} rate-limit tests passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
