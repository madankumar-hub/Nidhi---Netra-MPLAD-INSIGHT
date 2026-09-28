MPLAD Insight
Smart India Hackathon 2026 — SIH26102
MPLAD Insight is a web application for monitoring and analysing development works carried out under the Members of Parliament Local Area Development Scheme (MPLADS).
The main idea is simple: information about a project should not stop at its sanction. The system should make it possible to follow the project from sanction and allocation to expenditure, physical progress, review, and completion.
At the same time, officials need a different view of the same information. They need to know which projects are delayed, which ones need review, where spending and physical progress do not match, and which records may need further investigation.
MPLAD Insight therefore has two separate interfaces:
- Citizen Portal — for viewing project information, expenditure, progress and submitting issues.
- Officials/Admin Portal — for project monitoring, risk analysis, reviews, notes, mitigation actions and administrative workflows.
The information shown to citizens and officials is intentionally different. Internal risk analysis and administrative information is not exposed through the citizen APIs.
What problem are we trying to solve?
Monitoring a large number of development works manually can make it difficult to identify projects that need attention.
For example, a project may have:
- very little physical progress even though considerable money has been spent,
- an approaching completion date with significant work still pending,
- expenditure higher than expected,
- no expenditure after the project has started,
- unusually high or low spending compared with similar projects,
- incomplete or inconsistent project information,
- repeated citizen complaints,
- or a combination of several unusual indicators.
Looking at every project individually is time-consuming.
MPLAD Insight uses a combination of rule-based checks, statistical analysis and an unsupervised anomaly-detection model to bring such projects to the attention of officials.
The system does not claim that a flagged project is fraudulent. A flag means that the project deserves further review.
Main Features
1. Citizen project portal
Citizens can browse and search development works without accessing internal administrative information.
The citizen side includes:
- project search
- project details
- sanctioned amount
- expenditure
- remaining amount
- physical progress
- project status
- timeline information
- location information
- project documents
- site photographs
- citizen issue/report submission
The citizen view is intentionally kept simpler than the officials' dashboard.
2. Officials/Admin dashboard
Officials get access to information required for monitoring and review.
The administrative side includes:
- project listing and filtering
- progress monitoring
- expenditure monitoring
- delayed-project identification
- projects awaiting review
- risk analysis
- risk indicators and explanations
- mitigation actions
- review records
- internal notes
- citizen reports
- activity/audit history
- project status updates
- financial and progress updates
- CSV/PDF export
- administrative access management
The goal is not just to display charts. An official should be able to go from:
Project → Risk → Evidence → Review → Action → Follow-up
without moving to a separate system.
Risk Analysis
The risk engine is one of the main parts of the project.
We intentionally use more than one method because a single threshold is not enough to understand every unusual project.
Rule-based checks
The system checks project information for conditions such as:
- schedule delay
- approaching deadline with incomplete work
- overdue projects
- expenditure progressing faster than physical progress
- unusually low expenditure near the end of a project
- cost overrun
- stalled progress updates
- zero expenditure after commencement
- inconsistent completion information
- incomplete records
- concentration of citizen reports
These checks are deterministic, so the same project data produces the same result.
The rule implementation is in:
backend/app/risk/rules.py

Statistical checks
The system also compares a project with similar projects.
Examples include:
- allocation outliers
- cost-per-beneficiary outliers
- similar/duplicate project descriptions
The relevant code is under:
backend/app/risk/statistical.py
backend/app/risk/duplicate.py

Anomaly detection
MPLAD Insight also includes an unsupervised Isolation Forest based anomaly detector.
The model works on multiple project features instead of checking each number independently.
This is useful for cases where individual values may not look unusual, but their combination is unusual compared with the rest of the project population.
The implementation is in:
backend/app/risk/anomaly.py

The model does not require labelled fraud data.
This is important for our current prototype because we are working with a realistic synthetic dataset rather than a complete labelled dataset of real MPLADS fraud cases.
Optional external AI
An external AI provider can optionally generate a short explanation for an already-detected finding.
It does not decide the risk score.
The deterministic and statistical layers calculate the actual indicators. The optional AI layer is only used to help turn those findings into a reviewer-friendly summary.
The external AI integration is disabled unless an API key is configured.
backend/app/risk/ai_provider.py

