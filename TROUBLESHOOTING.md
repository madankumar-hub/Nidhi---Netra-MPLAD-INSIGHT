# Troubleshooting

## Installation

### `error: Microsoft Visual C++ 14.0 or greater is required`
### `error: linker 'link.exe' not found`
### `Failed building wheel for pydantic-core / psycopg2-binary`

pip could not find a ready-built package for your Python version, so it tried to
compile one from source — which needs a C compiler you almost certainly do not
have installed.

**You do not need to install Visual Studio.** `requirements.txt` uses version
floors rather than exact pins precisely so pip can pick a build that matches your
Python, and the PostgreSQL driver has been moved out of the default install.
Make sure you are on the current version of this project, then:

```powershell
cd backend
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If you are stuck on an older copy, the quickest unblock is:

```powershell
.venv\Scripts\python.exe -m pip install "fastapi>=0.115.6" "uvicorn[standard]>=0.34.0" "SQLAlchemy>=2.0.36" "pydantic>=2.12" "pydantic-settings>=2.7" "bcrypt>=4.0.1" "PyJWT>=2.10" "python-multipart>=0.0.20" "email-validator>=2.2.0" "python-dateutil>=2.9.0" "httpx>=0.28.1"
```

### `'uvicorn' is not recognized as the name of a cmdlet`

The virtual environment's `Scripts` folder is not on your PATH, even though the
prompt shows `(.venv)`. Call it through Python instead, which always works:

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### `'python' is not recognized` / the Microsoft Store opens

Python was installed without the PATH option. Re-run the installer, choose
**Modify**, and tick **Add python.exe to PATH**. Then close and reopen every
terminal.

### `running scripts is disabled on this system`

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Answer `Y`. This affects your user account only, not the machine.

### `cd backend` says the path does not exist

Windows' "Extract All" nests the folder inside another of the same name. Look for
`MPLAD-Insight-SIH-2026\MPLAD-Insight-SIH-2026\backend`. The inner folder is the
project; open **that** one in your editor.

---

## Running

### The setup script printed errors but still said "Setup complete"

That was a defect in an earlier version of the script: PowerShell does not treat
a failing external command as an error, so a failed `pip install` did not stop
it. The current script checks the exit code after every step and stops at the
first failure. Re-run `scripts\setup.ps1`.

### `Address already in use` / `error while attempting to bind on address`

Something is already on that port — usually a previous run you did not close.

```powershell
# find it
netstat -ano | findstr :8000
# stop it (use the number from the last column)
taskkill /PID <number> /F
```

Or start on a different port with `--port 8001`, and set
`VITE_DEV_API_TARGET=http://localhost:8001` in `frontend\.env`.

### The website loads but every panel shows "Could not reach the server"

The API is not running, or it is on a different port. Check
<http://localhost:8000/api/health> in your browser — it should return
`{"status":"ok","database":"connected", ...}`. If it does not, look at the
terminal running uvicorn.

### The website is empty — no projects at all

The database was never seeded. From `backend`:

```powershell
.venv\Scripts\python.exe -m seed.seed_data --reset --projects 600
```

### I cannot sign in

Passwords are generated during seeding, not hardcoded. They are in
`backend\.seed-credentials.txt`. If that file is missing, re-run the seed command
above — it will generate and print a fresh set.

### 403 on every admin page

You are signed in as the **citizen** account. That is the system working
correctly: the Citizen role is refused internal data by the API. Sign in with the
**auditor** or **admin** account from `.seed-credentials.txt`.

---

## Database

### Switching to PostgreSQL

Install the optional driver, create the database, then point the app at it:

```powershell
cd backend
.venv\Scripts\python.exe -m pip install -r requirements-postgres.txt
```

In pgAdmin: right-click **Databases** → **Create** → **Database** →
name it `mplad_insight` → Save.

In `backend\.env`, comment out the SQLite line and add:

```ini
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/mplad_insight
```

Then re-seed:

```powershell
.venv\Scripts\python.exe -m seed.seed_data --reset --projects 600
```

Note the driver name is `psycopg` (version 3), not `psycopg2`.

### `password authentication failed for user "postgres"`

The password in `DATABASE_URL` does not match the one you set when installing
PostgreSQL. If the password contains `@`, `:`, `/` or `#`, percent-encode it —
`p@ss` becomes `p%40ss`.

### Starting over completely

```powershell
cd backend
del mplad_insight.db
.venv\Scripts\python.exe -m seed.seed_data --reset --projects 600
```

---

## Still stuck?

Run the built-in checks — they diagnose most problems without a server:

```powershell
cd backend
.venv\Scripts\python.exe -m tests.run_all       # 32 tests
.venv\Scripts\python.exe tools\static_check.py  # imports, routes, guards
```
