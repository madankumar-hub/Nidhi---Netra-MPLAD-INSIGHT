"""Risk analysis and mitigation APIs. Internal roles only (FR3, FR8-FR11)."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import require_internal, require_reviewer
from app.core.exceptions import NotFoundError
from app.database.session import get_db
from app.core.enums import ActivityType, MitigationStatus
from app.models.risk import MitigationAction
from app.models.user import User
from app.risk import engine_info
from app.schemas.common import MessageResponse
from app.schemas.risk import (
    MitigationActionCreate,
    MitigationActionOut,
    MitigationActionUpdate,
    RiskAssessmentOut,
    RiskEngineInfo,
    RiskRecomputeRequest,
    RiskStatusUpdate,
)
from app.services import activity_service, project_service, risk_service

router = APIRouter(prefix="/admin", tags=["Admin - Risk"])


@router.get("/risk-engine", response_model=RiskEngineInfo)
def get_engine_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_internal),
) -> RiskEngineInfo:
    """Reports which analysis layers are actually active on this deployment."""
    return RiskEngineInfo(**engine_info(risk_service.load_anomaly_model(db)))


@router.get("/projects/{project_id}/risk", response_model=RiskAssessmentOut)
def get_risk(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_internal),
) -> RiskAssessmentOut:
    project = project_service.get_project_or_404(db, project_id, with_details=True)
    assessment = risk_service.get_current(db, project_id)
    if assessment is None:
        open_reports = project_service.open_citizen_report_count(db, project_id)
        assessment = risk_service.run_assessment(
            db, project, actor=current_user, open_citizen_reports=open_reports
        )
    return risk_service.to_out(assessment)


@router.post("/projects/{project_id}/risk/recompute", response_model=RiskAssessmentOut)
def recompute_risk(
    project_id: int,
    payload: RiskRecomputeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> RiskAssessmentOut:
    project = project_service.get_project_or_404(db, project_id, with_details=True)
    open_reports = project_service.open_citizen_report_count(db, project_id)
    assessment = risk_service.run_assessment(
        db,
        project,
        actor=current_user,
        use_external_ai=payload.use_external_ai,
        open_citizen_reports=open_reports,
    )
    return risk_service.to_out(assessment)


@router.get("/projects/{project_id}/risk/history", response_model=List[RiskAssessmentOut])
def risk_history(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_internal),
    limit: int = Query(default=20, ge=1, le=100),
) -> List[RiskAssessmentOut]:
    return [risk_service.to_out(a) for a in risk_service.history(db, project_id, limit)]


@router.patch("/projects/{project_id}/risk/status", response_model=RiskAssessmentOut)
def update_risk_status(
    project_id: int,
    payload: RiskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> RiskAssessmentOut:
    assessment = risk_service.get_current(db, project_id)
    if assessment is None:
        raise NotFoundError("No current risk assessment exists for this project.")
    previous = assessment.status
    assessment.status = payload.status
    activity_service.log(
        db,
        project_id=project_id,
        activity_type=ActivityType.RISK_STATUS_CHANGED,
        summary=f"Risk status changed: {previous.value} -> {payload.status.value}.",
        actor=current_user,
        detail=payload.reason,
        from_value=previous.value,
        to_value=payload.status.value,
    )
    db.commit()
    db.refresh(assessment)
    return risk_service.to_out(assessment)


# ---------------------------------------------------------------------------
# Mitigation tracker
# ---------------------------------------------------------------------------
@router.get("/projects/{project_id}/mitigation", response_model=List[MitigationActionOut])
def list_mitigation(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_internal),
) -> List[MitigationActionOut]:
    stmt = (
        select(MitigationAction)
        .where(MitigationAction.project_id == project_id)
        .order_by(MitigationAction.status, MitigationAction.priority, MitigationAction.created_at)
    )
    return [
        MitigationActionOut.model_validate(a, from_attributes=True)
        for a in db.execute(stmt).scalars().all()
    ]


@router.post(
    "/projects/{project_id}/mitigation",
    response_model=MitigationActionOut,
    status_code=status.HTTP_201_CREATED,
)
def add_mitigation(
    project_id: int,
    payload: MitigationActionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> MitigationActionOut:
    project = project_service.get_project_or_404(db, project_id)
    assessment = risk_service.get_current(db, project_id)
    if assessment is None:
        assessment = risk_service.run_assessment(db, project, actor=current_user)
    action = MitigationAction(
        assessment_id=assessment.id,
        project_id=project_id,
        risk_factor_code=payload.risk_factor_code,
        action=payload.action,
        responsible_party=payload.responsible_party,
        status=payload.status,
        priority=payload.priority,
        due_date=payload.due_date,
        notes=payload.notes,
        created_by_id=current_user.id,
        created_by_name=current_user.full_name,
        is_system_recommended=False,
    )
    db.add(action)
    activity_service.log(
        db,
        project_id=project_id,
        activity_type=ActivityType.MITIGATION_ADDED,
        summary=f"Mitigation action added: {payload.action[:160]}",
        actor=current_user,
        detail=f"Responsible party: {payload.responsible_party or 'unassigned'}.",
    )
    db.commit()
    db.refresh(action)
    return MitigationActionOut.model_validate(action, from_attributes=True)


@router.patch("/mitigation/{mitigation_id}", response_model=MitigationActionOut)
def update_mitigation(
    mitigation_id: int,
    payload: MitigationActionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> MitigationActionOut:
    action = risk_service.get_mitigation_or_404(db, mitigation_id)
    previous_status = action.status
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(action, field, value)
    if payload.status is not None and payload.status != previous_status:
        if payload.status == MitigationStatus.RESOLVED:
            from app.database.base import utcnow

            action.resolved_at = utcnow()
            action.resolved_by_name = current_user.full_name
        activity_service.log(
            db,
            project_id=action.project_id,
            activity_type=(
                ActivityType.MITIGATION_RESOLVED
                if payload.status == MitigationStatus.RESOLVED
                else ActivityType.MITIGATION_UPDATED
            ),
            summary=f"Mitigation status changed: {previous_status.value} -> {payload.status.value}.",
            actor=current_user,
            from_value=previous_status.value,
            to_value=payload.status.value,
        )
    else:
        activity_service.log(
            db,
            project_id=action.project_id,
            activity_type=ActivityType.MITIGATION_UPDATED,
            summary=f"Mitigation action updated: {action.action[:160]}",
            actor=current_user,
        )
    db.commit()
    db.refresh(action)
    return MitigationActionOut.model_validate(action, from_attributes=True)


@router.post("/mitigation/{mitigation_id}/resolve", response_model=MitigationActionOut)
def resolve_mitigation(
    mitigation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
) -> MitigationActionOut:
    action = risk_service.get_mitigation_or_404(db, mitigation_id)
    action = risk_service.resolve_mitigation(db, action, current_user)
    return MitigationActionOut.model_validate(action, from_attributes=True)


@router.post("/risk/recompute-all", response_model=MessageResponse)
def recompute_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer),
    limit: int = Query(default=500, ge=1, le=10000),
) -> MessageResponse:
    """Batch re-scoring (NFR: risk scoring runs as a batch job, not inline)."""
    from app.models.project import Project

    stats = risk_service.load_cohort_stats(db)
    peer_index = risk_service.build_peer_index(db)
    model = risk_service.load_anomaly_model(db, refit=True)
    projects = db.execute(select(Project).limit(limit)).scalars().all()
    for project in projects:
        open_reports = project_service.open_citizen_report_count(db, project.id)
        risk_service.run_assessment(
            db,
            project,
            actor=current_user,
            cohort_stats=stats,
            peers=peer_index.get(project.district, []),
            anomaly_model=model,
            open_citizen_reports=open_reports,
            commit=False,
        )
    db.commit()
    return MessageResponse(message=f"Risk assessment refreshed for {len(projects)} project(s).")
