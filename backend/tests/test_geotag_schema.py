"""Geotagging contract tests.

The map module saves a geotag through the existing
PATCH /api/admin/projects/{id}. That only persists if `ProjectUpdate` declares
latitude and longitude - Pydantic silently drops unknown fields, so without
them a save would "succeed" and store nothing. These tests fail loudly if the
two fields are ever removed.

    python -m tests.test_geotag_schema
"""
from __future__ import annotations

from tests._email_validator_stub import install_if_missing

install_if_missing()

from pydantic import ValidationError  # noqa: E402

from app.schemas.project import ProjectPublicSummary, ProjectUpdate  # noqa: E402


def test_update_schema_accepts_coordinates():
    payload = ProjectUpdate(latitude=26.912434, longitude=75.787271)
    changes = payload.model_dump(exclude_unset=True)
    assert changes == {"latitude": 26.912434, "longitude": 75.787271}, changes


def test_update_without_coordinates_leaves_them_untouched():
    changes = ProjectUpdate(remarks="site visited").model_dump(exclude_unset=True)
    assert "latitude" not in changes and "longitude" not in changes, changes


def test_update_rejects_impossible_coordinates():
    cases = [
        ("latitude above 90", lambda: ProjectUpdate(latitude=91.0)),
        ("latitude below -90", lambda: ProjectUpdate(latitude=-91.0)),
        ("longitude above 180", lambda: ProjectUpdate(longitude=181.0)),
        ("longitude below -180", lambda: ProjectUpdate(longitude=-181.0)),
    ]
    for label, factory in cases:
        try:
            factory()
        except ValidationError:
            continue
        raise AssertionError(f"schema wrongly accepted: {label}")


def test_citizen_summary_still_exposes_location():
    # The citizen map plots straight from the public list endpoint.
    assert "latitude" in ProjectPublicSummary.model_fields
    assert "longitude" in ProjectPublicSummary.model_fields


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
    print(f"\n{len(tests) - failures}/{len(tests)} geotag tests passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
