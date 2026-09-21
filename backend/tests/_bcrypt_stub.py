"""Import shim for environments without the `bcrypt` package.

Installing `requirements.txt` provides the real library and this module does
nothing. It exists only so the test modules can be imported in a bare
interpreter; any test that actually exercises hashing checks `is_stub()` first
and reports itself as skipped rather than asserting against a fake.
"""
from __future__ import annotations

import sys
import types

STUB_VERSION = "0.0.0-stub"


def install_if_missing() -> bool:
    """Returns True when a stand-in was installed."""
    try:
        import bcrypt  # noqa: F401

        return False
    except ImportError:
        pass

    module = types.ModuleType("bcrypt")
    module.gensalt = lambda *args, **kwargs: b"$2b$12$stub"
    module.hashpw = lambda password, salt: salt + password
    module.checkpw = lambda password, hashed: hashed.endswith(password)
    module.__version__ = STUB_VERSION
    sys.modules["bcrypt"] = module
    return True


def is_stub() -> bool:
    """True when the bcrypt currently importable is our stand-in."""
    module = sys.modules.get("bcrypt")
    if module is None:
        try:
            import bcrypt as module  # type: ignore[no-redef]
        except ImportError:
            return True
    return getattr(module, "__version__", "") == STUB_VERSION
