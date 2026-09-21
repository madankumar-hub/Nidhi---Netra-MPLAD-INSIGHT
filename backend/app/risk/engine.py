"""Risk engine orchestrator.

Three clearly separated layers:

  1. rule_based  - deterministic thresholds over the project record.
                   ALWAYS runs. No network, no model, no external service.
  2. statistical - peer-cohort outlier detection and near-duplicate
                   description matching. Runs whenever a peer group of
                   sufficient size is supplied.
  3. external_ai - OPTIONAL narrative enhancement. Only runs when an API key
                   is configured. Never changes the score or the level.

The assessment records exactly which layers contributed, so the interface
never implies a model was involved when only rules ran.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List, Optional, Sequence

from app.core.enums import (
    AnalysisSource,
    Impact,
    Likelihood,
    RiskCategory,
    RiskLevel,
)
from app.risk import ai_provider, anomaly, duplicate, statistical
from app.risk.metrics import compute_metrics
from app.risk.mitigation_templates import recommended_actions
from app.risk.rules import evaluate_rules
from app.risk.anomaly import IsolationForestModel
from app.risk.types import CohortStats, FactorResult, RiskResult

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from app.models.project import Project

logger = logging.getLogger("mplad.risk.engine")

ENGINE_VERSION = "mplad-risk-engine-1.0"

LEVEL_THRESHOLDS = ((75.0, RiskLevel.CRITICAL), (50.0, RiskLevel.HIGH), (25.0, RiskLevel.MEDIUM))


def level_from_score(score: float) -> RiskLevel:
    for threshold, level in LEVEL_THRESHOLDS:
        if score >= threshold:
            return level
    return RiskLevel.LOW


def _aggregate_score(factors: Sequence[FactorResult]) -> float:
    """Weighted, saturating aggregation.

    Contributions are combined with a diminishing-returns curve so that a
    project with one severe problem is not automatically ranked below a
    project with five trivial ones.
    """
    if not factors:
        return 0.0
    ordered = sorted(factors, key=lambda f: f.contribution, reverse=True)
    score = 0.0
    for index, factor in enumerate(ordered):
        decay = 1.0 / (1.0 + 0.30 * index)
        score += factor.contribution * decay
    return round(min(score, 100.0), 2)


def _likelihood_from_score(score: float) -> Likelihood:
    if score >= 80:
        return Likelihood.ALMOST_CERTAIN
    if score >= 60:
        return Likelihood.LIKELY
    if score >= 35:
        return Likelihood.POSSIBLE
    if score >= 15:
        return Likelihood.UNLIKELY
    return Likelihood.RARE


def _impact_from_exposure(project: Project, score: float) -> Impact:
    """Impact reflects the public money at stake as well as the score."""
    exposure = float(project.allocated_amount or 0.0)
    if exposure >= 100:
        band = 2
    elif exposure >= 40:
        band = 1
    else:
        band = 0

    if score >= 70:
        base = 3
    elif score >= 45:
        base = 2
    elif score >= 20:
        base = 1
    else:
        base = 0

    idx = min(base + (1 if band == 2 else 0), 4)
    return [Impact.NEGLIGIBLE, Impact.MINOR, Impact.MODERATE, Impact.MAJOR, Impact.SEVERE][idx]


def _primary_category(factors: Sequence[FactorResult]) -> Optional[RiskCategory]:
    if not factors:
        return None
    totals: dict[RiskCategory, float] = {}
    for factor in factors:
        totals[factor.category] = totals.get(factor.category, 0.0) + factor.contribution
    return max(totals.items(), key=lambda kv: kv[1])[0]


def _build_summary(project: Project, level: RiskLevel, factors: Sequence[FactorResult]) -> str:
    if not factors:
        return (
            "No risk indicators were detected. Schedule, expenditure and progress "
            "figures are consistent with the sanctioned plan."
        )
    top = factors[0]
    extra = len(factors) - 1
    tail = f" and {extra} further indicator{'s' if extra > 1 else ''}" if extra > 0 else ""
    return f"{level.value} risk. Principal indicator: {top.title.lower()}{tail}."


def _build_explanation(factors: Sequence[FactorResult]) -> str:
    if not factors:
        return (
            "Every deterministic check applied to this record passed. No schedule "
            "slippage, expenditure-progress divergence or data inconsistency was found."
        )
    lines = []
    for factor in factors:
        lines.append(
            f"{factor.title} ({factor.category.value}, {factor.severity.value}): "
            f"{factor.detected_indicator} {factor.evidence}"
        )
    return "\n\n".join(lines)


def assess_project(
    project: Project,
    *,
    peers: Optional[Sequence[Project]] = None,
    cohort_stats: Optional[CohortStats] = None,
    anomaly_model: Optional[IsolationForestModel] = None,
    open_citizen_reports: int = 0,
    use_external_ai: bool = False,
) -> RiskResult:
    """Run every available analysis layer and return a complete result."""
    metrics = compute_metrics(project)
    sources: List[AnalysisSource] = [AnalysisSource.RULE_BASED]

    factors: List[FactorResult] = evaluate_rules(project, metrics, open_citizen_reports)

    statistical_factors: List[FactorResult] = []
    if cohort_stats is not None:
        statistical_factors.extend(statistical.evaluate_statistical(project, metrics, cohort_stats))
    if peers:
        matches = duplicate.find_duplicates(project, peers)
        dup = duplicate.duplicate_factor(matches)
        if dup is not None:
            statistical_factors.append(dup)
    if statistical_factors:
        factors.extend(statistical_factors)
        sources.append(AnalysisSource.STATISTICAL)
    elif cohort_stats is not None or peers:
        # The layer ran and found nothing - still record that it ran.
        sources.append(AnalysisSource.STATISTICAL)

    # --- layer 3: unsupervised machine learning --------------------------
    if anomaly_model is not None and anomaly_model.is_fitted:
        sources.append(AnalysisSource.MACHINE_LEARNING)
        ml_factor = anomaly.evaluate_anomaly(project, anomaly_model)
        if ml_factor is not None:
            factors.append(ml_factor)

    factors.sort(key=lambda f: f.contribution, reverse=True)

    score = _aggregate_score(factors)
    level = level_from_score(score)

    result = RiskResult(
        risk_score=score,
        risk_level=level,
        likelihood=_likelihood_from_score(score).value,
        impact=_impact_from_exposure(project, score).value,
        primary_category=_primary_category(factors),
        summary=_build_summary(project, level, factors),
        explanation=_build_explanation(factors),
        recommended_actions="\n".join(f"- {a}" for a in recommended_actions(factors)),
        factors=factors,
        sources=sources,
        engine_version=ENGINE_VERSION,
        data_completeness_percent=metrics.data_completeness_percent,
        metrics=metrics,
    )

    if use_external_ai and ai_provider.is_available() and factors:
        enhancement = ai_provider.enhance(project.title, level.value, score, factors)
        if enhancement is not None:
            result.ai_narrative = enhancement.narrative
            result.ai_model_used = enhancement.model
            result.sources.append(AnalysisSource.EXTERNAL_AI)

    return result


def engine_info(anomaly_model: Optional[IsolationForestModel] = None) -> dict:
    ai = ai_provider.describe()
    ml = anomaly.describe(anomaly_model)
    return {
        "engine_version": ENGINE_VERSION,
        "rule_based_enabled": True,
        "statistical_enabled": True,
        "machine_learning_enabled": ml["available"],
        "machine_learning": ml,
        "duplicate_detection_backend": duplicate.active_backend(),
        "external_ai_enabled": bool(ai["configured"]),
        "external_ai_provider": ai["provider"],
        "external_ai_model": ai["model"],
        "notes": (
            "Three analysis layers contribute to the score: deterministic threshold "
            "rules, peer-cohort statistics, and an unsupervised isolation forest that "
            "is fitted on the live project population and needs no labels. Every "
            "contribution is traceable to the project record. A fourth, optional layer "
            "can ask an external model to write a narrative over findings that have "
            "already been computed; it never sets the score or the level. Findings are "
            "indicators flagged for investigation, not findings of wrongdoing."
        ),
    }
