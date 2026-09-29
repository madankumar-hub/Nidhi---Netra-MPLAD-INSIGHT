# Nidhi Netra

**Smart India Hackathon 2026 — Problem Statement SIH26102**

Nidhi Netra is a web application for monitoring and analysing development
works carried out under the Members of Parliament Local Area Development
Scheme (MPLADS).

The main idea is simple: information about a project should not stop at its
sanction. The system makes it possible to follow a project from sanction and
allocation through to expenditure, physical progress, review and
completion. At the same time, officials need a different view of the same
information — which projects are delayed, which need review, where spending
and physical progress do not match, and which records may need further
investigation.

## Resources

- **Live Prototype:** https://mplad-web.onrender.com/
- **Project Report:** https://docs.google.com/document/d/1MJsPMmifSIOTMEDHz3slvrIJoyF9UAHP/edit?usp=sharing
- **Video Walkthrough (Drive Link) :** https://drive.google.com/file/d/1RyqAPTSrK_8aFqG2QDogjsi3XAEsTKNt/view?usp=sharing
- **Video Walkthrough (Youtube) :** https://www.youtube.com/watch?v=HE4-WlDmaus

## Two portals, one system

Nidhi Netra has two separate interfaces, and the information shown to each
is intentionally different. Internal risk analysis and administrative
information is never exposed through the citizen-facing APIs.

- **Citizen Portal** — for viewing project information, expenditure,
  progress and submitting issues.
- **Officials/Admin Portal** — for project monitoring, risk analysis,
  reviews, notes, mitigation actions and administrative workflows.

## What problem are we trying to solve?

Monitoring a large number of development works manually makes it difficult
to identify the projects that need attention. A project may have:

- very little physical progress despite considerable money spent
- an approaching completion date with significant work still pending
- expenditure higher than expected
- no expenditure after the project has started
- unusually high or low spending compared with similar projects
- incomplete or inconsistent project information
- repeated citizen complaints
- or a combination of several unusual indicators

Reviewing every project individually is time-consuming. Nidhi Netra uses a
combination of rule-based checks, statistical analysis and an unsupervised
anomaly-detection model to bring such projects to officials' attention.
**A flag is not a claim of fraud** — it means the project deserves further
review. The final decision always remains with the responsible official.

## Main Features

### Citizen project portal

Citizens can browse and search development works without accessing internal
administrative information:

- project search and details
- sanctioned amount, expenditure, remaining amount
- physical progress and project status
- timeline and location information
- project documents and site photographs
- citizen issue/report submission

### Officials/Admin dashboard

Officials get access to everything required for monitoring and review:

- project listing and filtering
- progress and expenditure monitoring
- delayed-project identification, projects awaiting review
- risk analysis with indicators and explanations
- mitigation actions, review records, internal notes
- citizen reports, activity/audit history
- financial and progress updates
- CSV/PDF export
- administrative access management

The goal is for an official to go from
**Project → Risk → Evidence → Review → Action → Follow-up**
without leaving the system.

## Risk Analysis

The risk engine is one of the core parts of the project. More than one
method is used deliberately, because no single threshold can reliably catch
every kind of unusual project.

**Rule-based checks** — deterministic conditions such as schedule delay, an
approaching deadline with incomplete work, overdue projects, expenditure
outpacing physical progress, unusually low expenditure near completion, cost
overrun, stalled updates, zero expenditure after commencement, inconsistent
completion information, incomplete records, and a concentration of citizen
reports.
`backend/app/risk/rules.py`

**Statistical checks** — comparing a project against similar projects:
allocation outliers, cost-per-beneficiary outliers, and similar/duplicate
project descriptions.
`backend/app/risk/statistical.py`, `backend/app/risk/duplicate.py`

**Anomaly detection** — an unsupervised Isolation Forest model that looks at
multiple project features together, catching cases where no single value is
unusual but their combination is. It needs no labelled fraud data, which
matters for a prototype built on a realistic synthetic dataset rather than a
complete labelled dataset of real MPLADS fraud cases.
`backend/app/risk/anomaly.py`

**Optional external AI** — can generate a short, reviewer-friendly summary
of an already-detected finding. It never decides the risk score; the
deterministic and statistical layers calculate the actual indicators. This
integration is disabled unless an API key is configured.
`backend/app/risk/ai_provider.py`

```
Rules
  ↓
Statistical checks
  ↓
Anomaly detection
  ↓
Human review
  ↓
Mitigation / follow-up
```

### What an official sees for a risk

Every finding answers four questions instead of showing a bare number:

1. **What is the risk?** — a short description of the issue
2. **Why was it detected?** — the condition or indicator that triggered it
3. **What data caused it?** — the value, metric and threshold behind it
4. **What should be done?** — a suggested next step, convertible into a
   mitigation action

## Citizen and Official Access

| Role | Citizen Portal | Official Portal | Risk Information | Internal Notes |
|---|:---:|:---:|:---:|:---:|
| Citizen | Yes | No | No | No |
| District/Field Officer | Yes | Yes | Yes | Yes |
| Auditor | Yes | Yes | Yes | Yes |
| Administrator | Yes | Yes | Yes | Yes |

This separation is enforced on the backend, not just hidden in the
frontend. Every internal API checks the authenticated user's role against
the database before allowing access.

## Technology Stack

**Backend:** Python, FastAPI, SQLAlchemy, Pydantic, PostgreSQL (SQLite for
local development), PyJWT, bcrypt

**Frontend:** React, TypeScript, Vite, Tailwind CSS, React Router, Recharts,
Leaflet, Lucide React

**Analysis:** Python-based rule engine, statistical outlier detection,
TF-IDF similarity for duplicate detection, Isolation Forest anomaly
detection, optional external AI provider

