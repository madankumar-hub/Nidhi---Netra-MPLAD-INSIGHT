# MPLAD Insight

**AI-Powered Anomaly, Fraud & Inefficiency Detection System for the MPLAD Scheme**
Smart India Hackathon 2026 · Problem statement **SIH26102**

MPLAD Insight does two things that usually live in separate systems:

* a **citizen transparency portal**, where any registered member of the public can
  search a sanctioned work, follow its money from allocation to expenditure, and
  track physical progress; and
* an **officials' oversight portal**, where district officers, auditors and scheme
  administrators examine the same records for anomalies, delays and inefficiency,
  record reviews, raise mitigation actions and leave an audit trail.

The two surfaces are deliberately separated — different routes, different
components and, crucially, **different APIs**. Risk scores, risk reasoning,
mitigation tracking, internal notes and the audit trail are served only under
`/api/admin/...`, which rejects the Citizen role with HTTP 403 regardless of what
the client sends.

---

## Contents

| Path | What it holds |
|---|---|
| `backend/` | FastAPI application, SQLAlchemy models, risk engine, seed data |
| `frontend/` | React + TypeScript + Vite + Tailwind single-page app |
| `docs/` | Architecture, API reference, database, security, SRS traceability |
| `tools/` | Dependency-free static checks that run without installing anything |
| `docker-compose.yml` | Postgres + API + web, one command |

---

> **Hit an error?** `TROUBLESHOOTING.md` covers the common ones — missing C++
> build tools, `uvicorn` not recognised, the double-nested extract folder,
> PowerShell execution policy, and switching to PostgreSQL.

## Quick start (VS Code)

Open the project folder in VS Code, accept the recommended extensions, then
**Ctrl+Shift+P → Tasks: Run Task → `Setup: everything`**, and press **F5** with
**`▶ Full stack (API + web)`** selected. Full walk-through in
[`docs/VSCODE.md`](docs/VSCODE.md).

## Quick start (local, no Docker)

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Generate a signing key and paste it into .env as JWT_SECRET_KEY:
python -c "import secrets; print(secrets.token_urlsafe(48))"

# Seed the realistic synthetic dataset (creates the SQLite file by default).
python -m seed.seed_data --reset --projects 600

uvicorn app.main:app --reload --port 8000
```

The API is then on <http://localhost:8000>, with interactive documentation at
<http://localhost:8000/docs>.

> **Accounts.** Passwords are never hardcoded. If you leave the `SEED_*_PASSWORD`
> variables blank, the seed script generates strong random passwords, prints them
> once and writes them to `backend/.seed-credentials.txt` (git-ignored — delete it
> when you are done). Set the variables in `.env` first if you would rather choose
> your own. Four accounts are created: an administrator, an auditor, a district
> officer and a citizen.

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env               # optional; defaults work with the dev proxy
npm run dev
```

The app is then on <http://localhost:5173>. The Vite dev server proxies `/api` to
`http://localhost:8000`, so no CORS configuration is needed in development.

If you already had the project running, reseed once so that works get their
placeholder site photographs and sanction documents:

```bash
cd backend
python -m seed.seed_data --reset --projects 600
```

`--reset` rebuilds the database. Your administrator account is recreated from
`SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` in `backend/.env`.

### Verify everything

```bash
./verify.sh          # macOS / Linux / Git Bash
VERIFY.bat           # Windows (or double-click it)
```

Runs the backend test suite, the route/import static check, the API contract
check, the translation check and the TypeScript check. None of them need the
npm registry or a database, so this works on a fresh clone.

### 3. Production build

```bash
cd frontend
npm run build      # runs tsc, then vite build; output in frontend/dist
npm run preview
```

---

## Deploying it

`docs/DEPLOYMENT.md` walks through putting the three pieces online — managed
PostgreSQL, the FastAPI service and the static web app — using the `render.yaml`
blueprint in the repository root, with notes for Railway, Docker and split
static hosting.

## Quick start (Docker)

```bash
cp backend/.env.example backend/.env     # fill in JWT_SECRET_KEY
export POSTGRES_PASSWORD='choose-a-strong-password'

docker compose up --build
docker compose exec api python -m seed.seed_data --reset
```

* Web app: <http://localhost:8080>
* API: <http://localhost:8000/docs>

---

## PostgreSQL vs SQLite

PostgreSQL is the target database (SRS §2.3) and is what `docker compose` runs.
SQLite is supported for zero-configuration local development and needs no extra
packages. For PostgreSQL, install the optional driver first:

```bash
pip install -r requirements-postgres.txt
```

Then set one of:

```ini
DATABASE_URL=postgresql+psycopg://mplad:PASSWORD@localhost:5432/mplad_insight
DATABASE_URL=sqlite:///./mplad_insight.db
```

Everything else is identical; no code branches on the database.

---

## The risk engine, stated plainly

Risk levels and scores are produced by **two deterministic layers**, and an
optional third layer that never touches the number:

1. **Rule-based** (`backend/app/risk/rules.py`) — thresholds over the project
   record: schedule slippage against the sanctioned timeline, an imminent
   deadline with work outstanding, an overdue open work, expenditure running
   ahead of physical progress, underspend late in the project window, cost
   overrun against the estimate, stalled progress reporting, zero expenditure
   after commencement, completion inconsistencies, incomplete records, and
   clustered citizen reports. **Always runs. No network, no model, no external
   service.**