What an official sees for a risk
We tried to keep the risk explanation understandable instead of displaying only a number.
For each finding, the system can explain:
What is the risk?
A short description of the issue.
Why was it detected?
The condition or indicator that triggered the finding.
What data caused it?
The relevant project value, metric and comparison/threshold.
What should be done?
A suggested next step that can be converted into a mitigation action.
This makes the risk result something an official can actually review rather than just another dashboard score.
Risk does not mean fraud
A project being flagged does not mean that fraud has been established.
The system is intended to help officials decide where to look more closely.
For example:
High expenditure with low physical progress

may be a reason to review a project, but it could also have a legitimate explanation depending on the nature and stage of the work.
The final decision remains with the responsible official.
Citizen and Official Access
The application has separate access levels.
Role	Citizen Portal	Official Portal	Risk Information	Internal Notes
Citizen	Yes	No	No	No
District/Field Officer	Yes	Yes	Yes	Yes
Auditor	Yes	Yes	Yes	Yes
MPLAD Administrator	Yes	Yes	Yes	Yes


A citizen can submit an issue/report, but cannot access internal risk analysis or administrative notes.
This separation is implemented on the backend as well as in the frontend.
We do not depend only on hiding a page or button.
The backend checks the authenticated user's role before allowing access to internal APIs.
Technology Stack
Backend
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- PostgreSQL
- SQLite for simple local development
- PyJWT
- bcrypt
Frontend
- React
- TypeScript
- Vite
- Tailwind CSS
- React Router
- Recharts
- Leaflet
- Lucide React
Analysis
- Python-based rule engine
- Statistical outlier detection
- TF-IDF similarity for duplicate detection
- Isolation Forest anomaly detection
- Optional external AI provider
Project Structure
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
│   │
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
│   │   ├── features/
│   │   │   ├── admin/
│   │   │   ├── auth/
│   │   │   ├── citizen/
│   │   │   └── map/
│   │   └── ...
│   ├── .env.example
│   └── package.json
│
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── DATABASE.md
│   ├── DEPLOYMENT.md
│   ├── SECURITY.md
│   ├── DATA_INGESTION.md
│   └── ...
│
├── docker-compose.yml
├── Procfile
├── README.md
└── .gitignore

Running the Project Locally
Requirements
You will need:
- Python 3.11+
- Node.js
- npm
PostgreSQL is optional for local development because the application can run with SQLite.
1. Start the backend
cd backend

Create a virtual environment:
Windows
python -m venv .venv
.venv\Scripts\activate

Linux/macOS
python3 -m venv .venv
source .venv/bin/activate

Install dependencies:
pip install -r requirements.txt

Create the environment file:
cp .env.example .env

On Windows, you can copy the file manually if cp is unavailable.
Generate a JWT secret:
python -c "import secrets; print(secrets.token_urlsafe(48))"

Put the generated value in:
JWT_SECRET_KEY=your-generated-secret

Seed the development database:
python -m seed.seed_data --reset --projects 600

Start the API:
uvicorn app.main:app --reload --port 8000

Backend:
http://localhost:8000

API documentation:
http://localhost:8000/docs

2. Start the frontend
Open another terminal:
cd frontend
npm install

Create the frontend environment file if required:
cp .env.example .env

Start Vite:
npm run dev

The frontend will normally be available at:
http://localhost:5173

During development, Vite proxies /api requests to the backend.
Demo Accounts
The seed script creates accounts for the different roles.
Passwords should not be stored in the repository.
If the following variables are empty:
SEED_ADMIN_PASSWORD=
SEED_AUDITOR_PASSWORD=
SEED_OFFICER_PASSWORD=
SEED_CITIZEN_PASSWORD=

the seed script generates random passwords and writes them to:
backend/.seed-credentials.txt

This file is intentionally ignored by Git.
For a local demo, use the generated credentials.
Do not commit .env or .seed-credentials.txt.
Docker
The project also includes a Docker Compose setup.
Create the environment file:
cp backend/.env.example backend/.env

