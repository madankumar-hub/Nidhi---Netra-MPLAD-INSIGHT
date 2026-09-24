"""CSV and PDF export of flagged / filtered projects (FR12)."""
from __future__ import annotations

import csv
import io
from typing import Dict, Iterable, Optional

from app.models.project import Project
from app.models.risk import RiskAssessment

COLUMNS = [
    "project_code",
    "title",
    "mp_name",
    "constituency",
    "state",
    "district",
    "category",
    "executing_agency",
    "sanction_year",
    "start_date",
    "planned_end_date",
    "status",
    "review_status",
    "allocated_amount_lakh",
    "spent_amount_lakh",
    "remaining_amount_lakh",
    "utilization_percent",
    "progress_percent",
    "risk_level",
    "risk_score",
    "primary_risk_category",
    "top_flagged_reasons",
    # Provenance travels with the rows. A CSV gets forwarded, renamed and opened
    # by someone who never saw the page it came from, so the note cannot live in
    # a header comment: a leading "#" line would also push the real header to
    # row 2 and break every naive parser. A constant column is read by a human,
    # survives a filter in Excel, and cannot be mistaken for real data.
    "data_source",
]

#: Stated on every exported row. Update this when the dataset stops being
#: synthetic - and not before.
DATA_SOURCE_NOTE = (
    "Synthetic dataset prepared for Smart India Hackathon 2026 (SIH26102) - "
    "not official government data"
)


def projects_to_csv(
    projects: Iterable[Project], assessments: Optional[Dict[int, RiskAssessment]] = None
) -> str:
    assessments = assessments or {}
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for project in projects:
        assessment = assessments.get(project.id)
        reasons = ""
        if assessment and assessment.factors:
            reasons = " | ".join(f.title for f in assessment.factors[:3])
        writer.writerow(
            {
                "project_code": project.project_code,
                "title": project.title,
                "mp_name": project.mp_name,
                "constituency": project.constituency or "",
                "state": project.state,
                "district": project.district,
                "category": project.category,
                "executing_agency": project.executing_agency,
                "sanction_year": project.sanction_year,
                "start_date": project.start_date or "",
                "planned_end_date": project.planned_end_date or "",
                "status": project.status.value,
                "review_status": project.review_status.value,
                "allocated_amount_lakh": f"{project.allocated_amount:.2f}",
                "spent_amount_lakh": f"{project.spent_amount:.2f}",
                "remaining_amount_lakh": f"{project.remaining_amount:.2f}",
                "utilization_percent": f"{project.utilization_percent:.2f}",
                "progress_percent": f"{project.progress_percent:.2f}",
                "risk_level": assessment.risk_level.value if assessment else "",
                "risk_score": f"{assessment.risk_score:.2f}" if assessment else "",
                "primary_risk_category": (
                    assessment.primary_category.value
                    if assessment and assessment.primary_category
                    else ""
                ),
                "top_flagged_reasons": reasons,
                "data_source": DATA_SOURCE_NOTE,
            }
        )
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# PDF export (FR12)
#
# The SRS asks for CSV *and* PDF. CSV is for working with the numbers; the PDF
# is the printable report an officer attaches to a file or forwards upward, so
# it carries fewer columns and puts the risk assessment where the eye lands.
# ---------------------------------------------------------------------------
from datetime import date as _date  # noqa: E402

from app.services.pdf_writer import build_table_pdf  # noqa: E402

#: (header, width in points, alignment). Widths total the A4 text width (515pt).
#: Landscape A4: 841.89pt less two 40pt margins leaves 761.89pt of text width.
#: Widths are sized from the real Helvetica metrics of the worst-case value in
#: each column - a full work code is 73pt, "In Progress" is 41pt, "CRITICAL 91"
#: is 48pt - plus 8pt of padding. A test asserts the total fits the page.
PDF_COLUMNS = [
    ("Work ID", 84.0, "left"),
    ("Title", 250.0, "left"),
    ("District", 66.0, "left"),
    ("Agency", 92.0, "left"),
    ("Allocated", 56.0, "right"),
    ("Spent", 52.0, "right"),
    ("Util %", 36.0, "right"),
    ("Status", 60.0, "left"),
    ("Risk", 60.0, "left"),
]


def projects_to_pdf(
    projects: Iterable[Project],
    assessments: Optional[Dict[int, RiskAssessment]] = None,
    flagged_only: bool = False,
) -> bytes:
    """Render the current selection as a printable A4 report."""
    assessments = assessments or {}
    rows = []
    for project in projects:
        assessment = assessments.get(project.id)
        risk = assessment.risk_level.value if assessment else "-"
        if assessment:
            risk = f"{risk} {assessment.risk_score:.0f}"
        rows.append(
            [
                project.project_code,
                project.title,
                project.district,
                project.executing_agency,
                f"{project.allocated_amount:,.2f}",
                f"{project.spent_amount:,.2f}",
                f"{project.utilization_percent:.0f}",
                project.status.value,
                risk,
            ]
        )

    heading = "Flagged works" if flagged_only else "MPLAD works"
    generated = _date.today().strftime("%d %B %Y")

    return build_table_pdf(
        title=f"Nidhi Netra - {heading}",
        subtitle=(
            f"Generated {generated} | {len(rows)} record(s) | "
            "Amounts in Rs. lakh | Risk score is an internal indicator, not a finding"
        ),
        footer_note=(
            "Synthetic dataset prepared for Smart India Hackathon 2026 (SIH26102). "
            "Not official government data."
        ),
        columns=PDF_COLUMNS,
        rows=rows,
        empty_message="No works matched the selected filters.",
    )
