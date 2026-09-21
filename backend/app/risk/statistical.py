"""Statistical (peer-comparison) layer.

Pure-python descriptive statistics - no model training, no external service.
Findings from this layer are always tagged `statistical` so the UI can keep
them visually distinct from rule-based findings.
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional, Sequence

from app.core.enums import AnalysisSource, RiskCategory, RiskLevel
from app.risk.types import CohortStats, FactorResult, ProjectMetrics

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from app.models.project import Project

MIN_SAMPLE = 8
Z_THRESHOLD = 2.0


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    mu = _mean(values)
    return math.sqrt(sum((v - mu) ** 2 for v in values) / (len(values) - 1))


def build_cohort_stats(projects: Iterable[Project]) -> CohortStats:
    """Group peer statistics by project category."""
    allocations: Dict[str, List[float]] = {}
    cpb: Dict[str, List[float]] = {}

    for p in projects:
        key = p.category or "Uncategorised"
        if p.allocated_amount and p.allocated_amount > 0:
            allocations.setdefault(key, []).append(float(p.allocated_amount))
            if p.beneficiaries and p.beneficiaries > 0:
                cpb.setdefault(key, []).append(float(p.allocated_amount) / float(p.beneficiaries))

    stats = CohortStats()
    for key, values in allocations.items():
        stats.allocation_mean[key] = _mean(values)
        stats.allocation_std[key] = _std(values)
        stats.sample_size[key] = len(values)
    for key, values in cpb.items():
        stats.cost_per_beneficiary_mean[key] = _mean(values)
        stats.cost_per_beneficiary_std[key] = _std(values)
    return stats


def _z(value: float, mean: float, std: float) -> Optional[float]:
    if std <= 0:
        return None
    return (value - mean) / std


def evaluate_statistical(
    project: Project, metrics: ProjectMetrics, stats: Optional[CohortStats]
) -> List[FactorResult]:
    if stats is None:
        return []

    factors: List[FactorResult] = []
    key = project.category or "Uncategorised"
    sample = stats.sample_size.get(key, 0)
    if sample < MIN_SAMPLE:
        return factors

    # --- Allocation outlier within the same category -----------------------
    mean = stats.allocation_mean.get(key, 0.0)
    std = stats.allocation_std.get(key, 0.0)
    z = _z(float(project.allocated_amount or 0.0), mean, std)
    if z is not None and z >= Z_THRESHOLD:
        raw = min(30 + (z - Z_THRESHOLD) * 25, 100.0)
        factors.append(
            FactorResult(
                code="ALLOCATION_OUTLIER",
                title="Sanctioned amount is a statistical outlier for this category",
                category=RiskCategory.FINANCIAL,
                severity=RiskLevel.HIGH if raw >= 50 else RiskLevel.MEDIUM,
                weight=0.14,
                raw_score=raw,
                source=AnalysisSource.STATISTICAL,
                detected_indicator=(
                    f"The allocation is {z:.1f} standard deviations above the mean for "
                    f"'{key}' works."
                ),
                evidence=(
                    f"This work: Rs {project.allocated_amount:,.2f} lakh. Category mean "
                    f"Rs {mean:,.2f} lakh, standard deviation Rs {std:,.2f} lakh, "
                    f"n = {sample}."
                ),
                explanation=(
                    "An unusually large sanction for the category can be entirely "
                    "legitimate (larger scope, difficult terrain), but it should be "
                    "supported by an estimate that explains the difference."
                ),
                recommended_action=(
                    "Compare the detailed estimate against the schedule of rates and "
                    "confirm the scope justifies the higher sanction."
                ),
                metric_name="allocation_zscore",
                metric_value=round(z, 2),
                threshold_value=Z_THRESHOLD,
                responsible_party="Auditor",
            )
        )

    # --- Cost per beneficiary outlier --------------------------------------
    if project.beneficiaries and project.beneficiaries > 0 and project.allocated_amount:
        cpb_mean = stats.cost_per_beneficiary_mean.get(key, 0.0)
        cpb_std = stats.cost_per_beneficiary_std.get(key, 0.0)
        value = float(project.allocated_amount) / float(project.beneficiaries)
        zc = _z(value, cpb_mean, cpb_std)
        if zc is not None and zc >= Z_THRESHOLD:
            raw = min(28 + (zc - Z_THRESHOLD) * 22, 100.0)
            factors.append(
                FactorResult(
                    code="COST_PER_BENEFICIARY_OUTLIER",
                    title="Cost per beneficiary is far above the category norm",
                    category=RiskCategory.EXPENDITURE,
                    severity=RiskLevel.HIGH if raw >= 50 else RiskLevel.MEDIUM,
                    weight=0.12,
                    raw_score=raw,
                    source=AnalysisSource.STATISTICAL,
                    detected_indicator=(
                        f"Cost per beneficiary is {zc:.1f} standard deviations above the "
                        f"mean for '{key}' works."
                    ),
                    evidence=(
                        f"This work: Rs {value:,.4f} lakh per beneficiary "
                        f"({project.beneficiaries:,} beneficiaries). Category mean "
                        f"Rs {cpb_mean:,.4f} lakh."
                    ),
                    explanation=(
                        "Either the beneficiary count is understated or the per-unit cost "
                        "is high. Both affect the value-for-money assessment."
                    ),
                    recommended_action=(
                        "Verify the beneficiary estimate in the project proposal against "
                        "census or ward-level figures."
                    ),
                    metric_name="cost_per_beneficiary_zscore",
                    metric_value=round(zc, 2),
                    threshold_value=Z_THRESHOLD,
                    responsible_party="District Authority",
                )
            )

    return factors