2. **Statistical** (`backend/app/risk/statistical.py`, `duplicate.py`) —
   peer-cohort outlier detection (allocation and cost-per-beneficiary z-scores
   within a category) and near-duplicate description matching by TF-IDF cosine
   similarity within a district. Pure Python; no extra dependencies.
3. **Unsupervised machine learning** (`backend/app/risk/anomaly.py`) — an
   **isolation forest** (Liu, Ting & Zhou 2008) fitted on the live project
   population over an 11-dimensional feature vector. It needs no labels, which
   matters: a *supervised* model trained on a synthetic dataset would only learn
   the generator. It catches records where every individual figure sits inside
   its normal band but the *combination* occurs nowhere else in the cohort —
   exactly what a threshold rule cannot see. Each finding reports the anomaly
   score, its percentile against the population, and the three features that
   drove it, measured as robust z-scores against the cohort median. Implemented
   without external dependencies, so it is always available.
4. **External AI** (`backend/app/risk/ai_provider.py`) — **optional and off by
   default.** When an API key is configured, a model is asked to write a short
   reviewer briefing *over findings the deterministic layers have already
   computed*. It never sets the score, the level or the factors, and if the call
   fails the assessment is returned unchanged.

Every stored assessment records which layers actually contributed
(`analysis_sources`), so the interface never implies a model was involved when
only rules ran. `GET /api/admin/risk-engine` reports the live configuration.

Each detected indicator answers four questions explicitly, and the admin UI
renders them as four labelled blocks:

* **What is the risk?** — the explanation.
* **Why was it detected?** — the detected indicator.
* **What data caused it?** — the evidence, plus the metric, its value and the
  threshold it crossed.
* **What should be done?** — the recommended action, which is also seeded into
  the mitigation tracker with a responsible party and a due date.

Findings are framed throughout as **flagged for investigation**, never as
confirmed fraud (SRS FR10).

To upgrade the duplicate-detection layer to sentence-transformer embeddings,
`pip install sentence-transformers` and set `DUPLICATE_BACKEND=embeddings`. If the
package is absent the engine falls back to TF-IDF and reports which backend is
actually in use.

---

## Roles and what each may see

| Role | Citizen portal | Officials' portal | Risk score & factors | Notes / audit trail | Write actions |
|---|---|---|---|---|---|
| Citizen | yes | **no (403)** | **no** | **no** | file a citizen report |
| Field / District Officer | yes | yes | yes | yes | reviews, notes, mitigation, status, fund & progress entries |
| Auditor | yes | yes | yes | yes | the above, plus delete and bulk import |
| MPLAD Administrator | yes | yes | yes | yes | the above, plus provisioning official accounts |

Enforcement is server-side. `require_internal`, `require_reviewer`,
`require_elevated` and `require_admin` re-read the role **from the database** on
every request; the `role` claim inside the JWT is a UI hint and is never trusted
for authorisation.

---

## Verifying the build

```bash
# Backend: risk-engine, security and schema-contract tests.
# Standard library only — no database, no web server, no installed packages.
cd backend && python -m tests.run_all
#   or, with pytest installed:  pytest tests/

# Backend: parse every module, resolve every internal import, check that no
# admin route is missing a role guard, and that every response schema lines up
# with the ORM model it is validated from.
cd backend && python tools/static_check.py

# Whole repo: every API the frontend calls must exist on the backend.
python tools/check_api_contract.py

# Frontend: type-check and production build
cd frontend && npm run build
```

See `docs/VERIFICATION.md` for what each check covers and what it does not.

---

## Documentation

| Document | Contents |
|---|---|
| `docs/ARCHITECTURE.md` | Layered design, module map, request lifecycle |
| `docs/API.md` | Every endpoint, its role requirement and its shape |
| `docs/DATABASE.md` | Entities, relationships, migration path |
| `docs/SECURITY.md` | Auth, RBAC, field masking, secret handling |
| `docs/SRS_TRACEABILITY.md` | FR1–FR15 and the NFRs mapped to code |
| `docs/VERIFICATION.md` | What was tested and how to reproduce it |
| `docs/DO_THIS_NEXT.md` | Ordered steps from here to demo day |
| `docs/DEPLOY_GUIDE_SIH.md` | Deployment walk-through written against the SIH timeline |
| `docs/TEST_CHECKLIST.md` | The manual click-through the automated checks cannot do |
| `docs/DATA_INGESTION.md` | Where the data comes from and how real records get in |
| `docs/ASSUMPTIONS.md` | Engineering decisions taken where the SRS was open |
| `docs/DEPLOYMENT.md` | Putting it online: PostgreSQL, the API and the web app |
| `docs/JUDGE_READINESS.md` | Self-assessment, demo script and the gaps, stated plainly |
| `docs/VSCODE.md` | Running, debugging and testing the project in VS Code |
| `TROUBLESHOOTING.md` | Fixes for the errors people actually hit |

---

## A note on the data

Real government MPLAD data is not available for the hackathon (SRS §2.4), so the
repository ships a **realistic synthetic dataset** with deliberately injected
anomalies. Members of Parliament named in it are fictional. The footer of every
citizen page says so.
