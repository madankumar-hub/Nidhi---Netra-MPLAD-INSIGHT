"""Generate the realistic synthetic MPLAD dataset (SRS 2.4).

Usage:
    python -m seed.seed_data                # default 600 works
    python -m seed.seed_data --projects 5200 --reset

Credentials are NEVER hardcoded. Passwords are read from the environment
(SEED_ADMIN_PASSWORD and friends). Where one is not supplied a strong random
password is generated, printed once and written to `.seed-credentials.txt`,
which is git-ignored.
"""
from __future__ import annotations

import argparse
import logging
import random
import secrets
import string
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.database.base import utcnow
from app.database.init_db import drop_database, init_database
from app.database.session import SessionLocal
from app.models.citizen_report import CitizenReport
from app.core.enums import (
    AccessRequestStatus,
    ActivityType,
    CitizenReportCategory,
    CitizenReportStatus,
    MitigationStatus,
    NoteType,
    ProjectStatus,
    ReviewStatus,
    RiskLevel,
    UserRole,
)
from app.models.access_request import AccessRequest
from app.models.note import Note
from app.models.project import Project
from app.models.review import Review
from app.models.tracking import FundUpdate, ProgressUpdate
from app.models.user import User
from app.services import activity_service, risk_service
from seed import reference_data as ref

logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")
logger = logging.getLogger("mplad.seed")

TODAY = date.today()
CREDENTIALS_FILE = Path(__file__).resolve().parents[1] / ".seed-credentials.txt"


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
def _password(env_value: str, generated: List[Tuple[str, str]], label: str) -> str:
    if env_value:
        return env_value
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    value = "".join(secrets.choice(alphabet) for _ in range(16))
    generated.append((label, value))
    return value


