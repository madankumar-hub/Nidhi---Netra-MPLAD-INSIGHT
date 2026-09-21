"""Import shim for environments without the optional `email-validator` package.

`pydantic.EmailStr` requires it at schema-build time. Installing
`requirements.txt` provides it, and this module then does nothing. It exists so
the schema contract tests can run in a bare interpreter.
"""
from __future__ import annotations

import importlib.metadata as metadata
import re
import sys
import types


def install_if_missing() -> bool:
    """Returns True when a stand-in was installed."""
    try:
        import email_validator  # noqa: F401

        return False
    except ImportError:
        pass

    module = types.ModuleType("email_validator")

    class EmailNotValidError(ValueError):
        pass

    class EmailSyntaxError(EmailNotValidError):
        pass

    class EmailUndeliverableError(EmailNotValidError):
        pass

    pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")

    class _Result:
        def __init__(self, email: str):
            self.normalized = self.email = email
            self.local_part, _, self.domain = email.partition("@")

    def validate_email(email: str, *args, **kwargs):
        if not pattern.match(email or ""):
            raise EmailSyntaxError("invalid email address")
        return _Result(email)

    module.validate_email = validate_email
    module.EmailNotValidError = EmailNotValidError
    module.EmailSyntaxError = EmailSyntaxError
    module.EmailUndeliverableError = EmailUndeliverableError
    module.__version__ = "2.2.0"
    sys.modules["email_validator"] = module

    original_version = metadata.version

    def version(name: str) -> str:
        if name == "email-validator":
            return "2.2.0"
        return original_version(name)

    metadata.version = version
    try:
        import pydantic.networks as networks

        networks.version = version
    except ImportError:  # pragma: no cover
        pass
    return True