## Project Structure

```
mplad-insight/
│
├── backend/
│   ├── app/
│   │   ├── auth/
│   │   ├── core/
│   │   ├── database/
│   │   ├── models/
│   │   ├── risk/
│   │   ├── routers/
│   │   ├── schemas/
│   │   └── services/
│   ├── seed/
│   ├── tests/
│   ├── tools/
│   ├── .env.example
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   └── features/
│   │       ├── admin/
│   │       ├── auth/
│   │       ├── citizen/
│   │       └── map/
│   ├── .env.example
│   └── package.json
│
├── docs/
├── docker-compose.yml
├── Procfile
├── README.md
└── .gitignore
```

## Running the Project Locally

**Requirements:** Python 3.11+, Node.js, npm. PostgreSQL is optional — the
app runs on SQLite locally.

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env   # copy manually on Windows if cp is unavailable

python -c "import secrets; print(secrets.token_urlsafe(48))"
# put the generated value in .env as JWT_SECRET_KEY=your-generated-secret

python -m seed.seed_data --reset --projects 600
uvicorn app.main:app --reload --port 8000
```

- Backend: http://localhost:8000
- API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # if required
npm run dev
```

Available at http://localhost:5173. During development, Vite proxies
`/api` requests to the backend.

### Demo Accounts

The seed script creates accounts for each role. If
`SEED_ADMIN_PASSWORD` / `SEED_AUDITOR_PASSWORD` / `SEED_OFFICER_PASSWORD` /
`SEED_CITIZEN_PASSWORD` are left empty, random passwords are generated and
written to `backend/.seed-credentials.txt` (git-ignored). Never commit
`.env` or `.seed-credentials.txt`.

### Docker

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

- Web: http://localhost:8080
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Database

PostgreSQL is the intended database for deployment; SQLite is fine for
local development.

```
# SQLite
DATABASE_URL=sqlite:///./mplad_insight.db

# PostgreSQL
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE
```

Database credentials are always supplied through environment variables and
are never committed to Git.

## API

Built with FastAPI. Main areas: `/api/auth/...`, `/api/public/...`,
`/api/admin/projects/...`, `/api/admin/risk/...`, `/api/admin/analytics/...`,
`/api/admin/workflow/...`, `/api/admin/access/...`. Full documentation in
`docs/API.md`, and interactively at `/docs` while the backend is running.

## Security

Security was part of the application design, not an afterthought:

- JWT-based authentication, bcrypt password hashing
- role-based access control, checked server-side against the database
- rate limiting on sensitive endpoints
- separate citizen and internal API routes
- environment-based secrets; no committed `.env` files or credentials
- audit/activity records for important actions
- protected administrative operations

The backend never trusts a role value supplied only by the frontend. See
`docs/SECURITY.md` for details.

## Testing and Verification

Covers authentication and access control, security, rate limiting, the risk
engine, anomaly detection, geography, project schemas, PDF export, API
contracts, accessibility, sample data, and deployment safety.

```bash
cd backend
python -m tests.run_all
# or: pytest tests/
python tools/static_check.py

cd frontend
npm run typecheck
npm run build
```

## Sample Data

The project currently uses a realistic synthetic dataset for development
and demonstration — not an official MPLADS database. Connecting to a real
government data source would require adapting the ingestion and
field-mapping layer to the official data format.

## Current Limitations

This is a working prototype. Planned improvements include:

- integration with an official MPLADS/data.gov.in data source
- more complete geographic visualization
- real OTP/email delivery
- production database migrations
- larger-scale performance testing
- additional document verification
- more advanced duplicate detection
- automated notifications
- additional regional-language support
- production deployment hardening

None of this is hidden — `docs/` contains architecture, assumptions and
deployment documentation describing these gaps in detail.

## Documentation

| Document | Description |
|---|---|
| `ARCHITECTURE.md` | Application architecture |
| `API.md` | API endpoints and contracts |
| `DATABASE.md` | Database structure |
| `SECURITY.md` | Security design |
| `DEPLOYMENT.md` | Deployment instructions |
| `DATA_INGESTION.md` | Data import approach |
| `MAP_MODULE.md` | Geographic/map functionality |
| `VERIFICATION.md` | Testing and verification |
| `TEST_CHECKLIST.md` | Test checklist |
| `ASSUMPTIONS.md` | Current project assumptions |
| `DEMO_SCRIPT.md` | Demonstration flow |

## Team & Contributions

Nidhi Netra was built by a 6-member team, **Astryn**, for Smart India
Hackathon 2026, problem statement SIH26102. The repository was pushed as a
single upload by one teammate, so GitHub's contributor graph does not
reflect individual authorship. Actual contribution areas were:

| # | Name | Contribution Area | Branch / Year |
|---|------|-------------------|----------------|
| 1 | Chetan Didwaniya (Team Leader) | Database design, deployment | CSE-DS / 2nd |
| 2 | Vomesh Mandiya | AI/ML research & development (risk engine) | ECE / 2nd |
| 3 | Nakshtra Kularia | Backend, map module | ECE / 2nd |
| 4 | Madan Kumar | UI/UX, frontend | CSE-IOT / 2nd |
| 5 | Gargi Bindal | Internationalization (i18n), backend | CSE-DS / 2nd |
| 6 | Shailja Malani | Research, documentation | CSE-AI / 1st |

## A note about the project

Nidhi Netra is a prototype built to demonstrate how project monitoring,
citizen transparency and risk-based review can be brought into one system.
It is not meant to replace the judgement of government officials — the
intention is to reduce the manual checking required to find projects that
deserve attention, and to keep the review that follows traceable.
