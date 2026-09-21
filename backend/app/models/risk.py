from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.core.enums import (
    AnalysisSource,
    Impact,
    Likelihood,
    MitigationStatus,
    RiskCategory,
    RiskLevel,
    RiskStatus,
)


class RiskAssessment(Base, TimestampMixin):
    """A full, explainable risk assessment for one project at one point in time.

    Internal-only. Citizens receive a derived public indicator instead
    (see `PublicRiskIndicator`, FR6).
    """

    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )

    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0-100
    risk_level: Mapped[RiskLevel] = mapped_column(
        SAEnum(RiskLevel, native_enum=False, length=16), default=RiskLevel.LOW, nullable=False
    )
    likelihood: Mapped[Likelihood] = mapped_column(
        SAEnum(Likelihood, native_enum=False, length=24), default=Likelihood.UNLIKELY, nullable=False
    )
    impact: Mapped[Impact] = mapped_column(
        SAEnum(Impact, native_enum=False, length=24), default=Impact.MINOR, nullable=False
    )
    primary_category: Mapped[Optional[RiskCategory]] = mapped_column(
        SAEnum(RiskCategory, native_enum=False, length=40)
    )
    status: Mapped[RiskStatus] = mapped_column(
        SAEnum(RiskStatus, native_enum=False, length=24), default=RiskStatus.OPEN, nullable=False
    )

    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    recommended_actions: Mapped[str] = mapped_column(Text, nullable=False, default="")

    #: Comma-separated `AnalysisSource` values that actually contributed.
    analysis_sources: Mapped[str] = mapped_column(
        String(120), default=AnalysisSource.RULE_BASED.value, nullable=False
    )
    engine_version: Mapped[str] = mapped_column(String(40), default="rule-engine-1.0", nullable=False)
    ai_model_used: Mapped[Optional[str]] = mapped_column(String(80))
    ai_narrative: Mapped[Optional[str]] = mapped_column(Text)

    #: Confidence in the deterministic computation given the data available
    #: (data completeness), NOT a claim of predictive accuracy.
    data_completeness_percent: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)

    assessed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    assessed_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    project: Mapped["Project"] = relationship(back_populates="risk_assessments")
    factors: Mapped[List["RiskFactor"]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="RiskFactor.contribution.desc()",
    )
    mitigations: Mapped[List["MitigationAction"]] = relationship(
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="MitigationAction.created_at",
    )

    @property
    def source_list(self) -> List[str]:
        return [s for s in (self.analysis_sources or "").split(",") if s]


class RiskFactor(Base, TimestampMixin):
    """One detected indicator that contributed to the overall risk score.

    Every factor records the *observed data* that triggered it, so the admin
    UI can answer: what is the risk, why was it detected, what data caused it.
    """

    __tablename__ = "risk_factors"

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("risk_assessments.id", ondelete="CASCADE"), index=True, nullable=False
    )

    code: Mapped[str] = mapped_column(String(60), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[RiskCategory] = mapped_column(
        SAEnum(RiskCategory, native_enum=False, length=40), nullable=False
    )
    severity: Mapped[RiskLevel] = mapped_column(
        SAEnum(RiskLevel, native_enum=False, length=16), nullable=False
    )
    source: Mapped[AnalysisSource] = mapped_column(
        SAEnum(AnalysisSource, native_enum=False, length=24),
        default=AnalysisSource.RULE_BASED,
        nullable=False,
    )

    #: Points this factor added to the 0-100 risk score.
    contribution: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    detected_indicator: Mapped[str] = mapped_column(Text, nullable=False, default="")
    evidence: Mapped[str] = mapped_column(Text, nullable=False, default="")
    explanation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False, default="")

    #: Machine-readable values behind the finding, e.g. {"progress": 12.0}
    metric_name: Mapped[Optional[str]] = mapped_column(String(80))
    metric_value: Mapped[Optional[float]] = mapped_column(Float)
    threshold_value: Mapped[Optional[float]] = mapped_column(Float)
    reference_project_code: Mapped[Optional[str]] = mapped_column(String(40))

    assessment: Mapped["RiskAssessment"] = relationship(back_populates="factors")


class MitigationAction(Base, TimestampMixin):
    """A tracked, assignable action taken against a risk."""

    __tablename__ = "mitigation_actions"

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(
        ForeignKey("risk_assessments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    risk_factor_code: Mapped[Optional[str]] = mapped_column(String(60))

    action: Mapped[str] = mapped_column(Text, nullable=False)
    responsible_party: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    status: Mapped[MitigationStatus] = mapped_column(
        SAEnum(MitigationStatus, native_enum=False, length=24),
        default=MitigationStatus.OPEN,
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, default=2, nullable=False)  # 1 high .. 3 low
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_by_name: Mapped[str] = mapped_column(String(160), default="System", nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    resolved_by_name: Mapped[Optional[str]] = mapped_column(String(160))
    #: True when the action text came from the engine's recommendation library.
    is_system_recommended: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    assessment: Mapped["RiskAssessment"] = relationship(back_populates="mitigations")
