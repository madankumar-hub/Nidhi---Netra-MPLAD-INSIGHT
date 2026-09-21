"""Things that must hold before this is exposed to the internet.

Everything here is about the gap between "works on a laptop" and "safe on a
public URL". Each test guards a mistake that produces a deployment which looks
completely healthy - green health check, pages load - while being wrong in a way
nobody would notice until it mattered.

Source is read with `ast` and as text rather than imported, so these run without
SQLAlchemy or a database.
"""
from __future__ import annotations

import ast
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REPO = ROOT.parent
MAIN = ROOT / "app" / "main.py"
CONFIG = ROOT / "app" / "core" / "config.py"
ENV_EXAMPLE = ROOT / ".env.example"
GITIGNORE = REPO / ".gitignore"
RENDER = REPO / "render.yaml"

INSECURE_DEFAULT = "dev-only-insecure-secret-change-me"


def test_production_refuses_the_development_signing_key() -> None:
    """The default is in this repository. A production instance still using it
    lets anyone forge `{"role": "admin"}` - so this must abort startup, not log.
    """
    source = MAIN.read_text(encoding="utf-8")
    assert INSECURE_DEFAULT in source, "the startup guard no longer names the default secret"

    tree = ast.parse(source)
    raises_in_guard = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        test_src = ast.dump(node.test)
        if "is_production" not in test_src or "INSECURE_DEFAULT_SECRET" not in test_src:
            continue
        raises_in_guard = any(isinstance(inner, ast.Raise) for inner in ast.walk(node))
    assert raises_in_guard, (
        "the production/default-secret check does not raise - logging an error and "
        "starting anyway is not a control"
    )


def test_the_env_example_ships_no_real_secrets() -> None:
    """A filled-in example file is how a key reaches a public repository."""
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        upper = key.upper()
        # Match on how the name ENDS, not on what it contains: the first version
        # of this flagged ACCESS_TOKEN_EXPIRE_MINUTES=120 because "TOKEN" appears
        # in it. A test that cries wolf on a timeout is a test people switch off.
        if not upper.endswith(("PASSWORD", "SECRET", "SECRET_KEY", "API_KEY", "TOKEN")):
            continue
        if value == "":
            continue
        if "change-me" in value.lower() or "CHANGE_ME" in value:
            continue
        # A bare number is a setting, never a credential.
        if re.fullmatch(r"-?\d+", value):
            continue
        raise AssertionError(f".env.example carries a real-looking value for {key}: {value!r}")


def test_seed_passwords_are_blank_in_the_example() -> None:
    """Blank means the seeder generates one. A value here would become the
    password on every deployment that copied the file."""
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    for name in ("SEED_ADMIN_PASSWORD", "SEED_AUDITOR_PASSWORD",
                 "SEED_OFFICER_PASSWORD", "SEED_CITIZEN_PASSWORD"):
        match = re.search(rf"^{name}=(.*)$", text, re.M)
        assert match, f"{name} missing from .env.example"
        assert match.group(1).strip() == "", f"{name} is pre-filled in .env.example"


def test_gitignore_excludes_everything_that_must_never_be_committed() -> None:
    """Compare whole lines, not substrings.

    The first version of this used `required in patterns`, so deleting the `.env`
    rule still passed - the string `.env` survives inside `.env.*` and
    `!.env.example`. A test that cannot fail is worse than no test, because it
    reads as coverage. Rules are now matched exactly.
    """
    rules = {
        line.strip()
        for line in GITIGNORE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    for required in (".env", "*.db", "*.sqlite", "node_modules/", ".venv/", "dist/",
                     "backend/.seed-credentials.txt", "*.pem", "*.key"):
        assert required in rules, f".gitignore has no exact rule for {required}"
    # The negation must come after the .env rules or .env.example is excluded too.
    assert "!.env.example" in rules, ".env.example is excluded and would not ship"


def test_no_source_file_hardcodes_a_credential() -> None:
    offenders: list[str] = []
    for path in sorted((ROOT / "app").rglob("*.py")) + sorted((ROOT / "seed").rglob("*.py")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if re.search(r"""(password|secret|api_key)\s*=\s*["'][A-Za-z0-9!@#$%^&*_-]{6,}["']""",
                         line, re.I):
                if "change-me" in line.lower() or "dev-only" in line.lower():
                    continue  # the named development default, guarded above
                offenders.append(f"{path.relative_to(REPO)}:{number}: {line.strip()[:80]}")
    assert not offenders, "hardcoded credentials:\n  " + "\n  ".join(offenders)


def test_the_deployment_blueprint_holds_no_secret_values() -> None:
    """Every secret in render.yaml must be generated or set in the dashboard."""
    if not RENDER.exists():
        return
    text = RENDER.read_text(encoding="utf-8")
    for name in ("SEED_ADMIN_PASSWORD", "SEED_AUDITOR_PASSWORD",
                 "SEED_OFFICER_PASSWORD", "SEED_CITIZEN_PASSWORD"):
        block = re.search(rf"key:\s*{name}\s*\n\s*(\S+)", text)
        assert block, f"{name} not declared in render.yaml"
        assert block.group(1).startswith(("sync:", "generateValue:")), (
            f"{name} appears to carry a literal value in render.yaml"
        )
    jwt = re.search(r"key:\s*JWT_SECRET_KEY\s*\n\s*(\S+)", text)
    assert jwt, "JWT_SECRET_KEY not declared in render.yaml"
    assert jwt.group(1).startswith(("generateValue:", "sync:")), (
        "JWT_SECRET_KEY carries a literal value in render.yaml"
    )


def test_error_detail_is_hidden_in_production() -> None:
    """Stack traces and validation internals must not reach a public client."""
    source = MAIN.read_text(encoding="utf-8")
    assert source.count("if settings.is_production else") >= 2, (
        "error handlers no longer suppress detail in production"
    )


def test_console_otp_cannot_be_used_in_production() -> None:
    """In development the OTP is returned to the caller. In production that
    would let anyone sign in as anyone."""
    otp = (ROOT / "app" / "auth" / "otp.py").read_text(encoding="utf-8")
    assert "not settings.is_production" in otp, (
        "console OTP delivery is not gated on the environment"
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
    print(f"\n{len(tests) - failures}/{len(tests)} deployment safety tests passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
