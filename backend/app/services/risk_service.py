"""Persisting risk assessments and managing mitigation actions."""
from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Dict, List, Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundError
from app.database.base import utcnow
from app.models.activity import ActivityLog  # noqa: F401  (mapper registration)
from app.core.enums import (
    ActivityType,
    AnalysisSource,
    Impact,
    Likelihood,
    MitigationStatus,
    RiskStatus,
)
from app.models.project import Project
from app.models.risk import MitigationAction, RiskAssessment, RiskFactor
from app.models.user import User
from app.risk import IsolationForestModel, assess_project, build_cohort_stats, fit_anomaly_model
from app.risk.mitigation_templates import template_for
from app.risk.types import CohortStats
from app.schemas.risk import RiskAssessmentOut
from app.services import activity_service

logger = logging.getLogger("mplad.risk.service")


PEER_LIMIT = 150


def _peer_projects(db: Session, project: Project) -> List[Project]:
    """Same-district peers are the meaningful comparison set for duplicates."""
    stmt = (
        select(Project)
        .where(Project.district == project.district, Project.id != project.id)
        .limit(PEER_LIMIT)
    )
    return list(db.execute(stmt).scalars().all())


def build_peer_index(db: Session) -> Dict[str, List[Project]]:
    """District -> peer list, so a batch run does one query instead of N."""
    index: Dict[str, List[Project]] = {}
    for project in db.execute(select(Project)).scalars().all():
        bucket = index.setdefault(project.district, [])
        if len(bucket) < PEER_LIMIT:
            bucket.append(project)
    return index


def load_cohort_stats(db: Session) -> CohortStats:
    projects = db.execute(select(Project)).scalars().all()
    return build_cohort_stats(projects)


#: The fitted isolation forest, cached between requests. Fitting walks the whole
#: project table, so a single-project assessment must not repeat it.
_anomaly_model: Optional[IsolationForestModel] = None
_anomaly_model_size: int = 0


def load_anomaly_model(db: Session, *, refit: bool = False) -> Optional[IsolationForestModel]:
    """Return the cached model, refitting when the population has moved.

    The model is unsupervised, so "training" is just fitting to whatever is in
    the database. It is refitted when the record count changes by more than 5%,
    or on demand after a batch import.
    """
    global _anomaly_model, _anomaly_model_size

    count = int(db.execute(select(func.count()).select_from(Project)).scalar_one())
    drifted = _anomaly_model_size == 0 or abs(count - _anomaly_model_size) > max(
        1, _anomaly_model_size * 0.05
    )
    if _anomaly_model is None or refit or drifted:
        projects = db.execute(select(Project)).scalars().all()
        _anomaly_model = fit_anomaly_model(projects)
        _anomaly_model_size = count
        if _anomaly_model is not None:
            logger.info(
                "Isolation forest fitted on %d records (%d trees).",
                len(_anomaly_model.training_scores),
                _anomaly_model.n_trees,
            )
    return _anomaly_model


