"""Citizen community-feedback reports (FR7)."""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.citizen_report import CitizenReport
from app.core.enums import ActivityType, CitizenReportStatus
from app.models.user import User
from app.schemas.workflow import CitizenReportCreate, CitizenReportTriage
from app.services import activity_service


def create_report(
    db: Session, project_id: int, payload: CitizenReportCreate, user: User
) -> CitizenReport:
    report = CitizenReport(
        project_id=project_id,
        reporter_id=user.id,
        reporter_name=user.full_name,
        category=payload.category,
        description=payload.description,
        status=CitizenReportStatus.SUBMITTED,
    )
    db.add(report)
    activity_service.log(
        db,
        project_id=project_id,
        activity_type=ActivityType.CITIZEN_REPORT_FILED,
        summary=f"Citizen report filed: {payload.category.value}.",
        actor=user,
        detail=payload.description[:500],
    )
    db.commit()
    db.refresh(report)
    return report


def list_reports_for_user(db: Session, project_id: int, user_id: int) -> List[CitizenReport]:
    stmt = (
        select(CitizenReport)
        .where(CitizenReport.project_id == project_id, CitizenReport.reporter_id == user_id)
        .order_by(CitizenReport.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def list_reports(
    db: Session,
    project_id: Optional[int] = None,
    report_status: Optional[CitizenReportStatus] = None,
    limit: int = 200,
) -> List[CitizenReport]:
    stmt = select(CitizenReport)
    if project_id:
        stmt = stmt.where(CitizenReport.project_id == project_id)
    if report_status:
        stmt = stmt.where(CitizenReport.status == report_status)
    stmt = stmt.order_by(CitizenReport.created_at.desc()).limit(limit)
    return list(db.execute(stmt).scalars().all())


def get_or_404(db: Session, report_id: int) -> CitizenReport:
    report = db.get(CitizenReport, report_id)
    if report is None:
        raise NotFoundError(f"Citizen report {report_id} was not found.")
    return report


def triage(db: Session, report: CitizenReport, payload: CitizenReportTriage, actor: User) -> CitizenReport:
    previous = report.status
    report.status = payload.status
    if payload.official_response is not None:
        report.official_response = payload.official_response
    activity_service.log(
        db,
        project_id=report.project_id,
        activity_type=ActivityType.CITIZEN_REPORT_TRIAGED,
        summary=f"Citizen report status changed: {previous.value} -> {payload.status.value}.",
        actor=actor,
        detail=payload.official_response,
        from_value=previous.value,
        to_value=payload.status.value,
    )
    db.commit()
    db.refresh(report)
    return report
