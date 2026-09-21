# SRS traceability (SIH26102)

Every functional and non-functional requirement from the SRS, and where it is
implemented. Terminology follows the SRS.

## 4.1 Authentication & access control

| ID | Requirement | Implementation |
|---|---|---|
| FR1 | Citizens sign up / log in by email + OTP (lightweight, no KYC) | `POST /api/auth/signup/request-otp` → `POST /api/auth/signup/verify`; `backend/app/auth/otp.py`; UI `frontend/src/pages/SignupPage.tsx`. OTP codes are hashed at rest, expire after `OTP_EXPIRY_MINUTES`, and lock after 5 wrong attempts. In development delivery the code is returned as `dev_otp` and logged, so the demo needs no mail provider; in production that field is never populated. |
| FR2 | Officials/auditors log in with role-assigned credentials (Citizen / Officer / Auditor / Admin) | `POST /api/auth/login`; roles in `backend/app/core/enums.py`; administrator-only provisioning at `POST /api/auth/officials`. |
| FR3 | Sensitive fields (raw anomaly scores, internal flags) restricted from the Citizen role | Enforced by **separate endpoints**, not by filtering: `/api/projects/*` is served from `ProjectPublicSummary` / `ProjectPublicDetail`, which have no risk fields; every `/api/admin/*` route carries `require_internal` or stricter. A citizen token calling an admin route receives HTTP 403 `insufficient_role`. |

## 4.2 Citizen transparency portal

| ID | Requirement | Implementation |
|---|---|---|
| FR4 | Search / filter by MP, district, category, year, status | `GET /api/projects` with those parameters plus free-text search over code, title, description, agency and location. Executed in SQL (`project_service.build_project_query`), paginated server-side. UI: `pages/ProjectsPage.tsx` with `features/citizen/ProjectFilters.tsx`. |
| FR5 | View allocated funds, spent funds, timeline, agency, completion status | `GET /api/projects/{id}` → `ProjectPublicDetail`, including the fund-update and progress-update trails and the derived spending / progress timelines. |
| FR6 | Simplified, public-safe risk indicator, not raw ML scores | `PublicRiskIndicator` = `Normal` \| `Under Review`, derived in `project_service.public_indicator` from review status, execution status and whether the internal level is HIGH/CRITICAL. The numeric score never appears in a citizen response. |
| FR7 | Citizens can flag / report a project (community feedback) | `POST /api/projects/{id}/reports`, `GET /api/projects/{id}/my-reports` (a citizen sees only their own). Officials triage at `PATCH /api/admin/citizen-reports/{id}`. Clustered open reports feed the risk engine as an implementation-risk indicator. |
| FR7a | Citizen scheme detail page `/scheme/{id}` with fund breakdown, utilisation chart, agency and contractor, photos/documents | `pages/SchemeDetailPage.tsx`. |
| FR7b | A **completely separate** admin/auditor detail page at a distinct role-protected route, adding raw score, flagged-reason breakdown, explainability and internal notes | `/admin/scheme/{id}` → `pages/admin/AdminSchemeDetailPage.tsx`, a different component backed by a different API. |

## 4.3 AI anomaly / fraud detection engine

| ID | Requirement | Implementation |
|---|---|---|
| FR8 | Ingest project records and compute a risk score | `app/risk/engine.py` `assess_project()`; persisted by `services/risk_service.run_assessment()` as a `RiskAssessment` with its `RiskFactor` rows. Three layers contribute: deterministic rules, peer-cohort statistics, and an unsupervised isolation forest (`app/risk/anomaly.py`) fitted on the live population. `GET /api/admin/risk-engine` reports which are live. |
| FR9 | Detect cost overruns, abnormal delays, duplicate / near-duplicate descriptions, budget-deviation outliers | Cost overrun: `rule_cost_overrun`. Delays: `rule_schedule_slippage`, `rule_overdue_incomplete`, `rule_deadline_imminent_low_progress`, `rule_status_delayed`, `rule_stalled_reporting`. Duplicates: `risk/duplicate.py` (TF-IDF cosine within a district; embedding backend pluggable). Budget deviation: `risk/statistical.py` allocation and cost-per-beneficiary z-scores within a category. |
| FR10 | Ranked list of high-risk projects for auditor review, framed as "flagged for investigation", never as confirmed fraud | `GET /api/admin/projects/flagged`; UI `pages/admin/AdminFlaggedPage.tsx`. The wording appears in the page description, the engine's own `notes` field and the disclaimer on every risk panel. |

