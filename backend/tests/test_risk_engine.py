"""Executable tests for the deterministic risk engine.

These run with the standard library alone (no database, no web framework),
so `python -m tests.test_risk_engine` is a complete check of the core logic.
`pytest` picks them up too.
"""
from __future__ import annotations

from datetime import date, timedelta

from app.core.enums import AnalysisSource, ProjectStatus, RiskCategory, RiskLevel
from app.risk import assess_project, build_cohort_stats, engine_info
from app.risk.duplicate import find_duplicates
from app.risk.metrics import compute_metrics
from tests.fake_project import FakeProject, FakeUpdate

TODAY = date.today()


def _codes(result) -> set:
    return {f.code for f in result.factors}


# ---------------------------------------------------------------------------
def test_healthy_project_scores_low():
    p = FakeProject(
        start_date=TODAY - timedelta(days=100),
        planned_end_date=TODAY + timedelta(days=100),
        progress_percent=52.0,
        spent_amount=10.0,
        progress_updates=[FakeUpdate(TODAY - timedelta(days=10), 52.0)],
        fund_updates=[FakeUpdate(TODAY - timedelta(days=10), expenditure_amount=10.0)],
    )
    result = assess_project(p)
    assert result.risk_level == RiskLevel.LOW, result.risk_level
    assert result.risk_score < 25, result.risk_score
    assert AnalysisSource.RULE_BASED in result.sources


def test_schedule_slippage_is_detected():
    p = FakeProject(
        start_date=TODAY - timedelta(days=300),
        planned_end_date=TODAY + timedelta(days=100),
        progress_percent=20.0,
        spent_amount=4.0,
        progress_updates=[FakeUpdate(TODAY - timedelta(days=15), 20.0)],
    )
    result = assess_project(p)
    assert "SCHEDULE_SLIPPAGE" in _codes(result)
    factor = next(f for f in result.factors if f.code == "SCHEDULE_SLIPPAGE")
    assert factor.evidence and factor.explanation and factor.recommended_action
    assert factor.metric_value is not None


def test_deadline_imminent_with_low_progress():
    p = FakeProject(
        start_date=TODAY - timedelta(days=330),
        planned_end_date=TODAY + timedelta(days=30),
        progress_percent=35.0,
        spent_amount=7.0,
        progress_updates=[FakeUpdate(TODAY - timedelta(days=20), 35.0)],
    )
    result = assess_project(p)
    assert "DEADLINE_IMMINENT_LOW_PROGRESS" in _codes(result)
    assert result.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL)


def test_overdue_and_delayed_escalate_the_level():
    p = FakeProject(
        status=ProjectStatus.DELAYED,
        start_date=TODAY - timedelta(days=700),
        planned_end_date=TODAY - timedelta(days=200),
        progress_percent=30.0,
        spent_amount=6.0,
        progress_updates=[FakeUpdate(TODAY - timedelta(days=400), 30.0)],
    )
    result = assess_project(p)
    codes = _codes(result)
    assert "OVERDUE_INCOMPLETE" in codes
    assert "STATUS_DELAYED" in codes
    assert "STALLED_PROGRESS_REPORTING" in codes
    assert result.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL), result.risk_score
    assert result.primary_category == RiskCategory.SCHEDULE


def test_expenditure_far_ahead_of_progress():
    p = FakeProject(
        start_date=TODAY - timedelta(days=200),
        planned_end_date=TODAY + timedelta(days=160),
        progress_percent=25.0,
        spent_amount=17.0,   # 85% utilisation against 25% progress
        progress_updates=[FakeUpdate(TODAY - timedelta(days=10), 25.0)],
    )
    result = assess_project(p)
    assert "EXPENDITURE_AHEAD_OF_PROGRESS" in _codes(result)
    factor = next(f for f in result.factors if f.code == "EXPENDITURE_AHEAD_OF_PROGRESS")
    assert factor.category == RiskCategory.FINANCIAL
    assert factor.metric_value >= 20


def test_cost_overrun_flagged_against_estimate():
    p = FakeProject(
        estimated_cost=20.0,
        allocated_amount=20.0,
        spent_amount=26.0,
        progress_percent=90.0,
        start_date=TODAY - timedelta(days=200),
        planned_end_date=TODAY + timedelta(days=60),
        progress_updates=[FakeUpdate(TODAY - timedelta(days=5), 90.0)],
    )
    result = assess_project(p)
    assert "COST_OVERRUN" in _codes(result)


def test_underspend_late_in_the_window():
    p = FakeProject(
        start_date=TODAY - timedelta(days=330),
        planned_end_date=TODAY + timedelta(days=35),
        progress_percent=30.0,
        spent_amount=1.0,
        progress_updates=[FakeUpdate(TODAY - timedelta(days=20), 30.0)],
    )
    result = assess_project(p)
    assert "UNDERSPEND_NEAR_DEADLINE" in _codes(result)


def test_completed_but_progress_and_funds_inconsistent():
    p = FakeProject(
        status=ProjectStatus.COMPLETED,
        start_date=TODAY - timedelta(days=400),
        planned_end_date=TODAY - timedelta(days=40),
        progress_percent=80.0,
        spent_amount=8.0,   # 40% utilisation
        progress_updates=[FakeUpdate(TODAY - timedelta(days=45), 80.0)],
    )
    result = assess_project(p)
    codes = _codes(result)
    assert "COMPLETED_PROGRESS_MISMATCH" in codes
    assert "COMPLETED_LOW_UTILIZATION" in codes


