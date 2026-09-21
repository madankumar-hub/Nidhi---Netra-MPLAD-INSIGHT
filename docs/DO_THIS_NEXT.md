# Do this next — your steps, in order

Everything from here is on your machine, not mine. Follow this top to bottom.
Do not skip to Stage 3.

---

# Stage 1 — Apply the latest files (5 minutes)

## 1.1 Apply the docs update

From `mplad-docs-update.zip`, replace:

- the whole `docs\` folder
- `README.md`

Nothing else. **No code changed**, so nothing needs restarting for this one.

## 1.2 Confirm the map removal is applied

If you have not already replaced `frontend\src` and `frontend\package.json` from
the previous ZIP, do that now. Then, in the frontend terminal:

```powershell
Ctrl+C
npm install
npm run dev
```

`npm install` is what removes the Leaflet package. Skip it and you get a stale
`node_modules`.

---

# Stage 2 — Get it running (10 minutes)

## 2.1 Start the API

Double-click **`START-API.bat`** in the project folder.

Or, in PowerShell:

```powershell
cd C:\path\to\mplad-insight\backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

**Leave this window open.** You should see `Application startup complete`.

> Never set up before? Run **`SETUP.bat`** once instead. It creates the virtual
> environment, installs everything, generates a JWT secret, seeds 600 works and
> runs the tests. It takes 5–10 minutes.

## 2.2 Start the web app

Open a **second** window. Double-click **`START-WEB.bat`**.

Or:

```powershell
cd C:\path\to\mplad-insight\frontend
npm run dev
```

**Leave this window open too.**

## 2.3 Check both are alive

| Open this | Expect |
|---|---|
| http://localhost:8000/api/health | `{"status":"ok","database":"connected"}` |
| http://localhost:5173 | The home page, with real numbers — not zeroes |

## 2.4 Get your sign-in details

Open this file in Notepad:

```
backend\.seed-credentials.txt
```

Four accounts: citizen, officer, auditor, admin. You need **admin** and
**auditor** for testing.

> If the file is missing, re-seed:
> ```powershell
> cd backend
> .venv\Scripts\python.exe -m seed.seed_data --reset --projects 600
> ```

---

# Stage 3 — Test it (60–90 minutes, split it with your team)

Open **`docs\TEST_CHECKLIST.md`**. Work through it in this order and write in
the OK column as you go. A blank row means untested, not working.

| Order | Section | What it is | Who |
|---|---|---|---|
| 1 | **C** | The 403 check — 3 console commands | You. Do this first |
| 2 | **A** | Citizen pages, signed out | Teammate 1 |
| 3 | **A14** | Every citizen page again in हिन्दी | Teammate 2 |
| 4 | **B** | Signup, login, access request | Teammate 3 |
| 5 | **D** | Officials portal, all 23 rows | You |
| 6 | **E** | Projector resolution, keyboard, zoom | Anyone |

## Watch these five especially

They are the ones most likely to be broken:

1. **C1** — a citizen calling `/api/admin/projects` must get **403**.
   If it returns 200, stop everything and tell me.
2. **B6 / B8** — after an admin rejects your access request, the citizen's
   `/request-access` page must say **rejected with the note**, not "no records
   found". This was broken before.
3. **D7** — the PDF export must **open**, with columns that line up.
4. **D10–D12** — add a note, change a status, add a mitigation. Then **reload
   the page.** If it disappeared, it never saved.
5. **A14** — any English word on screen while in Hindi mode. Write down the page
   and the word.

## When something breaks

Look at the **backend terminal**, not the browser. The red traceback there is
the real error; the browser only shows what leaked out.

Send me: the page, what you clicked, and the last 20 lines of that terminal.

---

# Stage 4 — Fix round (me)

Send me your findings from Stage 3. I fix, you replace the folders I name, you
re-test only the rows that failed.

**Do not go to Stage 5 with open findings.**

---

# Stage 5 — Deploy (with your team, 45 minutes)

You said you want your teammates to agree first. When they do:

## 5.1 Clean up first

```powershell
del backend\.seed-credentials.txt
```

Then check nothing sensitive is staged:

```powershell
cd C:\path\to\mplad-insight
git status
```

`.env`, `.seed-credentials.txt` and any `.db` file must **not** appear.
The `.gitignore` already excludes all three, but look once anyway — a JWT
signing key in a public repo is hard to undo.

## 5.2 Push to GitHub

```powershell
git init
git add .
git commit -m "MPLAD Insight - SIH 2026 prototype"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/mplad-insight.git
git push -u origin main
```

## 5.3 Deploy on Render

1. **New** → **Blueprint** → pick your repository
2. It reads `render.yaml` and offers three services: `mplad-db`, `mplad-api`,
   `mplad-web`
3. Set the four seed passwords **yourself** — leave them blank and the seeder
   generates random ones into a container you cannot open
4. Leave `CORS_ORIGINS` and `VITE_API_BASE_URL` blank for now
5. **Apply.** First build takes 5–10 minutes

## 5.4 Join the two services

Once both are live, you have two URLs. On `mplad-api` → Environment:

```
CORS_ORIGINS = https://mplad-web.onrender.com
```

On `mplad-web` → Environment:

```
VITE_API_BASE_URL = https://mplad-api.onrender.com/api
```

Note the `/api` on that one. **No trailing slash on either.** Then redeploy both
— the web app reads its variable at build time, so it genuinely needs rebuilding.

Full detail and troubleshooting: `docs\DEPLOYMENT.md`.

## 5.5 Before the demo day

- Set `SEED_ON_STARTUP = false` so a restart cannot surprise you
- Free instances **sleep**. Open both URLs a few minutes before you present
- Put the web URL behind a **QR code** on your poster

---

# Stage 6 — Rehearse (2 hours, all of you)

Open **`docs\DEMO_SCRIPT.md`**. Ten minutes, six sections.

1. **Run it once each, out loud, with a timer.** Reading it silently does not
   count
2. Decide **who drives** and **who talks**. Not the same person
3. Each of you picks one question from the "Questions you should expect" section
   and answers it **without reading**
4. Whoever presents the risk engine must be able to explain it at a whiteboard —
   read `docs\ARCHITECTURE.md` and `backend\app\risk\anomaly.py`

## Have ready on the day

- Your admin password, written down
- One work ID the engine flagged **CRITICAL**
- The project running **locally on a laptop** as a fallback — venue Wi-Fi fails
- A short screen recording of the main flow on someone's phone

## Say this before a judge finds it

> "Our SRS said XGBoost. We shipped an unsupervised isolation forest instead,
> deliberately — XGBoost is supervised and there is no labelled corpus of
> confirmed MPLAD fraud in India. Training one would mean fitting to our own
> assumptions and calling the result evidence. We also claim no accuracy figure,
> because without labels there is nothing to measure against."

Volunteered, that reads as judgment. Discovered, it reads as a discrepancy.

---

# Summary

| Stage | What | How long | Who |
|---|---|---|---|
| 1 | Apply the files | 5 min | You |
| 2 | Get it running | 10 min | You |
| 3 | Test it | 60–90 min | Whole team |
| 4 | Fix round | — | Me |
| 5 | Deploy | 45 min | You + team |
| 6 | Rehearse | 2 hours | Whole team |

**Stage 3 is the one that matters.** Both bugs that reached you were runtime
wiring that no test or type checker can catch. Someone has to click.
