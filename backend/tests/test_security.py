"""Tests for password hashing and JWT issue / verification.

The JWT half runs anywhere PyJWT is installed. The password half needs
`bcrypt`; when it is absent (a bare interpreter with no requirements
installed) those checks report as skipped rather than failing.
"""
from __future__ import annotations

import time

from tests._bcrypt_stub import install_if_missing, is_stub

# Install a stand-in if the real library is absent, so the module under test
# can be imported and the JWT half still runs for real. Password checks detect
# the stand-in and report themselves as skipped rather than asserting on it.
install_if_missing()
BCRYPT_AVAILABLE = not is_stub()

from app.core.security import (  # noqa: E402
    TOKEN_TYPE_ACCESS,
    TOKEN_TYPE_REFRESH,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


# ---------------------------------------------------------------------------
# Passwords
# ---------------------------------------------------------------------------
def test_password_round_trip():
    if not BCRYPT_AVAILABLE:
        print("      (skipped - bcrypt not installed)")
        return
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple", "the password must not be stored in clear"
    assert hashed.startswith("$2"), "expected a bcrypt hash"
    assert verify_password("correct horse battery staple", hashed) is True
    assert verify_password("wrong password", hashed) is False


def test_same_password_hashes_differently_each_time():
    """Per-hash salting: two hashes of one password must not be equal."""
    if not BCRYPT_AVAILABLE:
        print("      (skipped - bcrypt not installed)")
        return
    assert hash_password("same input") != hash_password("same input")


def test_overlong_password_is_accepted():
    """bcrypt rejects inputs over 72 bytes, so they are truncated first."""
    if not BCRYPT_AVAILABLE:
        print("      (skipped - bcrypt not installed)")
        return
    long_password = "a" * 200
    hashed = hash_password(long_password)
    assert verify_password(long_password, hashed) is True


def test_malformed_hash_does_not_raise():
    if not BCRYPT_AVAILABLE:
        print("      (skipped - bcrypt not installed)")
        return
    assert verify_password("anything", "not-a-real-hash") is False
    assert verify_password("anything", "") is False


# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------
def test_access_token_round_trip():
    token = create_access_token("42", "auditor", "auditor@mplad.gov.in")
    assert isinstance(token, str)
    claims = decode_token(token)
    assert claims is not None
    assert claims["sub"] == "42"
    assert claims["type"] == TOKEN_TYPE_ACCESS
    assert claims["role"] == "auditor"
    assert claims["email"] == "auditor@mplad.gov.in"
    assert claims["exp"] > time.time()


def test_refresh_token_is_typed_separately():
    """A refresh token must be distinguishable from an access token, so it
    cannot be presented where an access token is required."""
    claims = decode_token(create_refresh_token("7"))
    assert claims is not None
    assert claims["type"] == TOKEN_TYPE_REFRESH
    assert "role" not in claims, "a refresh token should carry no role claim"


def test_tampered_token_is_rejected():
    token = create_access_token("1", "citizen", "citizen@example.com")
    header, payload, signature = token.split(".")

    # Flip a character in the signature.
    broken_signature = signature[:-1] + ("A" if signature[-1] != "A" else "B")
    assert decode_token(f"{header}.{payload}.{broken_signature}") is None

    # Re-encode the payload claiming the admin role, keeping the old signature.
    import base64
    import json

    decoded = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    decoded["role"] = "admin"
    forged = base64.urlsafe_b64encode(json.dumps(decoded).encode()).decode().rstrip("=")
    assert decode_token(f"{header}.{forged}.{signature}") is None


def test_garbage_token_is_rejected():
    for junk in ["", "not-a-token", "a.b.c", "Bearer something"]:
        assert decode_token(junk) is None


def test_expired_token_is_rejected():
    from app.core.security import _create_token

    expired = _create_token("1", TOKEN_TYPE_ACCESS, expires_minutes=-1)
    assert decode_token(expired) is None


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
    label = "security tests passed"
    if not BCRYPT_AVAILABLE:
        label += " (password checks skipped - bcrypt not installed)"
    print(f"\n{len(tests) - failures}/{len(tests)} {label}.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