**On the machine-learning requirement.** The SRS names XGBoost and
sentence-transformers. What ships is an **unsupervised isolation forest**
(`app/risk/anomaly.py`) rather than a supervised classifier, and the reasoning is
a design decision rather than a shortcut: real MPLADS data is unavailable
(SRS §2.4), so a supervised model would be trained on labels this project
generates itself. It would learn the generator, and any accuracy figure quoted
for it would measure nothing. An isolation forest needs no labels at all — it is
fitted on whatever population is in the database and flags the records that sit
apart from it, so pointing it at real ministry data requires no retraining on
hand-made examples and no code change.

It earns its place: it works on an 11-dimensional feature vector and catches
records where every individual figure is within its own acceptable band but the
*combination* occurs nowhere else in the cohort — which a threshold rule cannot
express. Each finding reports the score, its percentile against the population,
and the three features that drove it as robust z-scores against the cohort
median, so it is explainable to a reviewing officer rather than a black box.
Its factor is weighted at 0.16 and never sets the risk level alone.

The remaining upgrades stay as drop-in layers: `DUPLICATE_BACKEND=embeddings`
switches duplicate detection to sentence-transformers when the package is
installed, and a supervised model can be added as a fifth `AnalysisSource`
against real labelled data without touching the API. See `docs/ASSUMPTIONS.md`.

## 4.4 Admin / auditor dashboard

| ID | Requirement | Implementation |
|---|---|---|
| FR11 | Full risk dashboards, drill-down into individual anomaly explanations (feature importances) | `GET /api/admin/dashboard`, `GET /api/admin/analytics`; drill-down at `GET /api/admin/projects/{id}/risk`, which returns each factor's score contribution, weight, detected indicator, evidence, metric value and threshold. For the machine-learning factor this is a literal feature attribution: the model reports the ranked per-feature robust z-scores that produced the anomaly score. The Analytics page carries a live card showing which layers are active and what the model was fitted on. |
| FR12 | Export flagged reports | `GET /api/admin/projects/export?format=csv\|pdf` honours the current filters or `flagged_only=true`, and every export writes an audit entry naming the format. CSV carries all 22 columns for analysis; PDF is a paginated landscape A4 report generated by `app/services/pdf_writer.py` with no third-party dependency. UI: **Export** on the works register and the flagged list offers both. |
| FR13 | Mark a flagged case reviewed / resolved / escalated | `POST /api/admin/projects/{id}/reviews` with `ReviewStatus` ∈ {Pending Review, Reviewed, On Track, Delayed, Escalated, Resolved}. Reviews are rows in the database, not frontend state, and every review writes to the audit trail. Risk status has its own lifecycle at `PATCH /api/admin/projects/{id}/risk/status`. |

## 4.5 Data management

| ID | Requirement | Implementation |
|---|---|---|
| FR14 | Full CRUD on project records | `POST`, `GET`, `PATCH`, `DELETE /api/admin/projects[/{id}]`, plus fund-update and progress-update sub-resources. UI: "New work" and "Bulk import" on the register, "Edit record" on the detail page, and a delete action in the register that is rendered only for an Administrator and confirmed before it fires. |
| FR15 | Bulk data import | `POST /api/admin/projects/bulk-import` (Auditor/Admin), reporting created, skipped and per-row errors. UI: **Bulk import** on the works register parses the CSV in the browser, shows the row count and every rejected row before anything is sent, and the API re-validates each row server-side. |

