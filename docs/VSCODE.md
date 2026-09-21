# Running MPLAD Insight in VS Code

The repository ships a `.vscode/` folder, so most of this is already wired up.

## 1. Prerequisites

| Tool | Version | Check with |
|---|---|---|
| Python | 3.11 or newer | `python --version` |
| Node.js | 18 or newer | `node --version` |
| VS Code | any recent build | — |

On Windows, install Python from **python.org** (tick *Add python.exe to PATH*).
The Microsoft Store shim often breaks virtual environments.

## 2. Open the project

**File → Open Folder…** and choose the `MPLAD-Insight-SIH-2026` folder itself —
not `backend` or `frontend`. The tasks and launch configurations are written
against that root.

VS Code will offer to install the recommended extensions. Accept; they are:

* **Python** + **Pylance** + **debugpy** — backend editing and debugging
* **Tailwind CSS IntelliSense** — class-name completion in the React files
* **REST Client** — run the API examples in `backend/api-examples.http`
* **Docker** — optional, for the compose stack

## 3. One-time setup

Press **Ctrl+Shift+P** → **Tasks: Run Task** → **`Setup: everything`**.

That runs three tasks in order:

1. creates `backend/.venv`, installs the Python dependencies, copies
   `.env.example` to `.env` and generates a real `JWT_SECRET_KEY` into it;
2. seeds the database with 600 works, their fund and progress trails, reviews,
   notes, citizen reports, risk assessments and mitigation actions;
3. runs `npm install` in `frontend/`.

Allow a few minutes — `npm install` is the slow part.

**Your sign-in details** land in `backend/.seed-credentials.txt`. The seed script
generates random passwords rather than shipping hardcoded ones, so open that file
and keep it to hand. It is git-ignored; delete it when you are done.

> If the Python task fails with *"running scripts is disabled on this system"*,
> open a terminal and run
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`, then
> re-run the task.

## 4. Select the interpreter

**Ctrl+Shift+P** → **Python: Select Interpreter** → choose the one inside
`./backend/.venv`. This makes imports resolve, enables the test explorer and
points the debugger at the right Python.

## 5. Run it

Open the **Run and Debug** panel (**Ctrl+Shift+D**) and pick
**`▶ Full stack (API + web)`**, then press **F5**.

That starts the API under the debugger, starts the Vite dev server, and opens a
browser attached to VS Code. Breakpoints work on both sides.

If you would rather not use the debugger: **Tasks: Run Task** →
**`Run: both servers`**.

| | |
|---|---|
| Web app | <http://localhost:5173> |
| API documentation | <http://localhost:8000/docs> |

Sign in as the **auditor** for the officials' portal — risk analysis, mitigation,
reviews, notes, audit trail. Sign in as the **citizen** to see the public side and
confirm that none of that is reachable from it.

## 6. Debugging

**Backend.** Set a breakpoint in, say, `backend/app/risk/rules.py` or
`backend/app/routers/admin_risk.py`, then open a work's Risk tab in the browser.
Execution stops with the whole call stack available. `justMyCode` is off, so you
can step into FastAPI, SQLAlchemy and Pydantic if you need to.

**Frontend.** With the *Web* configuration running, set a breakpoint in any
`.tsx` file — VS Code maps it through Vite's source maps.

Other launch configurations in the dropdown:

* **API: seed the database** — re-seed under the debugger
* **Tests: risk engine + schema contracts** — step through the 32 tests

## 7. The API examples file

Open `backend/api-examples.http`. Paste the passwords from
`.seed-credentials.txt` into the variables at the top, then click
**Send Request** above any block.

It is organised as a walk-through: the citizen endpoints, then sign-in, then a
block of requests that **should all return 403** — a citizen token reaching for
the dashboard, the risk analysis, the notes and the audit trail — then the same
paths succeeding with an auditor token. That block is the quickest way to
demonstrate the access-control boundary to a judge.

## 8. Tests and checks

**Test Explorer** (the flask icon) discovers the pytest suite under
`backend/tests` once the interpreter is selected.

Or **Tasks: Run Task** →

| Task | What it does |
|---|---|
| `Check: backend tests` | 16 risk-engine + 9 security + 7 schema-contract tests |
| `Check: backend static analysis` | imports, route/guard coverage, schema-to-ORM alignment |
| `Check: API contract (frontend vs backend)` | every frontend call resolves to a real route |
| `Check: frontend type-check` | `tsc --noEmit` |
| `Build: frontend production bundle` | `npm run build` |
| `Check: everything` | all of the above, in sequence |

## 9. Useful entry points when reading the code

| To understand… | Start at |
|---|---|
| How a risk score is produced | `backend/app/risk/engine.py`, then `rules.py` |
| What the admin sees on one work | `frontend/src/pages/admin/AdminSchemeDetailPage.tsx` |
| What a citizen sees on the same work | `frontend/src/pages/SchemeDetailPage.tsx` |
| Why a citizen cannot see internal data | `backend/app/core/deps.py` + `schemas/project.py` |
| How reviews and the audit trail are stored | `backend/app/services/review_service.py` |

## 10. Docker instead

With the Docker extension installed, right-click `docker-compose.yml` →
**Compose Up**. Set `POSTGRES_PASSWORD` in your environment first and create
`backend/.env` as above. Then seed:

```
docker compose exec api python -m seed.seed_data --reset
```

Web app on <http://localhost:8080>, API on <http://localhost:8000>.
