# Database

PostgreSQL is the target (SRS §2.3). SQLite is supported for zero-configuration
local development; no application code branches on the engine.

## Entities

| Table | Purpose | Key relationships |
|---|---|---|
| `users` | Citizens and officials | 1→N reviews, notes |
| `otp_codes` | Hashed, expiring sign-up codes | by email |
| `projects` | The MPLAD work record | 1→N everything below |
| `fund_updates` | Installment-wise release and expenditure trail | N→1 project |
| `progress_updates` | Physical progress trail with milestones | N→1 project |
| `reviews` | Persisted review workflow (FR13) | N→1 project, N→1 reviewer |
| `notes` | Internal administrative notes | N→1 project, N→1 author |
| `risk_assessments` | One explainable assessment at a point in time | N→1 project |
| `risk_factors` | Individual detected indicators with their evidence | N→1 assessment |
| `mitigation_actions` | Tracked, assignable actions against a risk | N→1 assessment, N→1 project |
| `activity_logs` | Append-only audit trail | N→1 project (nullable for scheme-wide actions) |
| `citizen_reports` | Community feedback (FR7) | N→1 project, N→1 reporter |

```
users ──< reviews >── projects ──< fund_updates
  │                      │      ──< progress_updates
  └──< notes >───────────┤      ──< citizen_reports
                         │      ──< activity_logs
                         └──< risk_assessments ──< risk_factors
                                     │          ──< mitigation_actions
                                     └── is_current flag marks the live one
```

## Design notes

**Assessments are versioned, not overwritten.** Each run inserts a new
`risk_assessments` row and clears `is_current` on the previous one, so the
history of how a work's risk evolved is preserved and queryable
(`GET /api/admin/projects/{id}/risk/history`). Unresolved, human-authored
mitigation actions are carried forward onto the new assessment; engine-generated
recommendations are regenerated.

**Findings are relational, not a JSON blob.** `risk_factors` is a proper table
with `code`, `category`, `severity`, `source`, `contribution`, `metric_name`,
`metric_value` and `threshold_value` columns, so the analytics page can group and
count indicators in SQL rather than parsing documents.

**Denormalised totals are derived, not authoritative.** `projects.spent_amount`
and `projects.progress_percent` are recomputed from the fund and progress trails
whenever an entry is added (`project_service.recalculate_totals`).

**Enums are stored as strings** (`native_enum=False`), which keeps migrations
simple across both engines and makes the database readable without a decoder
ring.

## Indexes

Every filterable column is indexed: `project_code` (unique), `mp_name`,
`district`, `state`, `category`, `executing_agency`, `sanction_year`, `status`,
`review_status`, plus composite indexes on `(district, category)` and
`(status, sanction_year)`. Foreign keys on the child tables are indexed, as are
`risk_assessments.is_current` and `risk_assessments.assessed_at`.

## Schema creation and migrations

For the hackathon build the schema is created directly from the SQLAlchemy
metadata at application startup and by the seed script, which keeps
`docker compose up` a single step:

```python
Base.metadata.create_all(bind=engine)
```

A production deployment would introduce Alembic:

```bash
pip install alembic
alembic init migrations
# point migrations/env.py at app.database.base:Base.metadata
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

The models are written against SQLAlchemy 2.0's typed `Mapped[...]` style, which
autogenerate reads cleanly.

## Seeding

```bash
python -m seed.seed_data --reset --projects 600
python -m seed.seed_data --reset --projects 5200   # the dataset size in SRS §2.4
```

`--seed` fixes the RNG (default `20260101`), so a given invocation reproduces the
same dataset. The generator produces multiple states, districts, constituencies,
fictional MPs, work categories and executing agencies across six sanction years,
with a deliberate mix of execution profiles: healthy complete, healthy ongoing,
not started, slow progress, overdue, and four injected anomaly patterns —
expenditure running ahead of progress, underspend late in the window, cost
overrun, and stalled works. A small share of records is left deliberately
incomplete so the data-quality rule has real input, and a few descriptions are
duplicated within a district so the near-duplicate detector has something
genuine to find.

It then generates reviews, notes, citizen reports, risk assessments, risk factors
and mitigation actions — roughly a third of which are advanced to *In Progress*
or *Resolved* so the tracker does not look untouched.