def test_incomplete_record_is_reported_and_lowers_completeness():
    p = FakeProject(description="", planned_end_date=None, start_date=None)
    result = assess_project(p)
    assert "INCOMPLETE_RECORD" in _codes(result)
    assert result.data_completeness_percent < 100


def test_citizen_report_cluster_raises_implementation_risk():
    p = FakeProject(
        start_date=TODAY - timedelta(days=100),
        planned_end_date=TODAY + timedelta(days=100),
        progress_percent=50.0,
        spent_amount=10.0,
        progress_updates=[FakeUpdate(TODAY - timedelta(days=5), 50.0)],
    )
    result = assess_project(p, open_citizen_reports=4)
    assert "CITIZEN_REPORTS_CLUSTER" in _codes(result)


def test_statistical_allocation_outlier():
    peers = [
        FakeProject(id=i + 2, project_code=f"P{i}", allocated_amount=10.0 + i * 0.2, beneficiaries=1000)
        for i in range(20)
    ]
    outlier = FakeProject(
        id=1,
        allocated_amount=95.0,
        beneficiaries=1000,
        start_date=TODAY - timedelta(days=50),
        planned_end_date=TODAY + timedelta(days=150),
        progress_percent=25.0,
        spent_amount=20.0,
        progress_updates=[FakeUpdate(TODAY - timedelta(days=5), 25.0)],
    )
    stats = build_cohort_stats(peers + [outlier])
    result = assess_project(outlier, cohort_stats=stats)
    assert "ALLOCATION_OUTLIER" in _codes(result)
    factor = next(f for f in result.factors if f.code == "ALLOCATION_OUTLIER")
    assert factor.source == AnalysisSource.STATISTICAL
    assert AnalysisSource.STATISTICAL in result.sources


def test_duplicate_description_detection():
    base = FakeProject(
        id=1,
        title="Construction of overhead water tank at Ramnagar",
        description=(
            "Construction of a 50000 litre reinforced cement concrete overhead water tank "
            "with distribution pipeline at Ramnagar, Sadar block."
        ),
    )
    twin = FakeProject(
        id=2,
        project_code="MPLAD-2025-00002",
        title="Construction of overhead water tank at Ramnagar",
        description=(
            "Construction of a 50000 litre reinforced cement concrete overhead water tank "
            "with distribution pipeline at Ramnagar, Sadar block."
        ),
    )
    unrelated = FakeProject(
        id=3,
        project_code="MPLAD-2025-00003",
        title="Development of playground at Kalyanpur",
        description="Levelling, fencing and development of a playground with a jogging track.",
    )
    matches = find_duplicates(base, [twin, unrelated])
    assert matches and matches[0].project_code == twin.project_code
    assert matches[0].similarity > 0.9
    assert all(m.project_code != unrelated.project_code for m in matches)

    result = assess_project(base, peers=[twin, unrelated])
    assert "NEAR_DUPLICATE_WORK" in _codes(result)


def test_every_factor_answers_the_four_questions():
    """What is the risk / why detected / what data / what to do."""
    p = FakeProject(
        status=ProjectStatus.DELAYED,
        start_date=TODAY - timedelta(days=700),
        planned_end_date=TODAY - timedelta(days=150),
        progress_percent=22.0,
        spent_amount=18.0,
        estimated_cost=20.0,
        progress_updates=[FakeUpdate(TODAY - timedelta(days=300), 22.0)],
    )
    result = assess_project(p, open_citizen_reports=3)
    assert result.factors
    for factor in result.factors:
        assert factor.title.strip()
        assert factor.detected_indicator.strip()
        assert factor.evidence.strip()
        assert factor.explanation.strip()
        assert factor.recommended_action.strip()
        assert 0 <= factor.contribution <= 100
    assert result.recommended_actions.strip()


def test_score_is_bounded_and_monotonic_in_severity():
    mild = FakeProject(
        start_date=TODAY - timedelta(days=200),
        planned_end_date=TODAY + timedelta(days=160),
        progress_percent=45.0,
        spent_amount=9.0,
        progress_updates=[FakeUpdate(TODAY - timedelta(days=5), 45.0)],
    )
    severe = FakeProject(
        status=ProjectStatus.DELAYED,
        start_date=TODAY - timedelta(days=900),
        planned_end_date=TODAY - timedelta(days=400),
        progress_percent=8.0,
        spent_amount=19.0,
        estimated_cost=15.0,
        progress_updates=[FakeUpdate(TODAY - timedelta(days=500), 8.0)],
    )
    mild_result = assess_project(mild)
    severe_result = assess_project(severe)
    assert 0 <= mild_result.risk_score <= 100
    assert 0 <= severe_result.risk_score <= 100
    assert severe_result.risk_score > mild_result.risk_score


def test_engine_reports_no_external_ai_when_unconfigured():
    info = engine_info()
    assert info["rule_based_enabled"] is True
    assert info["external_ai_enabled"] is False
    assert info["duplicate_detection_backend"] in ("tfidf", "embeddings")


def test_metrics_are_arithmetically_correct():
    p = FakeProject(
        start_date=TODAY - timedelta(days=100),
        planned_end_date=TODAY + timedelta(days=100),
        allocated_amount=50.0,
        spent_amount=20.0,
        progress_percent=30.0,
    )
    m = compute_metrics(p)
    assert m.duration_days == 200
    assert m.elapsed_days == 100
    assert m.days_remaining == 100
    assert abs(m.time_elapsed_percent - 50.0) < 0.01
    assert abs(m.utilization_percent - 40.0) < 0.01
    assert abs(m.utilization_progress_gap - 10.0) < 0.01


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
    print(f"\n{len(tests) - failures}/{len(tests)} risk-engine tests passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
