"""Shared data structures for the risk engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from app.core.enums import AnalysisSource, RiskCategory, RiskLevel


@dataclass
class FactorResult:
    """One explainable finding produced by an analysis layer."""

    code: str
    title: str
    category: RiskCategory
    severity: RiskLevel
    weight: float                      # 0-1 relative importance
    raw_score: float                   # 0-100 severity of THIS factor
    detected_indicator: str            # what was detected
    evidence: str                      # the data that caused it
    explanation: str                   # why it matters
    recommended_action: str            # what the admin should do
    source: AnalysisSource = AnalysisSource.RULE_BASED
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    reference_project_code: Optional[str] = None
    responsible_party: str = "Executing Agency"

    @property
    def contribution(self) -> float:
        return round(self.raw_score * self.weight, 2)


@dataclass
class ProjectMetrics:
    """Derived, purely arithmetic indicators used by every rule."""

    as_of: date
    duration_days: Optional[int] = None
    elapsed_days: Optional[int] = None
    days_remaining: Optional[int] = None
    time_elapsed_percent: Optional[float] = None
    expected_progress_percent: Optional[float] = None
    progress_percent: float = 0.0
    schedule_variance: Optional[float] = None          # actual - expected
    utilization_percent: float = 0.0
    expected_utilization_percent: Optional[float] = None
    utilization_progress_gap: Optional[float] = None   # utilization - progress
    cost_overrun_percent: Optional[float] = None
    days_since_progress_update: Optional[int] = None
    days_since_fund_update: Optional[int] = None
    is_overdue: bool = False
    data_completeness_percent: float = 100.0
    missing_fields: List[str] = field(default_factory=list)


@dataclass
class CohortStats:
    """Peer-group statistics used by the statistical layer.

    Keys are cohort identifiers (e.g. the project category).
    """

    allocation_mean: Dict[str, float] = field(default_factory=dict)
    allocation_std: Dict[str, float] = field(default_factory=dict)
    cost_per_beneficiary_mean: Dict[str, float] = field(default_factory=dict)
    cost_per_beneficiary_std: Dict[str, float] = field(default_factory=dict)
    sample_size: Dict[str, int] = field(default_factory=dict)


@dataclass
class DuplicateMatch:
    project_code: str
    title: str
    similarity: float


@dataclass
class RiskResult:
    """Full output of one assessment run."""

    risk_score: float
    risk_level: RiskLevel
    likelihood: str
    impact: str
    primary_category: Optional[RiskCategory]
    summary: str
    explanation: str
    recommended_actions: str
    factors: List[FactorResult]
    sources: List[AnalysisSource]
    engine_version: str
    data_completeness_percent: float
    metrics: ProjectMetrics
    ai_model_used: Optional[str] = None
    ai_narrative: Optional[str] = None
