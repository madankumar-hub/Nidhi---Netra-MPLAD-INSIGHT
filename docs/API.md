# API reference

Base path `/api`. All responses are JSON except the CSV export. Errors share one
envelope: `{ "code": "...", "message": "...", "detail": null }`.

Authentication is `Authorization: Bearer <access_token>`.

**Role column key** — *public*: no token needed · *any*: any signed-in account ·
*internal*: Officer, Auditor, Admin · *reviewer*: Officer, Auditor, Admin (write)
· *elevated*: Auditor, Admin · *admin*: Admin only.

---

## System

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/` | public | Service banner |
| GET | `/api/health` | public | Liveness + database connectivity |
| GET | `/docs` | public | Interactive OpenAPI documentation |

## Authentication — `/api/auth`

| Method | Path | Role | Purpose |
|---|---|---|---|
| POST | `/login` | public | Email + password → access & refresh tokens |
| POST | `/signup/request-otp` | public | Step 1 of citizen sign-up (FR1) |
| POST | `/signup/verify` | public | Step 2: verify the code, create the account |
| POST | `/refresh` | public | Exchange a refresh token for a new pair |
| POST | `/logout` | any | Client discards its tokens |
| GET | `/me` | any | The signed-in account |
| POST | `/change-password` | any | Requires the current password |
| GET | `/officials` | admin | List all accounts |
| POST | `/officials` | admin | Provision an Officer / Auditor / Admin (FR2) |
| GET | `/access-policy` | public | Which email domains may request official access |
| GET | `/requestable-roles` | public | Officer and Auditor only — never Administrator |
| POST | `/request-official-access` | any | Ask to be granted an official role. Creates a request; changes nothing |
| GET | `/my-access-requests` | any | The caller's own requests and their outcome |

### Access control — `/api/admin` (Administrator only)

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/admin/access-requests` | admin | The approval queue; optional `status` filter |
| GET | `/admin/access-policy` | admin | The configured allowlist |
| POST | `/admin/access-requests/{id}/decide` | admin | Approve (granting the role) or decline; audited |
| GET | `/admin/users` | admin | All accounts, optional `role` filter |
| POST | `/admin/users/{id}/revoke` | admin | Return an official account to Citizen |

## Citizen portal — `/api/projects`

Public-safe only. No risk score, no factors, no notes, no reviews, no audit trail.

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/api/projects` | public | Search & filter (FR4). Parameters: `search`, `mp`, `district`, `state`, `category`, `agency`, `year`, `status`, `sort_by`, `sort_dir`, `page`, `page_size` |
| GET | `/api/projects/filters` | public | Facet lists with counts for the filter controls |
| GET | `/api/projects/statistics` | public | Public aggregate figures |
| GET | `/api/projects/{id}` | public | Scheme detail (FR5, FR7a) with fund and progress trails and derived timelines |
| POST | `/api/projects/{id}/reports` | any | File a citizen report (FR7) |
| GET | `/api/projects/{id}/my-reports` | any | The caller's own reports on this work |

## Officials' portal — `/api/admin`

Every route below returns **403 `insufficient_role`** to a Citizen token.

### Works register

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/admin/projects` | internal | Register with risk, review and mitigation state. Adds `review_status`, `risk_level`, `overdue_only` and `min_allocation` / `max_allocation` filters |
| GET | `/admin/projects/filters` | internal | Facet lists |
| GET | `/admin/projects/flagged` | internal | Ranked flagged list (FR10). `limit`, `min_score` |
| GET | `/admin/projects/export` | internal | CSV export (FR12). Honours filters or `flagged_only=true` |
| POST | `/admin/projects` | reviewer | Create a work record (FR14) |
| POST | `/admin/projects/bulk-import` | elevated | Bulk import (FR15) |
| GET | `/admin/projects/{id}` | internal | Full administrative detail (FR7b) |
| PATCH | `/admin/projects/{id}` | reviewer | Update the record; triggers re-assessment |
| DELETE | `/admin/projects/{id}` | elevated | Delete the record and its children |
| POST | `/admin/projects/{id}/status` | reviewer | Execution-status transition with a reason; audited |