## 5. Non-functional requirements

| Category | Requirement | Implementation |
|---|---|---|
| Usability | Fully responsive; accessible colour system; WCAG-AA contrast | Tailwind breakpoints throughout; 44px minimum tap targets (`.tap-target`); visible focus ring on every interactive element; status is never carried by colour alone (badges pair a dot or an icon with text). The chart palette was validated for lightness band, chroma floor, colour-vision-deficiency separation and contrast against the chart surface. |
| Performance | API responses < 500ms for standard queries; risk scoring as a batch job, not real-time blocking | Indexed columns for every filter (`district`, `category`, `status`, `sanction_year`, `mp_name`, plus two composite indexes); server-side pagination everywhere; every response carries `X-Response-Time-ms`. Scheme-wide re-scoring is a separate batch endpoint (`POST /api/admin/risk/recompute-all`) that builds the peer index and cohort statistics once. |
| Security | JWT auth, hashed credentials, RBAC-enforced field-level masking for the Citizen role | bcrypt password hashing; HS256 JWTs with separate access and refresh token types; the role is re-read from the database on every request; masking by schema, not by filtering. See `docs/SECURITY.md`. |
| Scalability | Modular layers allow the AI engine to scale independently of the API | `app/risk/` has no runtime ORM dependency and is invoked through a single service function, so it can be lifted into its own process behind a queue without changing the routers. |
| Availability | 99% uptime target framing | Container healthchecks on the API and the database; `GET /api/health` reports database connectivity; stateless API instances scale horizontally behind a load balancer. |
| Auditability | All admin actions (review / resolve / escalate) logged with timestamp and user ID | `ActivityLog` is append-only and records actor id, name, role, action type, from/to values and a timestamp. Written on status change, review, risk assessment, risk-level change, note, mitigation add/update/resolve, progress and fund entries, export and citizen-report triage. |

## 6. UI/UX specification

| Requirement | Implementation |
|---|---|
| Deep navy/indigo primary with a restrained saffron accent | `tailwind.config.js` `ink` + `saffron` scales; no literal tricolour. |
| Government-style top bar with emblem placeholder | `PublicLayout` identity strip; `components/layout/Emblem.tsx` is an abstract civic mark, deliberately **not** the State Emblem of India, which may not be reproduced without authorisation. |
| GIGW basics: high contrast, clear hierarchy, accessible fonts | Inter, rem-based type, semantic headings, `:focus-visible` rings, skip-free tab order. |
| Card layouts for citizens, dense tables for officials | `ProjectCard` vs `AdminProjectTable` (which also has a card layout below `md`). |
| Colour-coded, colourblind-safe status badges | `components/ui/Badge.tsx`; status meaning is always carried by the label too. |
| Fund utilisation charts, timeline bars | `components/charts/` (Recharts, auto-resizing). |
| Responsive breakpoints 375 / 768 / 1440 | Single-column stacked cards below `sm`, two-column from `sm`, sidebar collapses to a drawer below `lg`, multi-column dashboard from `xl`. |

## 7. Data requirements

| Entity | Model |
|---|---|
| Project (`project_id`, MP, district, category, agency, allocated_fund, spent_fund, start_date, end_date, status, description) | `models/project.py`, extended with constituency, house, block, location, coordinates, contractor, sanction year and date, estimate, beneficiaries, planned progress and review status. |
| Risk (`project_id` FK, risk_score, risk_category, flagged_reasons, model_version, reviewed_status) | `models/risk.py` — `RiskAssessment` (score, level, likelihood, impact, primary category, status, `engine_version`, `analysis_sources`) with `RiskFactor` rows carrying the flagged reasons and their evidence, and `MitigationAction` rows tracking what is being done. |
| User (`user_id`, role, email, auth_hash) | `models/user.py`, plus designation, department, district and verification state. |
