"""Deterministic metric computation - no heuristics, just arithmetic."""
from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Optional

from app.core.enums import ProjectStatus
from app.risk.types import ProjectMetrics

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from app.models.project import Project

REQUIRED_FIELDS = (
    "start_date",
    "planned_end_date",
    "allocated_amount",
    "spent_amount",
    "progress_percent",
    "executing_agency",
    "category",
    "description",
)


def _pct(numerator: float, denominator: float) -> Optional[float]:
    if not denominator:
        return None
    return round(numerator / denominator * 100.0, 2)


def compute_metrics(project: Project, as_of: Optional[date] = None) -> ProjectMetrics:
    today = as_of or date.today()
    m = ProjectMetrics(as_of=today)

    m.progress_percent = float(project.progress_percent or 0.0)
    m.utilization_percent = float(project.utilization_percent or 0.0)

    start = project.start_date
    end = project.planned_end_date

    if start and end and end > start:
        m.duration_days = (end - start).days
        m.elapsed_days = max((today - start).days, 0)
        m.days_remaining = (end - today).days
        m.time_elapsed_percent = round(min(m.elapsed_days / m.duration_days * 100.0, 100.0), 2)
        # A straight-line schedule baseline. Where the record carries an
        # explicit planned progress figure, that authoritative value wins.
        if project.planned_progress_percent is not None:
            m.expected_progress_percent = float(project.planned_progress_percent)
        else:
            m.expected_progress_percent = m.time_elapsed_percent
        m.expected_utilization_percent = m.time_elapsed_percent
        m.schedule_variance = round(m.progress_percent - m.expected_progress_percent, 2)
        m.is_overdue = (
            today > end
            and project.status not in (ProjectStatus.COMPLETED, ProjectStatus.CANCELLED)
        )
    elif end:
        m.days_remaining = (end - today).days
        m.is_overdue = (
            today > end
            and project.status not in (ProjectStatus.COMPLETED, ProjectStatus.CANCELLED)
        )

    m.utilization_progress_gap = round(m.utilization_percent - m.progress_percent, 2)

    baseline_cost = project.estimated_cost or project.allocated_amount
    if baseline_cost:
        overrun = _pct(project.spent_amount - baseline_cost, baseline_cost)
        m.cost_overrun_percent = overrun

    if project.progress_updates:
        last = max(u.updated_on for u in project.progress_updates)
        m.days_since_progress_update = max((today - last).days, 0)
    if project.fund_updates:
        last_f = max(u.updated_on for u in project.fund_updates)
        m.days_since_fund_update = max((today - last_f).days, 0)

    missing = []
    for fname in REQUIRED_FIELDS:
        value = getattr(project, fname, None)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(fname)
    m.missing_fields = missing
    m.data_completeness_percent = round(
        (len(REQUIRED_FIELDS) - len(missing)) / len(REQUIRED_FIELDS) * 100.0, 1
    )
    return m
