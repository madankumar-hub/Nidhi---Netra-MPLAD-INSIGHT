"""Contract tests for the API response schemas.

These run without a database or a web server. The most important assertions
here are the negative ones: a citizen-facing response model must not carry a
risk score, a review status, notes, reviews, mitigation or an audit trail.
That separation is the core requirement of the brief, so it is asserted in
code rather than left to review.
"""
from __future__ import annotations

from datetime import date, datetime

from tests._email_validator_stub import install_if_missing

install_if_missing()

from pydantic import ValidationError  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.schemas.auth import LoginRequest  # noqa: E402
from app.schemas.common import Page  # noqa: E402
from app.schemas.project import (  # noqa: E402
    ProgressPoint,
    ProjectAdminDetail,
    ProjectAdminSummary,
    ProjectCreate,
    ProjectPublicDetail,
    ProjectPublicSummary,
    StatusChangeRequest,
    TimelinePoint,
)
from app.schemas.risk import RiskAssessmentOut  # noqa: E402
from app.schemas.workflow import NoteCreate  # noqa: E402

#: Anything on this list leaking into a citizen response is a defect.
INTERNAL_FIELDS = {
    "risk_score",
    "risk_level",
    "review_status",
    "factors",
    "notes",
    "reviews",
    "mitigations",
    "open_risk_factors",
    "open_mitigations",
    "schedule_variance",
    "last_reviewed_at",
    "activity",
}

BASE = dict(
    id=1,
    project_code="MPLAD-2025-00001",
    title="Construction of community hall",
    mp_name="A B",
    constituency="C",
    state="Maharashtra",
    district="Pune",
    category="Community Halls",
    executing_agency="Public Works Department (PWD)",
    sanction_year=2025,
    start_date=date(2025, 1, 1),
    planned_end_date=date(2025, 12, 31),
    allocated_amount=20.0,
    spent_amount=8.0,
    remaining_amount=12.0,
    utilization_percent=40.0,
    progress_percent=35.0,
    status="In Progress",
    public_indicator="Normal",
)


def _public_summary() -> ProjectPublicSummary:
    return ProjectPublicSummary(**BASE)


def test_settings_load_and_parse_cors():
    assert settings.cors_origin_list, "CORS origins should parse from a comma-separated value"
    assert settings.ai_configured is False, "external AI must be off unless explicitly keyed"


def test_citizen_summary_carries_no_internal_fields():
    leaked = INTERNAL_FIELDS & set(_public_summary().model_dump())
    assert not leaked, f"citizen summary leaked {leaked}"


def test_citizen_detail_carries_no_internal_fields():
    detail = ProjectPublicDetail(
        **_public_summary().model_dump(),
        description="d",
        house="Lok Sabha",
        fund_updates=[],
        progress_updates=[],
        spending_timeline=[
            TimelinePoint(
                period="2025-03", allocated=20, spent=4, cumulative_spent=4, utilization_percent=20
            )
        ],
        progress_timeline=[ProgressPoint(period="2025-03", actual=10, planned=12)],
        days_remaining=100,
        is_overdue=False,
    )
    leaked = INTERNAL_FIELDS & set(detail.model_dump())
    assert not leaked, f"citizen detail leaked {leaked}"
    assert len(detail.spending_timeline) == 1


def test_admin_detail_does_carry_internal_fields():
    summary = ProjectAdminSummary(
        **_public_summary().model_dump(),
        review_status="Pending Review",
        risk_level="HIGH",
        risk_score=61.2,
        open_risk_factors=3,
        open_mitigations=2,
        is_overdue=False,
        days_remaining=100,
        schedule_variance=-12.0,
    )
    detail = ProjectAdminDetail(
        **summary.model_dump(),
        description="d",
        house="Lok Sabha",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        fund_updates=[],
        progress_updates=[],
        spending_timeline=[],
        progress_timeline=[],
        citizen_report_count=1,
    )
    assert detail.risk_level.value == "HIGH"
    assert detail.risk_score == 61.2
    assert detail.review_status.value == "Pending Review"


def test_generic_page_wrapper():
    page = Page[ProjectPublicSummary](
        items=[_public_summary()], total=1, page=1, page_size=12, total_pages=1
    )
    assert page.items[0].project_code == "MPLAD-2025-00001"


class _FakeFactor:
    id = 1
    code = "OVERDUE_INCOMPLETE"
    title = "Project is past its planned completion date and still open"
    category = "Schedule Risk"
    severity = "HIGH"
    source = "rule_based"
    contribution = 22.6
    weight = 0.24
    detected_indicator = "i"
    evidence = "e"
    explanation = "x"
    recommended_action = "a"
    metric_name = "days_overdue"
    metric_value = 173.0
    threshold_value = 0.0
    reference_project_code = None


class _FakeAssessment:
    id = 9
    project_id = 1
    risk_score = 68.4
    risk_level = "HIGH"
    likelihood = "Likely"
    impact = "Major"
    primary_category = "Schedule Risk"
    status = "Open"
    summary = "s"
    explanation = "x"
    recommended_actions = "- do it"
    #: The column stores a comma-separated string; the API returns a list.
    analysis_sources = "rule_based,statistical"
    engine_version = "mplad-risk-engine-1.0"
    ai_model_used = None
    ai_narrative = None
    data_completeness_percent = 100.0
    assessed_at = datetime.now()
    is_current = True
    factors = [_FakeFactor()]
    mitigations: list = []


def test_risk_assessment_validates_from_attributes():
    out = RiskAssessmentOut.model_validate(_FakeAssessment(), from_attributes=True)
    assert out.analysis_sources == ["rule_based", "statistical"]
    assert out.factors[0].code == "OVERDUE_INCOMPLETE"
    assert out.ai_narrative is None


def test_invalid_input_is_rejected():
    cases = [
        ("malformed email", lambda: LoginRequest(email="not-an-email", password="x")),
        ("empty password", lambda: LoginRequest(email="a@b.com", password="")),
        (
            "sanction year out of range",
            lambda: ProjectCreate(
                title="abcd",
                mp_name="x",
                state="MH",
                district="Pune",
                category="R",
                executing_agency="P",
                sanction_year=1800,
                allocated_amount=-5,
            ),
        ),
        (
            "progress above 100%",
            lambda: ProjectCreate(
                title="abcd",
                mp_name="x",
                state="MH",
                district="Pune",
                category="R",
                executing_agency="P",
                sanction_year=2025,
                allocated_amount=5,
                progress_percent=140,
            ),
        ),
        ("status outside the enum", lambda: StatusChangeRequest(status="Not A Status", reason="x")),
        ("note below minimum length", lambda: NoteCreate(content="a", note_type="General Note")),
    ]
    for label, factory in cases:
        try:
            factory()
        except ValidationError:
            continue
        raise AssertionError(f"schema wrongly accepted: {label}")


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
    print(f"\n{len(tests) - failures}/{len(tests)} schema contract tests passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