def run_assessment(
    db: Session,
    project: Project,
    *,
    actor: Optional[User] = None,
    use_external_ai: bool = False,
    cohort_stats: Optional[CohortStats] = None,
    peers: Optional[Sequence[Project]] = None,
    anomaly_model: Optional[IsolationForestModel] = None,
    open_citizen_reports: int = 0,
    seed_mitigations: bool = True,
    commit: bool = True,
) -> RiskAssessment:
    """Compute and persist a new current assessment for `project`.

    `cohort_stats` and `peers` may be supplied by a batch caller so that a
    scheme-wide re-scoring run does not re-query the peer group per project.
    """
    stats = cohort_stats if cohort_stats is not None else load_cohort_stats(db)
    peer_list = list(peers) if peers is not None else _peer_projects(db, project)
    model = anomaly_model if anomaly_model is not None else load_anomaly_model(db)

    result = assess_project(
        project,
        peers=peer_list,
        cohort_stats=stats,
        anomaly_model=model,
        open_citizen_reports=open_citizen_reports,
        use_external_ai=use_external_ai,
    )

    previous = db.execute(
        select(RiskAssessment).where(
            RiskAssessment.project_id == project.id, RiskAssessment.is_current.is_(True)
        )
    ).scalars().all()
    previous_level = previous[0].risk_level.value if previous else None
    carried_over: List[MitigationAction] = []
    for old in previous:
        old.is_current = False
        # Keep unresolved, human-authored mitigation work visible.
        for action in old.mitigations:
            if action.status != MitigationStatus.RESOLVED and not action.is_system_recommended:
                carried_over.append(action)

    assessment = RiskAssessment(
        project_id=project.id,
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        likelihood=Likelihood(result.likelihood),
        impact=Impact(result.impact),
        primary_category=result.primary_category,
        status=RiskStatus.OPEN if result.factors else RiskStatus.CLOSED,
        summary=result.summary,
        explanation=result.explanation,
        recommended_actions=result.recommended_actions,
        analysis_sources=",".join(sorted({s.value for s in result.sources})),
        engine_version=result.engine_version,
        ai_model_used=result.ai_model_used,
        ai_narrative=result.ai_narrative,
        data_completeness_percent=result.data_completeness_percent,
        assessed_at=utcnow(),
        assessed_by_id=actor.id if actor else None,
        is_current=True,
    )
    db.add(assessment)
    db.flush()

    for factor in result.factors:
        db.add(
            RiskFactor(
                assessment_id=assessment.id,
                code=factor.code,
                title=factor.title,
                category=factor.category,
                severity=factor.severity,
                source=factor.source,
                contribution=factor.contribution,
                weight=factor.weight,
                detected_indicator=factor.detected_indicator,
                evidence=factor.evidence,
                explanation=factor.explanation,
                recommended_action=factor.recommended_action,
                metric_name=factor.metric_name,
                metric_value=factor.metric_value,
                threshold_value=factor.threshold_value,
                reference_project_code=factor.reference_project_code,
            )
        )

    if seed_mitigations:
        for factor in result.factors:
            template = template_for(factor)
            action_text = template.action if template else factor.recommended_action
            if not action_text:
                continue
            db.add(
                MitigationAction(
                    assessment_id=assessment.id,
                    project_id=project.id,
                    risk_factor_code=factor.code,
                    action=action_text,
                    responsible_party=template.responsible_party if template else factor.responsible_party,
                    status=MitigationStatus.OPEN,
                    priority=template.priority if template else 2,
                    due_date=date.today() + timedelta(days=template.due_in_days if template else 21),
                    created_by_name="Risk Engine",
                    is_system_recommended=True,
                )
            )

    for action in carried_over:
        action.assessment_id = assessment.id

    activity_service.log(
        db,
        project_id=project.id,
        activity_type=ActivityType.RISK_ASSESSED,
        summary=(
            f"Risk assessment generated: {result.risk_level.value} "
            f"(score {result.risk_score:.1f}/100, {len(result.factors)} indicator(s))."
        ),
        actor=actor,
        detail=f"Analysis layers: {', '.join(sorted({s.value for s in result.sources}))}.",
    )
    if previous_level and previous_level != result.risk_level.value:
        activity_service.log(
            db,
            project_id=project.id,
            activity_type=ActivityType.RISK_LEVEL_CHANGED,
            summary=f"Risk level changed from {previous_level} to {result.risk_level.value}.",
            actor=actor,
            from_value=previous_level,
            to_value=result.risk_level.value,
        )

    if commit:
        db.commit()
        db.refresh(assessment)
    return assessment


def get_current(db: Session, project_id: int) -> Optional[RiskAssessment]:
    stmt = (
        select(RiskAssessment)
        .where(RiskAssessment.project_id == project_id, RiskAssessment.is_current.is_(True))
        .options(selectinload(RiskAssessment.factors), selectinload(RiskAssessment.mitigations))
    )
    return db.execute(stmt).scalars().first()


def history(db: Session, project_id: int, limit: int = 20) -> List[RiskAssessment]:
    stmt = (
        select(RiskAssessment)
        .where(RiskAssessment.project_id == project_id)
        .options(selectinload(RiskAssessment.factors))
        .order_by(RiskAssessment.assessed_at.desc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().unique().all())


def to_out(assessment: RiskAssessment) -> RiskAssessmentOut:
    return RiskAssessmentOut.model_validate(assessment, from_attributes=True)


def get_mitigation_or_404(db: Session, mitigation_id: int) -> MitigationAction:
    action = db.get(MitigationAction, mitigation_id)
    if action is None:
        raise NotFoundError(f"Mitigation action {mitigation_id} was not found.")
    return action


def resolve_mitigation(db: Session, action: MitigationAction, actor: User) -> MitigationAction:
    action.status = MitigationStatus.RESOLVED
    action.resolved_at = utcnow()
    action.resolved_by_name = actor.full_name
    activity_service.log(
        db,
        project_id=action.project_id,
        activity_type=ActivityType.MITIGATION_RESOLVED,
        summary=f"Mitigation action marked resolved: {action.action[:160]}",
        actor=actor,
        to_value=MitigationStatus.RESOLVED.value,
    )
    db.commit()
    db.refresh(action)
    return action


def sources_available() -> Sequence[str]:
    return [s.value for s in AnalysisSource]