def seed_users(db) -> Dict[str, User]:
    generated: List[Tuple[str, str]] = []
    definitions = [
        (
            settings.seed_admin_email,
            "Dr. S. Ramanathan",
            UserRole.ADMIN,
            "Joint Secretary (MPLADS)",
            "Ministry of Statistics and Programme Implementation",
            None,
            _password(settings.seed_admin_password, generated, settings.seed_admin_email),
        ),
        (
            settings.seed_auditor_email,
            "Kavitha Menon",
            UserRole.AUDITOR,
            "Senior Audit Officer",
            "Office of the Accountant General",
            None,
            _password(settings.seed_auditor_password, generated, settings.seed_auditor_email),
        ),
        (
            settings.seed_officer_email,
            "Rakesh Pawar",
            UserRole.OFFICER,
            "District Nodal Officer",
            "District Collectorate",
            "Pune",
            _password(settings.seed_officer_password, generated, settings.seed_officer_email),
        ),
        (
            settings.seed_citizen_email,
            "Ananya Iyer",
            UserRole.CITIZEN,
            None,
            None,
            None,
            _password(settings.seed_citizen_password, generated, settings.seed_citizen_email),
        ),
    ]

    users: Dict[str, User] = {}
    for email, name, role, designation, department, district, password in definitions:
        existing = db.execute(select(User).where(User.email == email)).scalars().first()
        if existing is not None:
            users[role.value] = existing
            continue
        user = User(
            email=email.lower(),
            full_name=name,
            password_hash=hash_password(password),
            role=role,
            designation=designation,
            department=department,
            district=district,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        users[role.value] = user

    # A couple of extra officers so review history looks plausible.
    for email, name, district in [
        ("officer.nagpur@mplad.gov.in", "Sunita Kale", "Nagpur"),
        ("officer.lucknow@mplad.gov.in", "Imran Siddiqui", "Lucknow"),
    ]:
        if db.execute(select(User).where(User.email == email)).scalars().first():
            continue
        db.add(
            User(
                email=email,
                full_name=name,
                password_hash=hash_password(
                    _password("", generated, email)
                ),
                role=UserRole.OFFICER,
                designation="District Nodal Officer",
                department="District Collectorate",
                district=district,
                is_active=True,
                is_verified=True,
            )
        )

    db.commit()
    for role in users:
        db.refresh(users[role])

    if generated:
        lines = [
            "MPLAD Insight - generated seed credentials",
            "Generated because the matching SEED_*_PASSWORD variable was not set.",
            "Set those variables in .env to choose your own. Delete this file after use.",
            "",
        ]
        lines += [f"{email}  {password}" for email, password in generated]
        CREDENTIALS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        logger.warning("Generated %d password(s). Written to %s", len(generated), CREDENTIALS_FILE)
        for email, password in generated:
            logger.warning("  %-34s %s", email, password)
    return users


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------
def _mp_for(index: int) -> str:
    first = ref.MP_FIRST[index % len(ref.MP_FIRST)]
    last = ref.MP_LAST[(index * 7) % len(ref.MP_LAST)]
    return f"{first} {last}"


def _constituency_pool() -> List[Tuple[str, str, str, str]]:
    """(state, district, constituency, mp_name)"""
    pool: List[Tuple[str, str, str, str]] = []
    index = 0
    for state, districts in ref.STATES.items():
        for district, constituency in districts:
            pool.append((state, district, constituency, _mp_for(index)))
            index += 1
    return pool


def _template_for(category: str, rng: random.Random) -> Tuple[str, str]:
    templates = ref.WORK_TEMPLATES.get(category) or ref.WORK_TEMPLATES["Community Halls"]
    return rng.choice(templates)


def _render(template: Tuple[str, str], rng: random.Random, block: str) -> Tuple[str, str]:
    place = rng.choice(ref.PLACES)
    values = {
        "place": place,
        "block": block,
        "capacity": rng.choice([20000, 30000, 50000, 75000, 100000]),
        "rooms": rng.randint(2, 20),
        "length": rng.choice([150, 250, 400, 600, 800, 1200]),
        "area": rng.choice([120, 180, 240, 320, 450]),
        "ben": rng.choice([250, 480, 750, 1200, 2400, 5000]),
    }
    return template[0].format(**values), template[1].format(**values)


def _make_dates(year: int, rng: random.Random) -> Tuple[date, Optional[date], Optional[date]]:
    sanction = date(year, rng.randint(4, 12), rng.randint(1, 28))
    start = sanction + timedelta(days=rng.randint(20, 150))
    planned_end = start + timedelta(days=rng.choice([180, 240, 300, 365, 450, 540, 730]))
    return sanction, start, planned_end


def _profile(rng: random.Random) -> str:
    """Pick an execution profile. ~30% of records carry injected anomalies."""
    roll = rng.random()
    if roll < 0.32:
        return "healthy_complete"
    if roll < 0.52:
        return "healthy_ongoing"
    if roll < 0.62:
        return "not_started"
    if roll < 0.72:
        return "slow_progress"
    if roll < 0.80:
        return "overdue"
    if roll < 0.87:
        return "expenditure_ahead"      # injected anomaly
    if roll < 0.92:
        return "underspend_late"        # injected anomaly
    if roll < 0.96:
        return "cost_overrun"           # injected anomaly
    return "stalled"                    # injected anomaly


def _apply_profile(
    profile: str, allocated: float, start: date, planned_end: date, rng: random.Random
) -> Tuple[ProjectStatus, float, float, Optional[date]]:
    """Return (status, progress_percent, spent_amount, actual_end_date)."""
    duration = max((planned_end - start).days, 1)
    elapsed_pct = min(max((TODAY - start).days / duration, 0.0), 1.5)

    if profile == "healthy_complete":
        progress = 100.0
        spent = allocated * rng.uniform(0.88, 1.0)
        end = planned_end - timedelta(days=rng.randint(0, 40))
        return ProjectStatus.COMPLETED, progress, spent, min(end, TODAY)

    if profile == "healthy_ongoing":
        progress = round(min(elapsed_pct * rng.uniform(0.92, 1.08), 0.97) * 100, 1)
        spent = allocated * (progress / 100) * rng.uniform(0.9, 1.05)
        return ProjectStatus.IN_PROGRESS, max(progress, 5.0), spent, None

    if profile == "not_started":
        return ProjectStatus.NOT_STARTED, 0.0, 0.0, None

    if profile == "slow_progress":
        progress = round(min(elapsed_pct * rng.uniform(0.35, 0.6), 0.85) * 100, 1)
        spent = allocated * (progress / 100) * rng.uniform(0.85, 1.05)
        return ProjectStatus.IN_PROGRESS, max(progress, 3.0), spent, None

    if profile == "overdue":
        progress = round(rng.uniform(35, 80), 1)
        spent = allocated * (progress / 100) * rng.uniform(0.9, 1.1)
        return ProjectStatus.DELAYED, progress, spent, None

    if profile == "expenditure_ahead":
        progress = round(rng.uniform(15, 45), 1)
        spent = allocated * rng.uniform(0.70, 0.95)
        return ProjectStatus.IN_PROGRESS, progress, spent, None

    if profile == "underspend_late":
        progress = round(rng.uniform(10, 35), 1)
        spent = allocated * rng.uniform(0.02, 0.18)
        return ProjectStatus.IN_PROGRESS, progress, spent, None

    if profile == "cost_overrun":
        progress = round(rng.uniform(70, 100), 1)
        spent = allocated * rng.uniform(1.06, 1.35)
        status = ProjectStatus.COMPLETED if progress >= 99 else ProjectStatus.IN_PROGRESS
        return status, progress, spent, (TODAY - timedelta(days=rng.randint(5, 60)) if status == ProjectStatus.COMPLETED else None)

    # stalled
    progress = round(rng.uniform(20, 55), 1)
    spent = allocated * (progress / 100) * rng.uniform(0.8, 1.0)
    return ProjectStatus.ON_HOLD, progress, spent, None


def _build_fund_trail(project: Project, rng: random.Random) -> List[FundUpdate]:
    if project.spent_amount <= 0 or project.start_date is None:
        return []
    installments = rng.randint(2, 5)
    remaining = project.spent_amount
    entries: List[FundUpdate] = []
    cumulative = 0.0
    span = max((min(TODAY, project.planned_end_date or TODAY) - project.start_date).days, 30)
    for i in range(installments):
        share = remaining if i == installments - 1 else round(remaining * rng.uniform(0.25, 0.5), 2)
        share = max(round(share, 2), 0.01)
        remaining = round(remaining - share, 2)
        cumulative = round(cumulative + share, 2)
        when = project.start_date + timedelta(days=int(span * (i + 1) / (installments + 0.5)))
        entries.append(
            FundUpdate(
                updated_on=min(when, TODAY),
                installment_no=i + 1,
                released_amount=round(share * rng.uniform(1.0, 1.15), 2),
                expenditure_amount=share,
                cumulative_spent=cumulative,
                voucher_reference=f"V/{project.sanction_year}/{rng.randint(1000, 9999)}",
                remarks=None,
            )
        )
        if remaining <= 0:
            break
    return entries


def _build_progress_trail(project: Project, profile: str, rng: random.Random) -> List[ProgressUpdate]:
    if project.start_date is None or project.progress_percent <= 0:
        return []
    points = rng.randint(3, 6)
    duration = max(((project.planned_end_date or TODAY) - project.start_date).days, 30)
    entries: List[ProgressUpdate] = []
    last_day = TODAY
    if profile == "stalled":
        last_day = TODAY - timedelta(days=rng.randint(150, 420))
    for i in range(1, points + 1):
        fraction = i / points
        when = project.start_date + timedelta(days=int(duration * fraction * rng.uniform(0.8, 1.0)))
        when = min(when, last_day)
        if when < project.start_date:
            when = project.start_date
        actual = round(project.progress_percent * fraction, 1)
        planned = round(min((when - project.start_date).days / duration * 100, 100.0), 1)
        entries.append(
            ProgressUpdate(
                updated_on=when,
                progress_percent=actual,
                planned_progress_percent=planned,
                milestone=ref.MILESTONES[min(int(actual / 10), len(ref.MILESTONES) - 1)],
                remarks=None,
            )
        )
    entries.sort(key=lambda e: e.updated_on)
    if entries:
        entries[-1].progress_percent = project.progress_percent
    return entries



def jittered_district_point(rng, district: str):
    """A point near `district`'s headquarters, or None if we do not know it.

    Returns (latitude, longitude) rounded to five decimals - about a metre,
    which is more precision than a headquarters coordinate deserves, but
    matches the column type and keeps markers from stacking exactly.
    """
    centre = ref.DISTRICT_COORDINATES.get(district)
    if centre is None:
        return None

    spread = ref.COORDINATE_JITTER_DEGREES
    latitude = centre[0] + rng.uniform(-spread, spread)
    longitude = centre[1] + rng.uniform(-spread, spread)
    return round(latitude, 5), round(longitude, 5)


def seed_projects(db, count: int, rng: random.Random) -> List[Project]:
    pool = _constituency_pool()
    years = [2021, 2022, 2023, 2024, 2025, 2026]
    year_weights = [0.10, 0.13, 0.17, 0.22, 0.24, 0.14]
    projects: List[Project] = []
    duplicate_sources: List[Project] = []

    for i in range(count):
        state, district, constituency, mp = rng.choice(pool)
        category = rng.choice(ref.CATEGORIES)
        block = f"{rng.choice(ref.BLOCKS)} ({district})"
        year = rng.choices(years, weights=year_weights, k=1)[0]
        sanction, start, planned_end = _make_dates(year, rng)

        allocated = round(rng.choice([5, 8, 10, 12, 15, 18, 20, 25, 30, 40, 50, 75, 100]) * rng.uniform(0.85, 1.2), 2)
        profile = _profile(rng)
        if start > TODAY:
            profile = "not_started"
        status, progress, spent, actual_end = _apply_profile(profile, allocated, start, planned_end, rng)

        title, description = _render(_template_for(category, rng), rng, block)

        # Inject a small number of genuine near-duplicate descriptions so the
        # duplicate-detection layer has something real to find (SRS FR9).
        if duplicate_sources and rng.random() < 0.02:
            source = rng.choice(duplicate_sources)
            if source.district == district:
                title = source.title
                description = source.description

        coordinates = jittered_district_point(rng, district)

        project = Project(
            project_code=f"MPLAD-{year}-{i + 1:05d}",
            title=title,
            description=description,
            mp_name=mp,
            constituency=constituency,
            house="Lok Sabha" if i % 7 else "Rajya Sabha",
            state=state,
            district=district,
            block=block,
            location=f"{rng.choice(ref.PLACES)}, {district}",
            # Placed near its own district, not at a random point in a box
            # covering half of South Asia. A district with no known
            # coordinates gets none at all - an absent marker is honest, a
            # wrong one is not.
            latitude=coordinates[0] if coordinates else None,
            longitude=coordinates[1] if coordinates else None,
            category=category,
            executing_agency=rng.choice(ref.AGENCIES),
            contractor=rng.choice(ref.CONTRACTORS),
            sanction_year=year,
            sanction_date=sanction,
            start_date=start,
            planned_end_date=planned_end,
            actual_end_date=actual_end,
            allocated_amount=allocated,
            spent_amount=round(spent, 2),
            estimated_cost=round(allocated * rng.uniform(0.95, 1.02), 2),
            progress_percent=progress,
            planned_progress_percent=None,
            status=status,
            review_status=ReviewStatus.PENDING_REVIEW,
            beneficiaries=rng.choice([180, 350, 600, 900, 1500, 2500, 4000, 8000]),
            # Clearly-labelled placeholder assets served from the frontend's
            # public/ directory. They are explicitly marked as synthetic so
            # nothing in the demo can be mistaken for a real record. Not every
            # work has them, which is also true of the real scheme.
            photo_url=(
                "/samples/site-photograph.svg" if rng.random() < 0.72 else None
            ),
            document_url=(
                "/samples/sanction-document.svg" if rng.random() < 0.65 else None
            ),
            remarks=None,
        )

        # A handful of records are deliberately left incomplete so the data
        # quality rule has real input.
        if rng.random() < 0.03:
            project.description = ""
        if rng.random() < 0.02:
            project.planned_end_date = None

        db.add(project)
        projects.append(project)
        if len(duplicate_sources) < 60:
            duplicate_sources.append(project)

    db.flush()

    for project in projects:
        profile_hint = "stalled" if project.status == ProjectStatus.ON_HOLD else ""
        for entry in _build_fund_trail(project, rng):
            entry.project_id = project.id
            db.add(entry)
        for entry in _build_progress_trail(project, profile_hint, rng):
            entry.project_id = project.id
            db.add(entry)

    db.commit()
    logger.info("Created %d project records with fund and progress trails.", len(projects))
    return projects


# ---------------------------------------------------------------------------
# Reviews, notes, citizen reports
# ---------------------------------------------------------------------------
REVIEW_FINDINGS = {
    ReviewStatus.ON_TRACK: [
        "Site inspection carried out. Work is progressing in line with the sanctioned "
        "milestone schedule and measurement entries are up to date.",
        "Quarterly review completed. Expenditure is consistent with physical progress; "
        "no observations raised.",
    ],
    ReviewStatus.DELAYED: [
        "Physical progress is materially behind schedule. The executing agency cites "
        "delayed material supply and unseasonal rainfall.",
        "Work has slipped against the sanctioned timeline. A revised milestone plan has "
        "been sought from the agency.",
    ],
    ReviewStatus.ESCALATED: [
        "Expenditure is substantially ahead of verified physical progress. The matter has "
        "been referred for third-party verification before any further release.",
        "Repeated failure to file progress returns. Referred to the District Collector for "
        "direction to the executing agency.",
    ],
    ReviewStatus.REVIEWED: [
        "Record examined. Documentation is in order; a further review is scheduled after "
        "the next installment is released.",
    ],
    ReviewStatus.RESOLVED: [
        "Earlier observations have been complied with. Completion certificate and final "
        "expenditure statement are on record.",
    ],
}

NOTE_TEXTS = {
    NoteType.REVIEW: [
        "Reviewed along with the district nodal officer. Measurement book entries verified "
        "up to the third installment.",
        "Agency confirmed that the revised completion schedule will be submitted within "
        "fifteen days.",
    ],
    NoteType.DELAY: [
        "Delay attributed to a pending right-of-way clearance from the forest department. "
        "Follow-up letter issued.",
        "Work suspended during the monsoon. Resumption expected in the first week of the "
        "coming quarter.",
    ],
    NoteType.RISK: [
        "Flagged indicator discussed with the agency. Third-party verification of the "
        "claimed progress has been requested.",
        "Expenditure-progress divergence noted. Further releases held pending "
        "reconciliation of running-account bills.",
    ],
    NoteType.ACTION: [
        "Directed the executing agency to upload dated site photographs with the next "
        "progress return.",
        "Instructed the district office to complete the missing fields in the project "
        "record before the next review.",
    ],
    NoteType.GENERAL: [
        "Beneficiary count revised after ward-level verification by the block office.",
        "Local representatives have requested that the work be inaugurated after the "
        "completion certificate is issued.",
    ],
}

CITIZEN_REPORT_TEXTS = {
    CitizenReportCategory.WORK_NOT_STARTED: (
        "The portal shows this work as in progress, but no construction activity is "
        "visible at the site. Residents have not seen any work for several months."
    ),
    CitizenReportCategory.POOR_QUALITY: (
        "The surface has already developed cracks within a few months of completion. "
        "Request a quality inspection by an independent engineer."
    ),
    CitizenReportCategory.INCOMPLETE_WORK: (
        "The structure has been built but the electrical connection and water supply "
        "have not been provided, so the facility cannot be used."
    ),
    CitizenReportCategory.WRONG_LOCATION: (
        "The location recorded on the portal does not match the actual site where the "
        "work has been carried out."
    ),
    CitizenReportCategory.INFORMATION_INCORRECT: (
        "The completion date shown on this page appears to be incorrect. The work was "
        "still ongoing at the end of last month."
    ),
    CitizenReportCategory.OTHER: (
        "Requesting a signboard at the site displaying the sanctioned amount and the "
        "name of the executing agency, as required under the guidelines."
    ),
}


def seed_workflow(db, projects: List[Project], users: Dict[str, User], rng: random.Random) -> None:
    officers = db.execute(select(User).where(User.role.in_([UserRole.OFFICER, UserRole.AUDITOR, UserRole.ADMIN]))).scalars().all()
    citizen = users.get(UserRole.CITIZEN.value)

    reviewed = 0
    noted = 0
    reports = 0

    for project in projects:
        # ~55% of works carry at least one recorded review.
        if rng.random() < 0.55:
            reviewer = rng.choice(officers)
            if project.status == ProjectStatus.DELAYED:
                outcome = rng.choices(
                    [ReviewStatus.DELAYED, ReviewStatus.ESCALATED], weights=[0.7, 0.3], k=1
                )[0]
            elif project.status == ProjectStatus.COMPLETED:
                outcome = rng.choices(
                    [ReviewStatus.RESOLVED, ReviewStatus.REVIEWED], weights=[0.6, 0.4], k=1
                )[0]
            elif project.status == ProjectStatus.ON_HOLD:
                outcome = ReviewStatus.ESCALATED
            else:
                outcome = rng.choices(
                    [ReviewStatus.ON_TRACK, ReviewStatus.REVIEWED, ReviewStatus.DELAYED],
                    weights=[0.55, 0.3, 0.15],
                    k=1,
                )[0]

            when = utcnow() - timedelta(days=rng.randint(3, 240))
            db.add(
                Review(
                    project_id=project.id,
                    reviewer_id=reviewer.id,
                    reviewer_name=reviewer.full_name,
                    reviewer_role=reviewer.role.value,
                    review_date=when,
                    previous_status=ReviewStatus.PENDING_REVIEW,
                    status=outcome,
                    findings=rng.choice(REVIEW_FINDINGS[outcome]),
                    notes=None,
                    action_required=(
                        "Obtain a revised completion schedule from the executing agency."
                        if outcome in (ReviewStatus.DELAYED, ReviewStatus.ESCALATED)
                        else None
                    ),
                    escalated_to=(
                        "District Collector" if outcome == ReviewStatus.ESCALATED else None
                    ),
                    follow_up_required=outcome in (ReviewStatus.DELAYED, ReviewStatus.ESCALATED),
                )
            )
            project.review_status = outcome
            reviewed += 1

            activity_service.log(
                db,
                project_id=project.id,
                activity_type=ActivityType.PROJECT_REVIEWED,
                summary=f"Project reviewed by {reviewer.full_name} - outcome: {outcome.value}.",
                actor=reviewer,
            )

        # Notes on works that need attention plus a random sample of others.
        needs_note = project.status in (ProjectStatus.DELAYED, ProjectStatus.ON_HOLD)
        if needs_note or rng.random() < 0.3:
            author = rng.choice(officers)
            note_type = (
                NoteType.DELAY
                if project.status == ProjectStatus.DELAYED
                else rng.choice(list(NOTE_TEXTS))
            )
            db.add(
                Note(
                    project_id=project.id,
                    author_id=author.id,
                    author_name=author.full_name,
                    author_role=author.role.value,
                    note_type=note_type,
                    content=rng.choice(NOTE_TEXTS[note_type]),
                    is_pinned=rng.random() < 0.1,
                )
            )
            noted += 1

        # Citizen reports concentrate on works that look troubled.
        trouble = project.status in (ProjectStatus.DELAYED, ProjectStatus.ON_HOLD)
        if citizen is not None and (rng.random() < (0.22 if trouble else 0.04)):
            for _ in range(rng.randint(1, 3) if trouble else 1):
                category = rng.choice(list(CITIZEN_REPORT_TEXTS))
                db.add(
                    CitizenReport(
                        project_id=project.id,
                        reporter_id=citizen.id,
                        reporter_name=citizen.full_name,
                        category=category,
                        description=CITIZEN_REPORT_TEXTS[category],
                        status=rng.choices(
                            [
                                CitizenReportStatus.SUBMITTED,
                                CitizenReportStatus.UNDER_REVIEW,
                                CitizenReportStatus.ACTION_TAKEN,
                                CitizenReportStatus.CLOSED,
                            ],
                            weights=[0.45, 0.25, 0.2, 0.1],
                            k=1,
                        )[0],
                    )
                )
                reports += 1

    db.commit()
    logger.info("Created %d reviews, %d notes, %d citizen reports.", reviewed, noted, reports)


ACCESS_REQUESTS = [
    dict(
        email="s.varghese@kerala.gov.in",
        full_name="Sunil Varghese",
        role=UserRole.OFFICER,
        designation="Assistant Executive Engineer",
        department="District Rural Roads Agency",
        district="Ernakulam",
        employee_id="KL/AEE/2019/0442",
        justification=(
            "I supervise MPLAD road and culvert works across three blocks in Ernakulam "
            "district and need to file progress returns and record delay reasons "
            "against the works assigned to this office."
        ),
        status=AccessRequestStatus.PENDING,
    ),
    dict(
        email="meera.das@nic.in",
        full_name="Meera Das",
        role=UserRole.AUDITOR,
        designation="Audit Officer (Grade II)",
        department="Office of the Accountant General",
        district="Khordha",
        employee_id="AG/OD/AUD/1187",
        justification=(
            "Posted to the MPLAD expenditure audit cell for the current financial year. "
            "I need access to the flagged-works queue and the expenditure trail to "
            "prepare the half-yearly audit observations."
        ),
        status=AccessRequestStatus.PENDING,
    ),
    dict(
        email="quick.money@example.com",
        full_name="Anon Requester",
        role=UserRole.AUDITOR,
        designation=None,
        department=None,
        district=None,
        employee_id=None,
        justification=(
            "I would like auditor access to look at the internal risk scores for "
            "research purposes."
        ),
        status=AccessRequestStatus.PENDING,
    ),
]


def seed_access_requests(db, rng: random.Random) -> None:
    """A small queue for the Administrator's access-requests screen.

    Includes one request from an address outside the government domains, so the
    screen demonstrates the allowlist warning rather than only the happy path.
    """
    created = 0
    for entry in ACCESS_REQUESTS:
        if db.execute(select(User).where(User.email == entry["email"])).scalars().first():
            continue
        user = User(
            email=entry["email"],
            full_name=entry["full_name"],
            password_hash=hash_password(secrets.token_urlsafe(18)),
            role=UserRole.CITIZEN,
            is_active=True,
            is_verified=True,
        )
        db.add(user)
        db.flush()
        db.add(
            AccessRequest(
                user_id=user.id,
                email=user.email,
                full_name=user.full_name,
                requested_role=entry["role"],
                designation=entry["designation"],
                department=entry["department"],
                district=entry["district"],
                employee_id=entry["employee_id"],
                justification=entry["justification"],
                status=entry["status"],
                email_allowlisted=settings.is_official_email(user.email),
            )
        )
        activity_service.log(
            db,
            project_id=None,
            activity_type=ActivityType.ACCESS_REQUESTED,
            summary=f"{user.full_name} requested {entry['role'].value} access.",
            actor=user,
            to_value=entry["role"].value,
        )
        created += 1
    db.commit()
    logger.info("Created %d pending access request(s).", created)


def seed_risk(db, projects: List[Project], rng: random.Random) -> None:
    from app.services import project_service

    stats = risk_service.load_cohort_stats(db)
    peer_index = risk_service.build_peer_index(db)
    model = risk_service.load_anomaly_model(db, refit=True)
    if model is not None:
        logger.info(
            "Isolation forest fitted on %d records (%d trees, %d features).",
            len(model.training_scores), model.n_trees, len(model.feature_median),
        )
    else:
        logger.info("Cohort too small to fit the anomaly model; skipping that layer.")
    assessed = 0
    for project in projects:
        open_reports = project_service.open_citizen_report_count(db, project.id)
        risk_service.run_assessment(
            db,
            project,
            actor=None,
            cohort_stats=stats,
            peers=peer_index.get(project.district, []),
            anomaly_model=model,
            open_citizen_reports=open_reports,
            commit=False,
        )
        assessed += 1
        if assessed % 100 == 0:
            db.commit()
            logger.info("  assessed %d/%d", assessed, len(projects))
    db.commit()

    # Give a realistic share of mitigation actions some human progress.
    from app.models.risk import MitigationAction

    actions = db.execute(select(MitigationAction)).scalars().all()
    officers = db.execute(select(User).where(User.role == UserRole.OFFICER)).scalars().all()
    for action in actions:
        roll = rng.random()
        if roll < 0.18:
            action.status = MitigationStatus.IN_PROGRESS
            action.notes = "Communication issued to the responsible party; awaiting reply."
        elif roll < 0.30:
            action.status = MitigationStatus.RESOLVED
            action.resolved_at = utcnow() - timedelta(days=rng.randint(1, 90))
            action.resolved_by_name = (rng.choice(officers).full_name if officers else "District Nodal Officer")
            action.notes = "Compliance received and verified at the district level."
    db.commit()
    logger.info("Ran %d risk assessments and updated mitigation progress.", assessed)


def summarise(db) -> None:
    from sqlalchemy import func

    from app.models.risk import RiskAssessment

    total = db.execute(select(func.count()).select_from(Project)).scalar_one()
    logger.info("--- Seed summary -------------------------------------------")
    logger.info("Projects: %s", total)
    for status in ProjectStatus:
        count = db.execute(
            select(func.count()).select_from(Project).where(Project.status == status)
        ).scalar_one()
        if count:
            logger.info("  %-14s %s", status.value, count)
    for level in RiskLevel:
        count = db.execute(
            select(func.count())
            .select_from(RiskAssessment)
            .where(RiskAssessment.is_current.is_(True), RiskAssessment.risk_level == level)
        ).scalar_one()
        logger.info("  risk %-9s %s", level.value, count)
    logger.info("------------------------------------------------------------")


def run_seed(*, projects: int = 600, reset: bool = False, rng_seed: int = 20260101) -> bool:
    """Seed the database. Returns False when it was already populated.

    Exposed as a function (not just a CLI) so a cloud deployment can call it
    once on first boot - see SEED_ON_STARTUP in `app/main.py`.
    """
    rng = random.Random(rng_seed)

    if reset:
        drop_database()
    init_database()

    db = SessionLocal()
    try:
        existing = db.execute(select(Project.id)).scalars().first()
        if existing is not None and not reset:
            logger.warning("Database already contains projects. Re-run with --reset to rebuild.")
            return False
        users = seed_users(db)
        created = seed_projects(db, projects, rng)
        seed_workflow(db, created, users, rng)
        seed_access_requests(db, rng)
        seed_risk(db, created, rng)
        summarise(db)
        logger.info("Seeding complete.")
        return True
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the MPLAD Insight database.")
    parser.add_argument("--projects", type=int, default=600, help="number of works to generate")
    parser.add_argument("--reset", action="store_true", help="drop all tables before seeding")
    parser.add_argument("--seed", type=int, default=20260101, help="RNG seed for reproducibility")
    args = parser.parse_args()

    run_seed(projects=args.projects, reset=args.reset, rng_seed=args.seed)


if __name__ == "__main__":
    main()
