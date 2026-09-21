"""Aggregations for the admin dashboard and the public statistics strip.

Every figure is computed from the database. Nothing is hardcoded.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.citizen_report import CitizenReport
from app.core.enums import (
    ACTIVE_STATUSES,
    CitizenReportStatus,
    MitigationStatus,
    ProjectStatus,
    ReviewStatus,
    RiskLevel,
)
from app.models.project import Project
from app.models.risk import MitigationAction, RiskAssessment, RiskFactor
from app.models.tracking import FundUpdate
from app.schemas.analytics import (
    AdminAnalytics,
    DashboardSummary,
    KeyValueAmount,
    KeyValueCount,
    PublicAnalytics,
    PublicSummary,
    TrendPoint,
)


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _count(db: Session, *conditions) -> int:
    stmt = select(func.count()).select_from(Project)
    for condition in conditions:
        stmt = stmt.where(condition)
    return int(db.execute(stmt).scalar_one())


def _sum(db: Session, column, *conditions) -> float:
    stmt = select(func.coalesce(func.sum(column), 0.0)).select_from(Project)
    for condition in conditions:
        stmt = stmt.where(condition)
    return float(db.execute(stmt).scalar_one() or 0.0)


def _group_counts(db: Session, column) -> List[KeyValueCount]:
    stmt = select(column, func.count()).group_by(column).order_by(func.count().desc())
    return [
        KeyValueCount(label=str(getattr(value, "value", value)), value=int(count))
        for value, count in db.execute(stmt).all()
        if value is not None
    ]


def _group_amounts(db: Session, column, limit: Optional[int] = None) -> List[KeyValueAmount]:
    stmt = (
        select(
            column,
            func.coalesce(func.sum(Project.allocated_amount), 0.0),
            func.coalesce(func.sum(Project.spent_amount), 0.0),
            func.count(),
        )
        .group_by(column)
        .order_by(func.coalesce(func.sum(Project.allocated_amount), 0.0).desc())
    )
    if limit:
        stmt = stmt.limit(limit)
    out: List[KeyValueAmount] = []
    for value, allocated, spent, count in db.execute(stmt).all():
        if value is None:
            continue
        allocated = float(allocated or 0.0)
        spent = float(spent or 0.0)
        out.append(
            KeyValueAmount(
                label=str(getattr(value, "value", value)),
                allocated=round(allocated, 2),
                spent=round(spent, 2),
                utilization_percent=round(spent / allocated * 100, 2) if allocated else 0.0,
                count=int(count),
            )
        )
    return out


def _distribution(db: Session, column, buckets: List[Tuple[str, float, float]]) -> List[KeyValueCount]:
    out: List[KeyValueCount] = []
    for label, low, high in buckets:
        stmt = select(func.count()).select_from(Project).where(column >= low, column < high)
        out.append(KeyValueCount(label=label, value=int(db.execute(stmt).scalar_one())))
    return out


def _utilization_distribution(db: Session) -> List[KeyValueCount]:
    buckets = [("0-25%", 0, 25), ("25-50%", 25, 50), ("50-75%", 50, 75), ("75-100%", 75, 100.01), ("Over 100%", 100.01, 10_000)]
    counters = {label: 0 for label, _, _ in buckets}
    rows = db.execute(select(Project.allocated_amount, Project.spent_amount)).all()
    for allocated, spent in rows:
        allocated = float(allocated or 0.0)
        spent = float(spent or 0.0)
        pct = (spent / allocated * 100) if allocated else 0.0
        for label, low, high in buckets:
            if low <= pct < high:
                counters[label] += 1
                break
    return [KeyValueCount(label=label, value=counters[label]) for label, _, _ in buckets]


def _yearly_trend(db: Session) -> List[TrendPoint]:
    stmt = (
        select(
            Project.sanction_year,
            func.coalesce(func.sum(Project.allocated_amount), 0.0),
            func.coalesce(func.sum(Project.spent_amount), 0.0),
            func.count(),
            func.coalesce(func.avg(Project.progress_percent), 0.0),
        )
        .group_by(Project.sanction_year)
        .order_by(Project.sanction_year)
    )
    return [
        TrendPoint(
            period=str(year),
            allocated=round(float(allocated or 0.0), 2),
            spent=round(float(spent or 0.0), 2),
            projects=int(count),
            avg_progress=round(float(avg or 0.0), 2),
        )
        for year, allocated, spent, count, avg in db.execute(stmt).all()
    ]


def _spending_trend(db: Session, months: int = 24) -> List[TrendPoint]:
    """Actual monthly expenditure, taken from the fund-update trail."""
    rows = db.execute(
        select(FundUpdate.updated_on, FundUpdate.expenditure_amount, FundUpdate.released_amount)
    ).all()
    buckets: Dict[str, Dict[str, float]] = defaultdict(lambda: {"spent": 0.0, "released": 0.0, "n": 0.0})
    for updated_on, expenditure, released in rows:
        if updated_on is None:
            continue
        key = updated_on.strftime("%Y-%m")
        buckets[key]["spent"] += float(expenditure or 0.0)
        buckets[key]["released"] += float(released or 0.0)
        buckets[key]["n"] += 1
    periods = sorted(buckets)[-months:]
    return [
        TrendPoint(
            period=period,
            allocated=round(buckets[period]["released"], 2),
            spent=round(buckets[period]["spent"], 2),
            projects=int(buckets[period]["n"]),
            avg_progress=0.0,
        )
        for period in periods
    ]


def _risk_counts(db: Session) -> Dict[str, int]:
    stmt = (
        select(RiskAssessment.risk_level, func.count())
        .where(RiskAssessment.is_current.is_(True))
        .group_by(RiskAssessment.risk_level)
    )
    return {str(level.value): int(count) for level, count in db.execute(stmt).all()}


def dashboard_summary(db: Session) -> DashboardSummary:
    total = _count(db)
    total_allocated = _sum(db, Project.allocated_amount)
    total_spent = _sum(db, Project.spent_amount)
    risk_counts = _risk_counts(db)

    open_risk_projects = int(
        db.execute(
            select(func.count(func.distinct(RiskFactor.assessment_id)))
            .select_from(RiskFactor)
            .join(RiskAssessment, RiskAssessment.id == RiskFactor.assessment_id)
            .where(RiskAssessment.is_current.is_(True))
        ).scalar_one()
    )
    open_mitigations = int(
        db.execute(
            select(func.count()).select_from(MitigationAction).where(
                MitigationAction.status != MitigationStatus.RESOLVED
            )
        ).scalar_one()
    )
    citizen_open = int(
        db.execute(
            select(func.count()).select_from(CitizenReport).where(
                CitizenReport.status.in_(
                    [CitizenReportStatus.SUBMITTED, CitizenReportStatus.UNDER_REVIEW]
                )
            )
        ).scalar_one()
    )
    avg_progress = float(
        db.execute(select(func.coalesce(func.avg(Project.progress_percent), 0.0))).scalar_one() or 0.0
    )
    avg_risk = float(
        db.execute(
            select(func.coalesce(func.avg(RiskAssessment.risk_score), 0.0)).where(
                RiskAssessment.is_current.is_(True)
            )
        ).scalar_one()
        or 0.0
    )
    overdue = _count(
        db,
        Project.planned_end_date < date.today(),
        Project.status.notin_([ProjectStatus.COMPLETED, ProjectStatus.CANCELLED]),
    )

    return DashboardSummary(
        total_projects=total,
        active_projects=_count(db, Project.status.in_(list(ACTIVE_STATUSES))),
        completed_projects=_count(db, Project.status == ProjectStatus.COMPLETED),
        delayed_projects=_count(db, Project.status == ProjectStatus.DELAYED),
        not_started_projects=_count(db, Project.status == ProjectStatus.NOT_STARTED),
        pending_review_projects=_count(db, Project.review_status == ReviewStatus.PENDING_REVIEW),
        escalated_projects=_count(db, Project.review_status == ReviewStatus.ESCALATED),
        projects_with_open_risks=open_risk_projects,
        high_risk_projects=risk_counts.get(RiskLevel.HIGH.value, 0),
        critical_risk_projects=risk_counts.get(RiskLevel.CRITICAL.value, 0),
        open_mitigations=open_mitigations,
        overdue_projects=overdue,
        citizen_reports_open=citizen_open,
        total_allocated=round(total_allocated, 2),
        total_spent=round(total_spent, 2),
        total_remaining=round(max(total_allocated - total_spent, 0.0), 2),
        utilization_percent=round(total_spent / total_allocated * 100, 2) if total_allocated else 0.0,
        average_progress=round(avg_progress, 2),
        average_risk_score=round(avg_risk, 2),
    )


def admin_analytics(db: Session) -> AdminAnalytics:
    risk_counts = _risk_counts(db)
    progress_buckets = [
        ("0-20%", 0, 20),
        ("20-40%", 20, 40),
        ("40-60%", 40, 60),
        ("60-80%", 60, 80),
        ("80-100%", 80, 100.01),
    ]
    risk_category = [
        KeyValueCount(label=str(getattr(value, "value", value)), value=int(count))
        for value, count in db.execute(
            select(RiskFactor.category, func.count())
            .join(RiskAssessment, RiskAssessment.id == RiskFactor.assessment_id)
            .where(RiskAssessment.is_current.is_(True))
            .group_by(RiskFactor.category)
            .order_by(func.count().desc())
        ).all()
        if value is not None
    ]
    top_factors = [
        KeyValueCount(label=str(title), value=int(count))
        for title, count in db.execute(
            select(RiskFactor.title, func.count())
            .join(RiskAssessment, RiskAssessment.id == RiskFactor.assessment_id)
            .where(RiskAssessment.is_current.is_(True))
            .group_by(RiskFactor.title)
            .order_by(func.count().desc())
            .limit(10)
        ).all()
    ]

    return AdminAnalytics(
        summary=dashboard_summary(db),
        by_status=_group_counts(db, Project.status),
        by_review_status=_group_counts(db, Project.review_status),
        by_risk_level=[
            KeyValueCount(label=level.value, value=risk_counts.get(level.value, 0))
            for level in RiskLevel
        ],
        by_category=_group_amounts(db, Project.category),
        by_district=_group_amounts(db, Project.district, limit=15),
        by_agency=_group_amounts(db, Project.executing_agency, limit=10),
        by_mp=_group_amounts(db, Project.mp_name, limit=10),
        progress_distribution=_distribution(db, Project.progress_percent, progress_buckets),
        utilization_distribution=_utilization_distribution(db),
        yearly_trend=_yearly_trend(db),
        spending_trend=_spending_trend(db),
        risk_category_distribution=risk_category,
        top_risk_factors=top_factors,
        generated_at=_now_iso(),
    )


def public_analytics(db: Session) -> PublicAnalytics:
    total_allocated = _sum(db, Project.allocated_amount)
    total_spent = _sum(db, Project.spent_amount)
    districts = int(db.execute(select(func.count(func.distinct(Project.district)))).scalar_one())
    categories = int(db.execute(select(func.count(func.distinct(Project.category)))).scalar_one())
    avg_progress = float(
        db.execute(select(func.coalesce(func.avg(Project.progress_percent), 0.0))).scalar_one() or 0.0
    )
    summary = PublicSummary(
        total_projects=_count(db),
        completed_projects=_count(db, Project.status == ProjectStatus.COMPLETED),
        ongoing_projects=_count(db, Project.status.in_(list(ACTIVE_STATUSES))),
        districts_covered=districts,
        categories_covered=categories,
        total_allocated=round(total_allocated, 2),
        total_spent=round(total_spent, 2),
        utilization_percent=round(total_spent / total_allocated * 100, 2) if total_allocated else 0.0,
        average_progress=round(avg_progress, 2),
    )
    return PublicAnalytics(
        summary=summary,
        by_status=_group_counts(db, Project.status),
        by_category=_group_amounts(db, Project.category),
        by_district=_group_amounts(db, Project.district, limit=15),
        yearly_trend=_yearly_trend(db),
        generated_at=_now_iso(),
    )