Set the required values and start the services:
docker compose up --build

The default services are:
Web: http://localhost:8080
API: http://localhost:8000
API Docs: http://localhost:8000/docs

The Compose setup uses PostgreSQL.
Database
PostgreSQL is the intended database for deployment.
For local development, SQLite can be used without installing PostgreSQL.
SQLite:
DATABASE_URL=sqlite:///./mplad_insight.db

PostgreSQL:
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE

The actual database password should always be supplied through environment variables and should never be committed to Git.
API
The backend is built using FastAPI.
Some of the main API areas are:
/api/auth/...
/api/public/...
/api/admin/projects/...
/api/admin/risk/...
/api/admin/analytics/...
/api/admin/workflow/...
/api/admin/access/...

The complete API documentation is available in:
docs/API.md

When the backend is running, FastAPI's interactive documentation can also be opened at:
http://localhost:8000/docs

Security
Security was considered as part of the application design rather than only at deployment.
Some of the measures currently implemented include:
- JWT-based authentication
- password hashing with bcrypt
- role-based access control
- server-side authorization checks
- rate limiting
- separate citizen and internal API routes
- environment-based secrets
- no committed .env files
- no committed database credentials
- audit/activity records for important actions
- protected administrative operations
The backend does not trust a role value supplied only by the frontend.
For internal operations, the user's role is checked against the database before the request is allowed.
More information is available in:
docs/SECURITY.md

Testing and Verification
The repository contains tests for several important parts of the system.
Examples include:
- authentication and access control
- security
- rate limiting
- risk engine
- anomaly detection
- geography
- project schemas
- PDF export
- API contracts
- accessibility
- sample data
- deployment safety
Run the backend test suite with:
cd backend
python -m tests.run_all

If pytest is installed:
pytest tests/

There is also a static check:
python tools/static_check.py

For the frontend:
cd frontend
npm run typecheck
npm run build

Sample Data
The project currently uses a realistic synthetic dataset for development and demonstration.
This lets us test:
- project monitoring
- expenditure tracking
- progress calculations
- delayed projects
- risk detection
- anomaly detection
- citizen reports
- reviews
- mitigation workflows
The dataset is intended for demonstration and development, not as an official MPLADS database.
When connected to a real government data source, the ingestion and field-mapping layer would need to be adapted to the official data format.
Current Limitations
This is a working prototype, so there are areas that can still be improved.
Some of the planned improvements are:
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
These are not hidden from the implementation. The current repository contains documentation describing the architecture, assumptions and deployment considerations.
Why the system uses multiple analysis methods
There is no single method that can reliably identify every unusual project.
A rule can catch something obvious, such as a project being overdue.
Statistical comparison can identify a project that is very different from similar projects.
Anomaly detection can identify combinations of values that are unusual even when no single value crosses a fixed threshold.
The optional AI layer can help summarize the findings for a human reviewer.
This gives the system a combination of:
Rules
  ↓
Statistical checks
  ↓
Anomaly detection
  ↓
Human review
  ↓
Mitigation / follow-up

The final decision is made by the responsible official, not by the model.
Documentation
More detailed documentation is available in the docs/ directory.
Document	Description
ARCHITECTURE.md	Application architecture
API.md	API endpoints and contracts
DATABASE.md	Database structure
SECURITY.md	Security design
DEPLOYMENT.md	Deployment instructions
DATA_INGESTION.md	Data import approach
MAP_MODULE.md	Geographic/map functionality
VERIFICATION.md	Testing and verification
TEST_CHECKLIST.md	Test checklist
ASSUMPTIONS.md	Current project assumptions
DEMO_SCRIPT.md	Demonstration flow


Team
MPLAD Insight — SIH 2026
This project was developed as part of Smart India Hackathon 2026, problem statement SIH26102.
The repository contains the implementation, supporting documentation, tests and deployment configuration used for the prototype.
A note about the project
MPLAD Insight is a prototype built to demonstrate how project monitoring, citizen transparency and risk-based review can be brought into one system.
The intention is not to replace the judgement of government officials. The system is meant to reduce the amount of manual checking required to find projects that deserve attention and to keep the subsequent review process traceable.
