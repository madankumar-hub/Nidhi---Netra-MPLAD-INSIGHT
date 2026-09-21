"""Tests for how an account can - and cannot - become an official one.

The rule being protected: a role is never self-assigned. Public sign-up always
produces a Citizen, Administrator can never be requested, and elevation happens
only through an administrator's decision.
"""
from __future__ import annotations

from tests._bcrypt_stub import install_if_missing as install_bcrypt_stub
from tests._email_validator_stub import install_if_missing as install_email_stub

install_bcrypt_stub()
install_email_stub()

from app.core.config import Settings  # noqa: E402
from app.core.enums import ACCESS_REQUESTABLE_ROLES, ELEVATED_ROLES, INTERNAL_ROLES, UserRole  # noqa: E402


# ---------------------------------------------------------------------------
# What may be requested
# ---------------------------------------------------------------------------
def test_administrator_can_never_be_requested():
    """The one that matters: no self-service route to Administrator."""
    assert UserRole.ADMIN not in ACCESS_REQUESTABLE_ROLES
    assert UserRole.CITIZEN not in ACCESS_REQUESTABLE_ROLES
    assert ACCESS_REQUESTABLE_ROLES == {UserRole.OFFICER, UserRole.AUDITOR}


def test_public_signup_hardcodes_the_citizen_role():
    """The sign-up handler must not read a role from the request body.

    Read as source rather than imported, so this check runs in a bare
    interpreter with no web framework installed.
    """
    import ast
    from pathlib import Path

    tree = ast.parse(Path("app/routers/auth.py").read_text(encoding="utf-8"))
    handler = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "complete_signup"
    )
    source = ast.unparse(handler)
    assert "role=UserRole.CITIZEN" in source, "sign-up must pin the Citizen role"
    assert "payload.role" not in source, "sign-up must never take a role from the caller"

    # The request schema itself must not even carry a role field.
    schema_tree = ast.parse(Path("app/schemas/auth.py").read_text(encoding="utf-8"))
    schema = next(
        node
        for node in ast.walk(schema_tree)
        if isinstance(node, ast.ClassDef) and node.name == "CitizenSignupComplete"
    )
    fields = {
        stmt.target.id
        for stmt in schema.body
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
    }
    assert "role" not in fields, "the sign-up schema must not accept a role"


def test_role_sets_are_consistent():
    assert UserRole.CITIZEN not in INTERNAL_ROLES
    assert ACCESS_REQUESTABLE_ROLES <= INTERNAL_ROLES
    assert UserRole.ADMIN in ELEVATED_ROLES


# ---------------------------------------------------------------------------
# The email allowlist
# ---------------------------------------------------------------------------
def _settings(**overrides) -> Settings:
    base = {
        "official_email_allowlist": "",
        "official_email_domains": "gov.in,nic.in",
        "official_allowlist_enforced": True,
    }
    base.update(overrides)
    return Settings(**base)


def test_government_domains_match():
    s = _settings()
    for address in [
        "officer@gov.in",
        "auditor@mplad.gov.in",
        "someone@dept.nic.in",
        "UPPER@GOV.IN",
    ]:
        assert s.is_official_email(address) is True, address


def test_non_government_domains_do_not_match():
    s = _settings()
    for address in [
        "someone@gmail.com",
        "attacker@notgov.in",          # must not match by suffix alone
        "person@gov.in.evil.com",
        "",
    ]:
        assert s.is_official_email(address) is False, address


def test_explicit_addresses_are_honoured():
    s = _settings(official_email_allowlist="named.person@example.org, other@example.org")
    assert s.is_official_email("named.person@example.org") is True
    assert s.is_official_email("Other@Example.org") is True
    assert s.is_official_email("stranger@example.org") is False


def test_blank_configuration_defers_to_the_administrator():
    """With nothing configured, every address may *ask* - and an administrator
    still has to approve. The allowlist narrows who can ask; it never grants."""
    s = _settings(official_email_allowlist="", official_email_domains="")
    assert s.is_official_email("anyone@anywhere.com") is True


def test_every_admin_route_is_guarded():
    """A structural check: no route under /admin without a role dependency."""
    import ast
    from pathlib import Path

    guards = {"require_internal", "require_reviewer", "require_elevated", "require_admin"}
    unguarded = []
    for file in sorted(Path("app/routers").glob("*.py")):
        tree = ast.parse(file.read_text(encoding="utf-8"))
        prefix = ""
        for node in tree.body:
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                func = node.value.func
                if isinstance(func, ast.Name) and func.id == "APIRouter":
                    for kw in node.value.keywords:
                        if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                            prefix = kw.value.value
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                f = dec.func
                if not (isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name)):
                    continue
                if f.value.id != "router":
                    continue
                path = dec.args[0].value if dec.args and isinstance(dec.args[0], ast.Constant) else ""
                if not (prefix + path).startswith("/admin"):
                    continue
                deps = set()
                for default in list(node.args.defaults) + list(node.args.kw_defaults):
                    if (
                        isinstance(default, ast.Call)
                        and isinstance(default.func, ast.Name)
                        and default.func.id == "Depends"
                        and default.args
                        and isinstance(default.args[0], ast.Name)
                    ):
                        deps.add(default.args[0].id)
                if not (deps & guards):
                    unguarded.append(f"{f.attr.upper()} {prefix}{path}")
    assert not unguarded, f"unguarded admin routes: {unguarded}"


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
    print(f"\n{len(tests) - failures}/{len(tests)} access-control tests passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
