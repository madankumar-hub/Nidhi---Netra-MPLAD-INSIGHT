from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import (
    AnalysisSource,
    Impact,
    Likelihood,
    MitigationStatus,
    RiskCategory,
    RiskLevel,
    RiskStatus,
)


class RiskFactorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    title: str
    category: RiskCategory
    severity: RiskLevel
    source: AnalysisSource
    contribution: float
    weight: float
    detected_indicator: str
    evidence: str
    explanation: str
    recommended_action: str
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None
    reference_project_code: Optional[str] = None


class MitigationActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assessment_id: int
    project_id: int
    risk_factor_code: Optional[str] = None
    action: str
    responsible_party: str
    status: MitigationStatus
    priority: int
    due_date: Optional[date] = None
    notes: Optional[str] = None
    created_by_name: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by_name: Optional[str] = None
    is_system_recommended: bool


class MitigationActionCreate(BaseModel):
    action: str = Field(min_length=4, max_length=2000)
    responsible_party: str = Field(default="", max_length=200)
    risk_factor_code: Optional[str] = Field(default=None, max_length=60)
    priority: int = Field(default=2, ge=1, le=3)
    due_date: Optional[date] = None
    notes: Optional[str] = None
    status: MitigationStatus = MitigationStatus.OPEN


class MitigationActionUpdate(BaseModel):
    action: Optional[str] = Field(default=None, min_length=4, max_length=2000)
    responsible_party: Optional[str] = Field(default=None, max_length=200)
    status: Optional[MitigationStatus] = None
    priority: Optional[int] = Field(default=None, ge=1, le=3)
    due_date: Optional[date] = None
    notes: Optional[str] = None


class RiskAssessmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    risk_score: float
    risk_level: RiskLevel
    likelihood: Likelihood
    impact: Impact
    primary_category: Optional[RiskCategory] = None
    status: RiskStatus
    summary: str
    explanation: str
    recommended_actions: str
    analysis_sources: List[str] = Field(default_factory=list)
    engine_version: str
    ai_model_used: Optional[str] = None
    ai_narrative: Optional[str] = None
    data_completeness_percent: float
    assessed_at: datetime
    is_current: bool
    factors: List[RiskFactorOut] = Field(default_factory=list)
    mitigations: List[MitigationActionOut] = Field(default_factory=list)

    @field_validator("analysis_sources", mode="before")
    @classmethod
    def _split_sources(cls, value):
        """The column stores 'rule_based,statistical'; the API returns a list."""
        if isinstance(value, str):
            return [item for item in value.split(",") if item]
        return value


class RiskStatusUpdate(BaseModel):
    status: RiskStatus
    reason: Optional[str] = Field(default=None, max_length=1000)


class RiskRecomputeRequest(BaseModel):
    use_external_ai: bool = False


class MachineLearningInfo(BaseModel):
    """What the unsupervised model is, and whether it is currently fitted."""

    available: bool
    model: str
    algorithm: str
    trees: int
    subsample_size: int
    features: int
    feature_names: List[str] = Field(default_factory=list)
    trained_on_records: int
    flag_threshold: float
    flag_percentile: float = 97.0
    contamination: float = 0.03
    minimum_cohort: int
    supervised: bool
    notes: str


class RiskEngineInfo(BaseModel):
    """Honest description of which analysis layers are actually available."""

    engine_version: str
    rule_based_enabled: bool
    statistical_enabled: bool
    machine_learning_enabled: bool = False
    machine_learning: Optional[MachineLearningInfo] = None
    duplicate_detection_backend: str
    external_ai_enabled: bool
    external_ai_provider: Optional[str] = None
    external_ai_model: Optional[str] = None
    notes: str


class FlaggedProject(BaseModel):
    project_id: int
    project_code: str
    title: str
    district: str
    category: str
    mp_name: str
    allocated_amount: float
    spent_amount: float
    progress_percent: float
    risk_score: float
    risk_level: RiskLevel
    primary_category: Optional[RiskCategory] = None
    top_factors: List[str] = Field(default_factory=list)
    review_status: str
