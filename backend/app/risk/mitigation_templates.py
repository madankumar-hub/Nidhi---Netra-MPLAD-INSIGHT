"""Standard mitigation actions proposed for each detected risk factor.

These are suggestions seeded into the mitigation tracker when an assessment
runs. An officer can accept, edit, reassign or close each one - nothing is
auto-resolved.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from app.risk.types import FactorResult


@dataclass(frozen=True)
class MitigationTemplate:
    action: str
    responsible_party: str
    priority: int  # 1 = high, 3 = low
    due_in_days: int


TEMPLATES: Dict[str, MitigationTemplate] = {
    "SCHEDULE_SLIPPAGE": MitigationTemplate(
        "Obtain a revised, milestone-wise implementation schedule from the executing "
        "agency and record the cause of slippage.",
        "Executing Agency",
        1,
        21,
    ),
    "DEADLINE_IMMINENT_LOW_PROGRESS": MitigationTemplate(
        "Hold a completion review; decide between remobilisation of resources and a "
        "formal time-extension proposal.",
        "District Authority",
        1,
        14,
    ),
    "OVERDUE_INCOMPLETE": MitigationTemplate(
        "Issue a written notice to the executing agency seeking a dated completion "
        "commitment, and escalate if no reply is received.",
        "District Authority",
        1,
        10,
    ),
    "STATUS_DELAYED": MitigationTemplate(
        "Record the delay reason against the work and schedule a fortnightly progress "
        "review until the work is back on track.",
        "Field / District Officer",
        2,
        14,
    ),
    "WORK_ON_HOLD": MitigationTemplate(
        "Determine whether the work can resume; if not, initiate de-sanction so the "
        "allocation can be reassigned.",
        "District Authority",
        1,
        30,
    ),
    "EXPENDITURE_AHEAD_OF_PROGRESS": MitigationTemplate(
        "Reconcile the measurement book and running-account bills with released amounts; "
        "require third-party physical verification before the next release.",
        "Auditor",
        1,
        15,
    ),
    "UNDERSPEND_NEAR_DEADLINE": MitigationTemplate(
        "Confirm physical commencement on site and obtain an installment-wise drawdown "
        "plan for the remaining project period.",
        "Executing Agency",
        2,
        21,
    ),
    "COST_OVERRUN": MitigationTemplate(
        "Obtain the revised estimate and its sanction; hold further releases until the "
        "excess expenditure is regularised.",
        "Auditor",
        1,
        10,
    ),
    "STALLED_PROGRESS_REPORTING": MitigationTemplate(
        "Direct the executing agency to file an immediate progress return supported by "
        "dated site photographs.",
        "Executing Agency",
        2,
        7,
    ),
    "ZERO_EXPENDITURE_AFTER_START": MitigationTemplate(
        "Verify the actual commencement date and reconcile the agency cash book against "
        "the portal record.",
        "District Authority",
        2,
        14,
    ),
    "COMPLETED_LOW_UTILIZATION": MitigationTemplate(
        "Obtain the completion certificate and final expenditure statement; surrender or "
        "re-appropriate the unspent balance.",
        "Auditor",
        2,
        30,
    ),
    "COMPLETED_PROGRESS_MISMATCH": MitigationTemplate(
        "Reconcile the completion certificate with the last measurement entry and correct "
        "the erroneous field.",
        "Field / District Officer",
        2,
        14,
    ),
    "INCOMPLETE_RECORD": MitigationTemplate(
        "Complete the missing mandatory fields in the project record.",
        "District Authority",
        3,
        21,
    ),
    "CITIZEN_REPORTS_CLUSTER": MitigationTemplate(
        "Assign a field officer to verify the reported issues and publish an official "
        "response against each citizen report.",
        "Field / District Officer",
        2,
        14,
    ),
    "ALLOCATION_OUTLIER": MitigationTemplate(
        "Compare the detailed estimate against the applicable schedule of rates and "
        "record the justification for the higher sanction.",
        "Auditor",
        2,
        30,
    ),
    "COST_PER_BENEFICIARY_OUTLIER": MitigationTemplate(
        "Verify the beneficiary estimate in the proposal against ward-level population "
        "figures.",
        "District Authority",
        3,
        30,
    ),
    "NEAR_DUPLICATE_WORK": MitigationTemplate(
        "Compare site locations and estimates of the matched works; if the same asset is "
        "sanctioned twice, stop the duplicate release and raise an audit observation.",
        "Auditor",
        1,
        15,
    ),
}


def template_for(factor: FactorResult) -> Optional[MitigationTemplate]:
    return TEMPLATES.get(factor.code)


def recommended_actions(factors: List[FactorResult]) -> List[str]:
    seen = set()
    actions: List[str] = []
    for factor in factors:
        template = TEMPLATES.get(factor.code)
        text = template.action if template else factor.recommended_action
        if text and text not in seen:
            seen.add(text)
            actions.append(text)
    return actions
