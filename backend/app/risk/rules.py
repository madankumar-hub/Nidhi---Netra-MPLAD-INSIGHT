"""Deterministic, rule-based risk detection.

This layer is the backbone of the engine: it requires no external service,
no trained model and no network access, so risk analysis always works.
Every rule states plainly what it detected, which data triggered it, why
it matters and what the administrator should do next.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from app.core.enums import ProjectStatus, RiskCategory, RiskLevel
from app.risk.types import FactorResult, ProjectMetrics

if TYPE_CHECKING:  # pragma: no cover - import for type checking only
    from app.models.project import Project


def _level_from_score(score: float) -> RiskLevel:
    if score >= 75:
        return RiskLevel.CRITICAL
    if score >= 50:
        return RiskLevel.HIGH
    if score >= 25:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _fmt_money(value: Optional[float]) -> str:
    if value is None:
        return "not recorded"
    return f"Rs {value:,.2f} lakh"


def _fmt_pct(value: Optional[float]) -> str:
    return "not recorded" if value is None else f"{value:.1f}%"


# ---------------------------------------------------------------------------
# Individual rules. Each returns a FactorResult or None.
# ---------------------------------------------------------------------------
def rule_schedule_slippage(p: Project, m: ProjectMetrics) -> Optional[FactorResult]:
    if m.expected_progress_percent is None or p.status == ProjectStatus.COMPLETED:
        return None
    gap = (m.expected_progress_percent or 0) - m.progress_percent
    if gap < 10:
        return None
    raw = min(gap * 1.6, 100.0)
    return FactorResult(
        code="SCHEDULE_SLIPPAGE",
        title="Physical progress is behind the planned schedule",
        category=RiskCategory.SCHEDULE,
        severity=_level_from_score(raw),
        weight=0.22,
        raw_score=raw,
        detected_indicator=(
            f"Reported progress {_fmt_pct(m.progress_percent)} against an expected "
            f"{_fmt_pct(m.expected_progress_percent)} for the elapsed period."
        ),
        evidence=(
            f"Start {p.start_date}; planned completion {p.planned_end_date}; "
            f"{_fmt_pct(m.time_elapsed_percent)} of the sanctioned duration has elapsed "
            f"({m.elapsed_days} of {m.duration_days} days). Schedule variance "
            f"{m.schedule_variance:+.1f} percentage points."
            if m.duration_days
            else f"Schedule variance {gap:.1f} percentage points behind plan."
        ),
        explanation=(
            "Work is being executed more slowly than the sanctioned timeline assumes. "
            "If the current rate continues the work will not be completed by the planned "
            "end date, which typically triggers cost escalation and re-sanction requests."
        ),
        recommended_action=(
            "Obtain a revised milestone plan from the executing agency and confirm "
            "whether the delay is due to site, material or clearance issues."
        ),
        metric_name="schedule_variance_pp",
        metric_value=round(-gap, 2),
        threshold_value=-10.0,
    )


def rule_deadline_imminent_low_progress(p: Project, m: ProjectMetrics) -> Optional[FactorResult]:
    if m.days_remaining is None or p.status == ProjectStatus.COMPLETED:
        return None
    if m.days_remaining < 0 or m.days_remaining > 90:
        return None
    if m.progress_percent >= 80:
        return None
    shortfall = 80 - m.progress_percent
    urgency = (90 - m.days_remaining) / 90
    raw = min(shortfall * 1.1 * (0.5 + urgency), 100.0)
    return FactorResult(
        code="DEADLINE_IMMINENT_LOW_PROGRESS",
        title="Deadline approaching with substantial work outstanding",
        category=RiskCategory.COMPLETION,
        severity=_level_from_score(raw),
        weight=0.20,
        raw_score=raw,
        detected_indicator=(
            f"{m.days_remaining} days remain before the planned completion date while "
            f"progress stands at {_fmt_pct(m.progress_percent)}."
        ),
        evidence=(
            f"Planned completion {p.planned_end_date}; current progress "
            f"{_fmt_pct(m.progress_percent)}; fund utilisation "
            f"{_fmt_pct(m.utilization_percent)}."
        ),
        explanation=(
            "The remaining scope is unlikely to be delivered within the remaining time at "
            "the observed rate of execution. Late-stage compression also raises the risk "
            "of substandard work being certified as complete."
        ),
        recommended_action=(
            "Convene a completion review with the executing agency; decide between a "
            "time-extension proposal and remobilisation of resources."
        ),
        metric_name="days_remaining",
        metric_value=float(m.days_remaining),
        threshold_value=90.0,
    )


def rule_overdue_incomplete(p: Project, m: ProjectMetrics) -> Optional[FactorResult]:
    if not m.is_overdue or p.planned_end_date is None:
        return None
    days_over = max((m.as_of - p.planned_end_date).days, 0)
    raw = min(35 + days_over / 4.0, 100.0)
    return FactorResult(
        code="OVERDUE_INCOMPLETE",
        title="Project is past its planned completion date and still open",
        category=RiskCategory.SCHEDULE,
        severity=_level_from_score(raw),
        weight=0.24,
        raw_score=raw,
        detected_indicator=(
            f"Planned completion was {p.planned_end_date} - {days_over} days ago - and the "
            f"work is still recorded as '{p.status.value}' at {_fmt_pct(m.progress_percent)}."
        ),
        evidence=(
            f"Planned end date {p.planned_end_date}; today {m.as_of}; status "
            f"{p.status.value}; progress {_fmt_pct(m.progress_percent)}; unspent balance "
            f"{_fmt_money(p.remaining_amount)}."
        ),
        explanation=(
            "An overdue open work blocks the constituency entitlement from being "
            "recycled and is the single strongest predictor of eventual cost escalation "
            "in MPLAD execution data."
        ),
        recommended_action=(
            "Record a formal delay reason, set the review status to Delayed or Escalated, "
            "and obtain a dated completion commitment from the executing agency."
        ),
        metric_name="days_overdue",
        metric_value=float(days_over),
        threshold_value=0.0,
    )


def rule_status_delayed(p: Project, m: ProjectMetrics) -> Optional[FactorResult]:
    if p.status != ProjectStatus.DELAYED:
        return None
    raw = 60.0 if m.progress_percent < 50 else 40.0
    return FactorResult(
        code="STATUS_DELAYED",
        title="Work has been formally marked as Delayed",
        category=RiskCategory.SCHEDULE,
        severity=_level_from_score(raw),
        weight=0.14,
        raw_score=raw,
        detected_indicator="The execution status recorded against this work is 'Delayed'.",
        evidence=(
            f"Status {p.status.value}; progress {_fmt_pct(m.progress_percent)}; "
            f"utilisation {_fmt_pct(m.utilization_percent)}."
        ),
        explanation=(
            "A declared delay confirms that the sanctioned timeline is no longer being "
            "met and that monitoring intensity must increase."
        ),
        recommended_action=(
            "Ensure a delay note with the cause is on record and that a mitigation "
            "action with a responsible party and due date has been raised."
        ),
        metric_name="progress_percent",
        metric_value=m.progress_percent,
    )


def rule_on_hold(p: Project, m: ProjectMetrics) -> Optional[FactorResult]:
    if p.status != ProjectStatus.ON_HOLD:
        return None
    raw = 55.0
    return FactorResult(
        code="WORK_ON_HOLD",
        title="Work is suspended",
        category=RiskCategory.IMPLEMENTATION,
        severity=_level_from_score(raw),
        weight=0.12,
        raw_score=raw,
        detected_indicator="The work is recorded as 'On Hold'.",
        evidence=f"Status {p.status.value}; funds released to date {_fmt_money(p.spent_amount)}.",
        explanation=(
            "Suspended works tie up sanctioned funds without producing any public asset, "
            "and suspensions frequently become permanent if not reviewed."
        ),
        recommended_action=(
            "Determine whether the work can be resumed; if it cannot, initiate "
            "de-sanction so the allocation can be reassigned."
        ),
    )


def rule_expenditure_ahead_of_progress(p: Project, m: ProjectMetrics) -> Optional[FactorResult]:
    gap = m.utilization_progress_gap or 0.0
    if gap < 20 or p.allocated_amount <= 0:
        return None
    raw = min(gap * 1.5, 100.0)
    return FactorResult(
        code="EXPENDITURE_AHEAD_OF_PROGRESS",
        title="Expenditure is materially ahead of physical progress",
        category=RiskCategory.FINANCIAL,
        severity=_level_from_score(raw),
        weight=0.22,
        raw_score=raw,
        detected_indicator=(
            f"Fund utilisation is {_fmt_pct(m.utilization_percent)} while physical "
            f"progress is only {_fmt_pct(m.progress_percent)} - a gap of "
            f"{gap:.1f} percentage points."
        ),
        evidence=(
            f"Allocated {_fmt_money(p.allocated_amount)}; spent "
            f"{_fmt_money(p.spent_amount)}; progress {_fmt_pct(m.progress_percent)}."
        ),
        explanation=(
            "Money has left the account faster than the asset has been built. This is the "
            "classic signature of advance payments without matching measurement-book "
            "entries, inflated running bills, or simple progress under-reporting."
        ),
        recommended_action=(
            "Reconcile the measurement book and running-account bills against released "
            "amounts; require a third-party physical verification before the next release."
        ),
        metric_name="utilization_progress_gap_pp",
        metric_value=round(gap, 2),
        threshold_value=20.0,
        responsible_party="District Authority / Executing Agency",
    )


def rule_underspend_near_deadline(p: Project, m: ProjectMetrics) -> Optional[FactorResult]:
    if m.time_elapsed_percent is None or p.status == ProjectStatus.COMPLETED:
        return None
    if m.time_elapsed_percent < 70 or m.utilization_percent >= 50:
        return None
    raw = min((m.time_elapsed_percent - 70) * 1.2 + (50 - m.utilization_percent) * 1.2, 100.0)
    return FactorResult(
        code="UNDERSPEND_NEAR_DEADLINE",
        title="Sanctioned funds remain largely unspent late in the project window",
        category=RiskCategory.EXPENDITURE,
        severity=_level_from_score(raw),
        weight=0.18,
        raw_score=raw,
        detected_indicator=(
            f"{_fmt_pct(m.time_elapsed_percent)} of the project duration has elapsed but "
            f"only {_fmt_pct(m.utilization_percent)} of the allocation has been drawn."
        ),
        evidence=(
            f"Allocated {_fmt_money(p.allocated_amount)}; spent "
            f"{_fmt_money(p.spent_amount)}; unspent balance "
            f"{_fmt_money(p.remaining_amount)}; {m.days_remaining} days remaining."
        ),
        explanation=(
            "Low utilisation this late usually means the work has not genuinely started. "
            "It also creates pressure for a rushed year-end drawdown, which is where "
            "expenditure irregularities concentrate."
        ),
        recommended_action=(
            "Verify whether work has physically commenced on site and require an "
            "installment-wise drawdown plan for the remaining period."
        ),
        metric_name="utilization_percent",
        metric_value=m.utilization_percent,
        threshold_value=50.0,
        responsible_party="District Authority",
    )


def rule_cost_overrun(p: Project, m: ProjectMetrics) -> Optional[FactorResult]:
    if m.cost_overrun_percent is None or m.cost_overrun_percent <= 2:
        return None
    raw = min(m.cost_overrun_percent * 3.0, 100.0)
    baseline = "sanctioned estimate" if p.estimated_cost else "allocated amount"
    return FactorResult(
        code="COST_OVERRUN",
        title="Expenditure has exceeded the sanctioned amount",
        category=RiskCategory.FINANCIAL,
        severity=_level_from_score(raw),
        weight=0.24,
        raw_score=raw,
        detected_indicator=(
            f"Expenditure exceeds the {baseline} by {m.cost_overrun_percent:.1f}%."
        ),
        evidence=(
            f"Spent {_fmt_money(p.spent_amount)} against a {baseline} of "
            f"{_fmt_money(p.estimated_cost or p.allocated_amount)}."
        ),
        explanation=(
            "Expenditure beyond sanction has no automatic authority under the MPLAD "
            "guidelines and must be regularised or recovered."
        ),
        recommended_action=(
            "Obtain the revised estimate and its approval; if none exists, raise an "
            "audit observation and hold further releases."
        ),
        metric_name="cost_overrun_percent",
        metric_value=round(m.cost_overrun_percent, 2),
        threshold_value=2.0,
        responsible_party="Auditor / District Authority",
    )


def rule_stalled_reporting(p: Project, m: ProjectMetrics) -> Optional[FactorResult]:
    if p.status in (ProjectStatus.COMPLETED, ProjectStatus.CANCELLED):
        return None
    days = m.days_since_progress_update
    if days is None or days < 120:
        return None
    raw = min(25 + (days - 120) / 3.0, 100.0)
    return FactorResult(
        code="STALLED_PROGRESS_REPORTING",
        title="No progress has been reported for an extended period",
        category=RiskCategory.IMPLEMENTATION,
        severity=_level_from_score(raw),
        weight=0.14,
        raw_score=raw,
        detected_indicator=f"The last physical progress update was {days} days ago.",
        evidence=(
            f"Latest progress entry {max(u.updated_on for u in p.progress_updates)}; "
            f"current progress {_fmt_pct(m.progress_percent)}; status {p.status.value}."
        ),
        explanation=(
            "A reporting gap of this length means the monitoring record cannot be relied "
            "upon. Works that stop being reported are frequently works that have stopped."
        ),
        recommended_action=(
            "Direct the executing agency to file an immediate progress return supported "
            "by dated site photographs."
        ),
        metric_name="days_since_progress_update",
        metric_value=float(days),
        threshold_value=120.0,
    )


def rule_zero_expenditure_after_start(p: Project, m: ProjectMetrics) -> Optional[FactorResult]:
    if p.spent_amount > 0 or p.start_date is None:
        return None
    if p.status in (ProjectStatus.NOT_STARTED, ProjectStatus.CANCELLED):
        return None
    days_since_start = (m.as_of - p.start_date).days
    if days_since_start < 120:
        return None
    raw = min(30 + days_since_start / 10.0, 100.0)
    return FactorResult(
        code="ZERO_EXPENDITURE_AFTER_START",
        title="No expenditure recorded despite the work having commenced",
        category=RiskCategory.EXPENDITURE,
        severity=_level_from_score(raw),
        weight=0.16,
        raw_score=raw,
        detected_indicator=(
            f"Start date was recorded {days_since_start} days ago but cumulative "
            f"expenditure is still nil."
        ),
        evidence=(
            f"Start {p.start_date}; allocated {_fmt_money(p.allocated_amount)}; spent "
            f"{_fmt_money(p.spent_amount)}; status {p.status.value}."
        ),
        explanation=(
            "Either the work has not actually started, or expenditure is being incurred "
            "without being entered into the system. Both break the audit trail."
        ),
        recommended_action=(
            "Confirm the true commencement date and reconcile the agency's cash book "
            "with the portal."
        ),
        metric_name="days_since_start",
        metric_value=float(days_since_start),
        threshold_value=120.0,
    )


def rule_completed_low_utilization(p: Project, m: ProjectMetrics) -> Optional[FactorResult]:
    if p.status != ProjectStatus.COMPLETED:
        return None
    if m.utilization_percent >= 60 or p.allocated_amount <= 0:
        return None
    raw = min((60 - m.utilization_percent) * 1.4, 100.0)
    return FactorResult(
        code="COMPLETED_LOW_UTILIZATION",
        title="Work certified complete with a large unspent balance",
        category=RiskCategory.FINANCIAL,
        severity=_level_from_score(raw),
        weight=0.16,
        raw_score=raw,
        detected_indicator=(
            f"The work is marked complete but only {_fmt_pct(m.utilization_percent)} of "
            f"the allocation was drawn."
        ),
        evidence=(
            f"Allocated {_fmt_money(p.allocated_amount)}; spent "
            f"{_fmt_money(p.spent_amount)}; unspent {_fmt_money(p.remaining_amount)}."
        ),
        explanation=(
            "Either the delivered scope is smaller than what was sanctioned, or the "
            "closing expenditure statement has not been filed. The unspent balance also "
            "needs to be surrendered or re-appropriated."
        ),
        recommended_action=(
            "Obtain the completion certificate and final expenditure statement; "
            "surrender the balance if the scope was genuinely reduced."
        ),
        metric_name="utilization_percent",
        metric_value=m.utilization_percent,
        threshold_value=60.0,
        responsible_party="Auditor",
    )


def rule_completed_incomplete_progress(p: Project, m: ProjectMetrics) -> Optional[FactorResult]:
    if p.status != ProjectStatus.COMPLETED or m.progress_percent >= 99.5:
        return None
    raw = min((100 - m.progress_percent) * 2.0, 100.0)
    return FactorResult(
        code="COMPLETED_PROGRESS_MISMATCH",
        title="Completion status conflicts with the recorded physical progress",
        category=RiskCategory.PROGRESS,
        severity=_level_from_score(raw),
        weight=0.18,
        raw_score=raw,
        detected_indicator=(
            f"Status is 'Completed' while physical progress is recorded as "
            f"{_fmt_pct(m.progress_percent)}."
        ),
        evidence=f"Status {p.status.value}; progress {_fmt_pct(m.progress_percent)}.",
        explanation=(
            "The two authoritative fields for the same fact disagree. Until reconciled, "
            "neither the completion report nor the progress series can be trusted."
        ),
        recommended_action=(
            "Reconcile the completion certificate against the last measurement entry and "
            "correct whichever field is wrong."
        ),
        metric_name="progress_percent",
        metric_value=m.progress_percent,
        threshold_value=100.0,
    )


def rule_incomplete_record(p: Project, m: ProjectMetrics) -> Optional[FactorResult]:
    if not m.missing_fields:
        return None
    raw = min(len(m.missing_fields) * 18.0, 70.0)
    return FactorResult(
        code="INCOMPLETE_RECORD",
        title="Mandatory monitoring fields are missing from the record",
        category=RiskCategory.IMPLEMENTATION,
        severity=_level_from_score(raw),
        weight=0.10,
        raw_score=raw,
        detected_indicator=(
            f"{len(m.missing_fields)} required field(s) are blank: "
            f"{', '.join(m.missing_fields)}."
        ),
        evidence=f"Record completeness {m.data_completeness_percent:.0f}%.",
        explanation=(
            "Schedule and expenditure checks cannot be applied to fields that are blank, "
            "so the assessment below is based on partial information."
        ),
        recommended_action="Direct the data-entry authority to complete the missing fields.",
        metric_name="data_completeness_percent",
        metric_value=m.data_completeness_percent,
        threshold_value=100.0,
        responsible_party="District Authority",
    )


def rule_citizen_reports(p: Project, m: ProjectMetrics, open_reports: int) -> Optional[FactorResult]:
    if open_reports < 2:
        return None
    raw = min(20 + open_reports * 12.0, 100.0)
    return FactorResult(
        code="CITIZEN_REPORTS_CLUSTER",
        title="Multiple unresolved citizen reports against this work",
        category=RiskCategory.IMPLEMENTATION,
        severity=_level_from_score(raw),
        weight=0.12,
        raw_score=raw,
        detected_indicator=f"{open_reports} citizen reports are open against this work.",
        evidence=f"Open citizen reports: {open_reports}.",
        explanation=(
            "Independent public reports are a useful cross-check on agency-supplied "
            "status. A cluster against one work warrants field verification."
        ),
        recommended_action=(
            "Assign a field officer to verify the reported issues and publish an "
            "official response on each report."
        ),
        metric_name="open_citizen_reports",
        metric_value=float(open_reports),
        threshold_value=2.0,
        responsible_party="Field / District Officer",
    )


RULES = (
    rule_schedule_slippage,
    rule_deadline_imminent_low_progress,
    rule_overdue_incomplete,
    rule_status_delayed,
    rule_on_hold,
    rule_expenditure_ahead_of_progress,
    rule_underspend_near_deadline,
    rule_cost_overrun,
    rule_stalled_reporting,
    rule_zero_expenditure_after_start,
    rule_completed_low_utilization,
    rule_completed_incomplete_progress,
    rule_incomplete_record,
)


def evaluate_rules(project: Project, metrics: ProjectMetrics, open_citizen_reports: int = 0) -> List[FactorResult]:
    factors: List[FactorResult] = []
    for rule in RULES:
        result = rule(project, metrics)
        if result is not None:
            factors.append(result)
    citizen = rule_citizen_reports(project, metrics, open_citizen_reports)
    if citizen is not None:
        factors.append(citizen)
    return factors
