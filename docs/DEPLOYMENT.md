# Deploying MPLAD Insight

The target shape is three pieces: a managed **PostgreSQL** database, the
**FastAPI** service, and the **React** app served as static files.

```
   Browser
      │
      ├─────────────►  mplad-web    (static site: HTML/CSS/JS)
      │
      └─────────────►  mplad-api    (FastAPI, uvicorn)
                            │
                            └──────►  mplad-db  (PostgreSQL)
```

The instructions below use **Render**, because its blueprint file lets you
create all three from one commit and it does not ask for a card to start. The
same build and start commands work on Railway, Fly.io or any VPS — see
*Other platforms* at the end.

> Free tiers change. Check the current limits on your platform's pricing page
> before the demo, and be aware that free web services usually **sleep when
> idle** — the first request after a quiet period can take 30–60 seconds. Open
> the site a couple of minutes before you present.

---

## Before you start

You need:

* a **GitHub** account — the platform deploys from a repository;
* a **Render** account (sign in with GitHub);
* Git installed locally (`git --version`).

---

## Step 1 — Put the project on GitHub

From the project folder:

```bash
git init
git add .
git commit -m "MPLAD Insight - SIH 2026 prototype"
```

Create an empty repository on GitHub (**no** README, **no** .gitignore — the
project has its own), then:

```bash
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/mplad-insight.git
git push -u origin main
```

**Check before pushing** that `git status` does not list `.env`,
`.seed-credentials.txt` or any `.db` file. The project's `.gitignore` excludes
all three, but it is worth one look — a JWT signing key in a public repository
is the one mistake that is hard to undo.

---

## Step 2 — Create the services

1. On Render: **New** → **Blueprint**
2. Choose your repository
3. Render reads `render.yaml` and shows three resources: `mplad-db`,
   `mplad-api`, `mplad-web`
4. It will ask for the values marked `sync: false`. Fill in:

| Variable | Value |
|---|---|
| `SEED_ADMIN_PASSWORD` | a password you choose |
| `SEED_AUDITOR_PASSWORD` | a password you choose |
| `SEED_OFFICER_PASSWORD` | a password you choose |
| `SEED_CITIZEN_PASSWORD` | a password you choose |
| `CORS_ORIGINS` | leave blank for now |
| `VITE_API_BASE_URL` | leave blank for now |

Setting the four seed passwords yourself matters: leave them blank and the
seeder generates random ones into a file on a container you cannot open.

5. Click **Apply**. The first build takes 5–10 minutes.

---

## Step 3 — Join the two services up

Once both are live you have two URLs, something like:

* API: `https://mplad-api.onrender.com`
* Web: `https://mplad-web.onrender.com`

They now need to know about each other.

**On `mplad-api`** → Environment → set:

```
CORS_ORIGINS = https://mplad-web.onrender.com
```

**On `mplad-web`** → Environment → set:

```
VITE_API_BASE_URL = https://mplad-api.onrender.com/api
```

Note the `/api` on the end of that one, and **no** trailing slash on either.

Redeploy both (**Manual Deploy** → **Deploy latest commit**). The web app reads
its variable at build time, so it genuinely needs the rebuild.

---

## Step 4 — Check it

Open `https://mplad-api.onrender.com/api/health`. You want:

```json
{"status": "ok", "database": "connected", "environment": "production"}
```

Then open the web URL. The homepage should show real figures — total works,
allocation, utilisation. If the numbers are all zero, the seed has not run yet;
see *The site is empty* below.

Sign in with `auditor@mplad.gov.in` and the password you set in step 2.

---

## Step 5 — Before you present

**Turn the seeder off.** Once the database is populated, set
`SEED_ON_STARTUP = false` on `mplad-api` so a restart cannot surprise you.

**Warm the service up.** Free instances sleep. Open both URLs a few minutes
beforehand.

**Have a fallback.** Judges' venue Wi-Fi is not reliable. Keep the project
running locally on your laptop as well, and have a short screen recording of the
main flow on your phone.

**Know your two URLs by heart**, or put them behind a QR code on your poster —
judges who can open the live site on their own phone remember the project.

---

## Troubleshooting

### The site loads but every panel says "Could not reach the server"

`VITE_API_BASE_URL` is wrong, or the API is asleep. Open the API health URL
directly. Remember the value needs `/api` on the end and no trailing slash, and
that the web app must be **rebuilt** after you change it.

### Browser console shows a CORS error

`CORS_ORIGINS` on the API does not exactly match the web app's origin. It must
be the scheme plus host with no path and no trailing slash:
`https://mplad-web.onrender.com`. Several origins are separated by commas.

### The site is empty — no projects

The seed did not run. Either set `SEED_ON_STARTUP=true` and restart the API, or
run it once from the platform's shell:

```bash
cd backend && python -m seed.seed_data --projects 400
```

### `sqlalchemy.exc.OperationalError: could not translate host name`

`DATABASE_URL` is not reaching the service. On Render it comes from the
blueprint's `fromDatabase` block — confirm the database finished provisioning
before the API built, then redeploy the API.

### Deploy fails building `psycopg`

Confirm the API's build command is `pip install -r requirements-postgres.txt`
(not `requirements.txt`) and that `PYTHON_VERSION` is set. The project uses
psycopg 3, which ships prebuilt wheels; psycopg2 is deliberately not used
because it needs a compiler.

### First request after a quiet period takes ~50 seconds

That is the free instance waking up, not a bug. Paid instances do not sleep.

---

## Other platforms

### Railway

Create a project from the repo, add a PostgreSQL plugin, then two services:

| | Root | Build | Start |
|---|---|---|---|
| API | `backend` | `pip install -r requirements-postgres.txt` | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Web | `frontend` | `npm ci && npm run build` | serve `dist/` |

Railway injects `DATABASE_URL` automatically; the app normalises the
`postgres://` prefix it uses.

### Docker / VPS

Everything is already in `docker-compose.yml`:

```bash
export POSTGRES_PASSWORD='choose-something-strong'
cp backend/.env.example backend/.env     # set JWT_SECRET_KEY
docker compose up --build -d
docker compose exec api python -m seed.seed_data --reset
```

Web app on port 8080, API on 8000. Put nginx or Caddy in front for TLS.

### Split hosting (Vercel/Netlify + a Python host)

The frontend is a plain static bundle, so any static host works. Set
`VITE_API_BASE_URL` at build time and keep the SPA rewrite —
`frontend/public/_redirects` already carries it for Netlify and Cloudflare
Pages; on Vercel add a rewrite of `/(.*)` to `/index.html`.

---

## Production hardening

What this prototype does **not** do, and would need before real use:

| Gap | What to add |
|---|---|
| Token revocation | A server-side refresh-token store, so sign-out is real |
| Rate limiting | At the gateway, or `slowapi` in front of `/api/auth` |
| Real OTP delivery | `OTP_DELIVERY=email` wired to a provider |
| Schema migrations | Alembic, instead of `create_all` — see `docs/DATABASE.md` |
| Backups | The managed database's snapshot schedule |
| Observability | Structured logs to a collector; the API already emits `X-Response-Time-ms` |
| Secrets management | A vault rather than dashboard environment variables |

These are listed in `docs/SECURITY.md` too. Saying them out loud to a judge is
better than being asked.