### Fund and progress trails

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/admin/projects/{id}/fund-updates` | internal | Expenditure entries |
| POST | `/admin/projects/{id}/fund-updates` | reviewer | Record expenditure; recomputes totals and risk |
| GET | `/admin/projects/{id}/progress` | internal | Progress entries |
| POST | `/admin/projects/{id}/progress` | reviewer | Record progress; recomputes totals and risk |

### Risk (FR8–FR11)

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/admin/risk-engine` | internal | Which analysis layers are actually active |
| GET | `/admin/projects/{id}/risk` | internal | Current assessment with factors and mitigation |
| POST | `/admin/projects/{id}/risk/recompute` | reviewer | Re-assess. `{ "use_external_ai": false }` |
| GET | `/admin/projects/{id}/risk/history` | internal | Previous assessments |
| PATCH | `/admin/projects/{id}/risk/status` | reviewer | Open / Under Review / Mitigated / Accepted / Closed |
| POST | `/admin/risk/recompute-all` | reviewer | Batch re-scoring across the scheme |

### Mitigation

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/admin/projects/{id}/mitigation` | internal | Actions for this work |
| POST | `/admin/projects/{id}/mitigation` | reviewer | Add an action with a responsible party and due date |
| PATCH | `/admin/mitigation/{id}` | reviewer | Update action, party, status, priority, due date, notes |
| POST | `/admin/mitigation/{id}/resolve` | reviewer | Mark resolved; records who and when |

### Reviews, notes, activity (FR13)

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/admin/projects/{id}/reviews` | internal | Review history |
| POST | `/admin/projects/{id}/reviews` | reviewer | Record a review; updates review status and audits |
| GET | `/admin/review-queue` | internal | Most recent reviews across the scheme |
| GET | `/admin/projects/{id}/notes` | internal | Internal notes, optional `note_type` filter |
| POST | `/admin/projects/{id}/notes` | reviewer | Add a note |
| PATCH | `/admin/notes/{id}` | reviewer | Edit your own note (Auditor/Admin may edit any) |
| DELETE | `/admin/notes/{id}` | reviewer | Delete your own note (Auditor/Admin may delete any) |
| GET | `/admin/projects/{id}/activity` | internal | Audit trail for one work |
| GET | `/admin/activity` | internal | Scheme-wide recent activity |

### Citizen reports

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/admin/citizen-reports` | internal | All reports; optional `project_id`, `status` |
| GET | `/admin/projects/{id}/citizen-reports` | internal | Reports on one work |
| PATCH | `/admin/citizen-reports/{id}` | reviewer | Triage and publish an official response |

### Analytics (FR11)

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/admin/dashboard` | internal | Headline counters |
| GET | `/admin/analytics` | internal | Everything the analytics page charts |
| GET | `/admin/delayed-projects` | internal | Works marked Delayed |
| GET | `/admin/pending-review` | internal | Works awaiting a first review |

---

## Worked example: risk drill-down

```http
GET /api/admin/projects/42/risk
Authorization: Bearer <auditor token>
```

```jsonc
{
  "id": 91,
  "project_id": 42,
  "risk_score": 68.4,
  "risk_level": "HIGH",
  "likelihood": "Likely",
  "impact": "Major",
  "primary_category": "Schedule Risk",
  "status": "Open",
  "summary": "HIGH risk. Principal indicator: project is past its planned completion date and still open and 3 further indicators.",
  "analysis_sources": ["rule_based", "statistical"],
  "engine_version": "mplad-risk-engine-1.0",
  "ai_model_used": null,
  "ai_narrative": null,
  "data_completeness_percent": 100.0,
  "factors": [
    {
      "code": "OVERDUE_INCOMPLETE",
      "title": "Project is past its planned completion date and still open",
      "category": "Schedule Risk",
      "severity": "CRITICAL",
      "source": "rule_based",
      "contribution": 22.6,
      "weight": 0.24,
      "detected_indicator": "Planned completion was 2025-03-31 - 173 days ago - and the work is still recorded as 'Delayed' at 41.0%.",
      "evidence": "Planned end date 2025-03-31; today 2025-09-20; status Delayed; progress 41.0%; unspent balance Rs 11.80 lakh.",
      "explanation": "An overdue open work blocks the constituency entitlement from being recycled and is the single strongest predictor of eventual cost escalation in MPLAD execution data.",
      "recommended_action": "Record a formal delay reason, set the review status to Delayed or Escalated, and obtain a dated completion commitment from the executing agency.",
      "metric_name": "days_overdue",
      "metric_value": 173.0,
      "threshold_value": 0.0
    }
  ],
  "mitigations": [ /* … */ ]
}
```

`analysis_sources` states exactly which layers contributed. When external AI is
not configured it is absent from that list and `ai_narrative` is `null` — the
interface then says so rather than implying a model was involved.
