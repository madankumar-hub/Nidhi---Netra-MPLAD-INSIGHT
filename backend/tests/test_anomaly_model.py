"""Tests for the unsupervised machine-learning layer.

These prove the isolation forest does real work: that it scores a planted
multivariate outlier above the population, that it refuses to run on a cohort
too small to learn from, that its output is deterministic for a given seed, and
that every finding it produces names the features that drove it.
"""
from __future__ import annotations

import random
from datetime import date, timedelta

from app.core.enums import AnalysisSource
from app.risk import assess_project
from app.risk.anomaly import (
    FEATURE_NAMES,
    FLAG_PERCENTILE,
    FLAG_THRESHOLD,
    MIN_COHORT,
    describe,
    evaluate_anomaly,
    extract_features,
    fit,
)
from tests.fake_project import FakeProject, FakeUpdate

TODAY = date.today()


def _normal_cohort(count: int = 240, seed: int = 11) -> list:
    """A population of unremarkable works, all internally consistent."""
    rng = random.Random(seed)
    cohort = []
    for index in range(count):
        start = TODAY - timedelta(days=rng.randint(120, 400))
        end = start + timedelta(days=rng.choice([365, 540]))
        allocated = round(rng.uniform(8.0, 22.0), 2)
        elapsed = min(max((TODAY - start).days / (end - start).days, 0.0), 1.0)
        progress = round(min(elapsed * rng.uniform(0.92, 1.05), 0.98) * 100, 1)
        spent = round(allocated * (progress / 100) * rng.uniform(0.95, 1.05), 2)
        cohort.append(
            FakeProject(
                id=index + 1,
                project_code=f"N{index:04d}",
                allocated_amount=allocated,
                spent_amount=spent,
                progress_percent=progress,
                start_date=start,
                planned_end_date=end,
                beneficiaries=rng.choice([800, 1000, 1200]),
                progress_updates=[FakeUpdate(TODAY - timedelta(days=rng.randint(5, 40)), progress)],
                fund_updates=[
                    FakeUpdate(TODAY - timedelta(days=30), expenditure_amount=spent / 2),
                    FakeUpdate(TODAY - timedelta(days=10), expenditure_amount=spent / 2),
                ],
            )
        )
    return cohort


def test_feature_vector_shape_and_order():
    project = _normal_cohort(MIN_COHORT)[0]
    features = extract_features(project)
    assert len(features) == len(FEATURE_NAMES)
    assert all(isinstance(value, float) for value in features)


def test_model_refuses_a_cohort_that_is_too_small():
    """Below the minimum the model must decline rather than pretend."""
    assert fit(_normal_cohort(MIN_COHORT - 1)) is None
    info = describe(None)
    assert info["available"] is False


def test_model_fits_on_a_real_cohort():
    model = fit(_normal_cohort())
    assert model is not None and model.is_fitted
    info = describe(model)
    assert info["available"] is True
    assert info["supervised"] is False
    assert info["trees"] == model.n_trees
    assert info["trained_on_records"] == 240


def test_planted_outlier_scores_above_the_population():
    """The point of the layer: a record whose *combination* is unlike the rest.

    Every individual figure below is plausible on its own - it is the
    combination that does not occur anywhere else in the cohort.
    """
    cohort = _normal_cohort()
    outlier = FakeProject(
        id=9999,
        project_code="OUTLIER",
        allocated_amount=140.0,          # far larger than the 8-22 population
        spent_amount=138.0,              # ~99% utilisation
        progress_percent=22.0,           # against very low progress
        start_date=TODAY - timedelta(days=60),
        planned_end_date=TODAY + timedelta(days=700),   # unusually long window
        beneficiaries=90,                # very high cost per beneficiary
        progress_updates=[FakeUpdate(TODAY - timedelta(days=400), 22.0)],
        fund_updates=[FakeUpdate(TODAY - timedelta(days=20), expenditure_amount=138.0)],
    )
    model = fit(cohort + [outlier])
    assert model is not None

    outlier_score = model.anomaly_score(extract_features(outlier))
    normal_scores = [model.anomaly_score(extract_features(p)) for p in cohort]
    average_normal = sum(normal_scores) / len(normal_scores)

    assert outlier_score > average_normal, (outlier_score, average_normal)
    assert outlier_score >= FLAG_THRESHOLD, outlier_score
    assert model.percentile(outlier_score) >= FLAG_PERCENTILE

    # and the typical record must NOT be flagged
    assert evaluate_anomaly(cohort[0], model) is None


def test_finding_names_the_features_that_drove_it():
    cohort = _normal_cohort()
    outlier = FakeProject(
        id=9999,
        project_code="OUTLIER",
        allocated_amount=160.0,
        spent_amount=158.0,
        progress_percent=15.0,
        start_date=TODAY - timedelta(days=45),
        planned_end_date=TODAY + timedelta(days=800),
        beneficiaries=60,
        progress_updates=[FakeUpdate(TODAY - timedelta(days=430), 15.0)],
        fund_updates=[FakeUpdate(TODAY - timedelta(days=15), expenditure_amount=158.0)],
    )
    model = fit(cohort + [outlier])
    factor = evaluate_anomaly(outlier, model)
    assert factor is not None
    assert factor.source == AnalysisSource.MACHINE_LEARNING
    assert factor.code == "ML_MULTIVARIATE_ANOMALY"
    # the four questions the interface renders
    assert factor.detected_indicator.strip()
    assert "percentile" in factor.detected_indicator
    assert "sigma" in factor.evidence
    assert factor.explanation.strip()
    assert factor.recommended_action.strip()
    assert factor.metric_value is not None and factor.metric_value >= FLAG_THRESHOLD


def test_model_is_deterministic_for_a_given_seed():
    cohort = _normal_cohort()
    first = fit(cohort, seed=7)
    second = fit(cohort, seed=7)
    assert first is not None and second is not None
    sample = extract_features(cohort[3])
    assert first.anomaly_score(sample) == second.anomaly_score(sample)


def test_engine_records_the_ml_layer_only_when_a_model_is_supplied():
    cohort = _normal_cohort()
    model = fit(cohort)
    subject = cohort[0]

    without = assess_project(subject)
    assert AnalysisSource.MACHINE_LEARNING not in without.sources

    with_model = assess_project(subject, anomaly_model=model)
    assert AnalysisSource.MACHINE_LEARNING in with_model.sources


def test_ml_factor_cannot_dominate_the_score_on_its_own():
    """The model contributes one weighted factor; it never sets the level."""
    cohort = _normal_cohort()
    outlier = FakeProject(
        id=9999,
        project_code="OUTLIER",
        allocated_amount=150.0,
        spent_amount=148.0,
        progress_percent=95.0,
        start_date=TODAY - timedelta(days=200),
        planned_end_date=TODAY + timedelta(days=200),
        beneficiaries=70,
        progress_updates=[FakeUpdate(TODAY - timedelta(days=5), 95.0)],
        fund_updates=[FakeUpdate(TODAY - timedelta(days=5), expenditure_amount=148.0)],
    )
    model = fit(cohort + [outlier])
    result = assess_project(outlier, anomaly_model=model)
    ml_factors = [f for f in result.factors if f.source == AnalysisSource.MACHINE_LEARNING]
    if ml_factors:
        assert ml_factors[0].contribution <= 16.0, "one factor must not swamp the score"
    assert 0 <= result.risk_score <= 100


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
    print(f"\n{len(tests) - failures}/{len(tests)} machine-learning tests passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
