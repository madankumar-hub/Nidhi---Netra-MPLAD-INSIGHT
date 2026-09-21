# Click-through checklist

Every page, in both portals, with the server actually running. Print this or
split it between teammates.

`verify.sh` proves the code is internally consistent. It cannot start the server
and click a button — and **both bugs that reached you were exactly that kind**:
a dependency FastAPI could not resolve, and a duplicate keyword argument. Neither
was visible to a test or a type checker. This list is the part only a human can
do.

Mark each row **OK** or write what went wrong. A blank row means untested, which
is not the same as working.

---

## Before you start

```powershell
# terminal 1
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload

# terminal 2
cd frontend
npm run dev
```

Sign-in details are in `backend\.seed-credentials.txt`.
**Delete that file before you share the project or deploy it.**

Keep the backend terminal visible. A red traceback there is the real error; the
browser only shows you what leaked out.

---

## A. Citizen side — signed out

Open a **private/incognito window** so no token is present.

| # | Page | Check | OK? |
|---|------|-------|-----|
| A1 | `/` | Home loads, totals show real numbers, nothing says NaN or 0 | |
| A2 | `/` | Search a district you know → results appear | |
| A3 | `/projects` | Filters work: district, category, status, year | |
| A4 | `/projects` | Result count changes when a filter changes | |
| A5 | `/projects` | Pagination — go to page 2, then back | |
| A6 | `/scheme/:id` | Open a work. Allocated / spent / remaining all render | |
| A7 | `/scheme/:id` | Expenditure timeline chart draws | |
| A8 | `/scheme/:id` | Site photograph and sanction document show | |
| A9 | `/scheme/:id` | Status badge says **Normal** or **Under review** — **never** a risk score, never a percentage | |
| A10 | `/scheme/:id` | Submit a citizen report. It accepts and confirms | |
| A11 | `/statistics` | Every chart renders; no empty panel | |
| A12 | `/about` | Loads, no placeholder text left in it | |
| A13 | `/nonsense-url` | 404 page, not a blank screen | |

### A14 — Hindi, on every page above

Switch to **हिन्दी** and walk A1–A12 again. This is the one most likely to
embarrass you live. Look specifically at:

- status badges and risk categories (the enum translation)
- table headers and column labels
- chart axis and legend labels
- empty states and error messages
- date and currency formats

**Any English word still on screen in Hindi mode is a finding.** Write down the
page and the word.

---

## B. Accounts and access

| # | Step | Check | OK? |
|---|------|-------|-----|
| B1 | `/signup` | Let Chrome autofill the form. Name and email land in the right boxes | |
| B2 | `/signup` | Complete a signup with the OTP | |
| B3 | `/login` | Sign in as that new citizen | |
| B4 | `/login` | Wrong password → a readable message, not a raw validation dump | |
| B5 | `/request-access` | Submit a request as the citizen | |
| B6 | `/request-access` | The page now shows **your own request and its status** | |
| B7 | — | Sign in as admin, **reject** it with a note | |
| B8 | `/request-access` | Back as the citizen: it says **rejected**, with the note. Not "no records found" | |
| B9 | — | Repeat B5–B7 but **approve**. Sign out, sign back in, the citizen is now an official | |

B6 and B8 are the ones that were broken before. Check them properly.

---

## C. The separation — do this one yourself

Signed in as a **citizen**, open devtools console and run:

```js
await fetch('/api/admin/projects', {
  headers: { Authorization: `Bearer ${localStorage.getItem('mplad.access_token')}` }
}).then(r => r.status)
```

| # | Check | OK? |
|---|-------|-----|
| C1 | Returns **403** | |
| C2 | Same for `/api/admin/projects/flagged`, `/api/admin/activity`, `/api/admin/dashboard` and `/api/admin/users` | |
| C3 | The citizen detail response has no `risk_score`, `risk_level`, `factors` or `notes` | |

**Use the exact paths above.** A path that does not exist — `/api/admin/flagged`,
say — returns **404** before it ever reaches the role guard. That is correct
behaviour, but it proves nothing, and improvising a URL in front of a judge makes
a working endpoint look broken.

For C3, open any work on the citizen side and take the number from the URL
(`localhost:5173/scheme/347` → `347`), then:

```js
await fetch('/api/projects/347').then(r => r.json()).then(d =>
  ['risk_score','risk_level','factors','notes','reviews','mitigations','review_status'].filter(k => k in d)
)
```

It must print `[]`. Anything inside the brackets is a leak.

If any of these returns 200, stop and tell me. Nothing else matters more.

---

## D. Officials portal — sign in as auditor or admin

| # | Page | Check | OK? |
|---|------|-------|-----|
| D1 | `/admin` | Dashboard loads; every tile has a number | |
| D2 | `/admin` | Every chart draws | |
| D3 | `/admin/projects` | List loads, filters work, pagination works | |
| D4 | `/admin/projects` | **New work** — create one. It saves and appears in the list | |
| D5 | `/admin/projects` | **Bulk import** — upload `samples\mplad-works-sample.csv`. Row count and errors shown before anything is sent | |
| D6 | `/admin/projects` | Export **CSV**. Opens in Excel, headers intact | |
| D7 | `/admin/projects` | Export **PDF**. **Opens without an error**, columns line up, nothing runs into the next column | |
| D8 | `/admin/scheme/:id` | Open a work. Risk panel shows category, level, reason, the metric and its threshold | |
| D9 | `/admin/scheme/:id` | Layer badges show which of the three layers fired | |
| D10 | `/admin/scheme/:id` | Add a review note → **reload the page** → it is still there | |
| D11 | `/admin/scheme/:id` | Change review status → reload → it held | |
| D12 | `/admin/scheme/:id` | Add a mitigation action → reload → it held | |
| D13 | `/admin/flagged` | Loads; sorting by risk works | |
| D14 | `/admin/delayed` | Loads | |
| D15 | `/admin/reviews` | Review queue loads and a decision can be recorded | |
| D16 | `/admin/citizen-reports` | The report you filed in A10 is here | |
| D17 | `/admin/analytics` | Every chart renders | |
| D18 | `/admin/activity` | Your actions from D10–D12 appear, with your name and a timestamp | |

### Admin-only

| # | Page | Check | OK? |
|---|------|-------|-----|
| D19 | `/admin/access-requests` | Pending requests listed; approve and reject both work with a note | |
| D20 | `/admin/users` | Accounts list loads; role filter works | |
| D21 | `/admin/users` | Revoke an officer → they become Citizen, account still exists | |
| D22 | `/admin/users` | An **admin** row and **your own** row offer no revoke button | |

### D23 — Auditor, not admin

Sign in as the **auditor**. `/admin/access-requests` and `/admin/users` must not
be reachable — not in the nav, and not by typing the URL.

---

## E. Presentation

| # | Check | OK? |
|---|-------|-----|
| E1 | Full walk-through on a **projector resolution** (1280×720). Nothing cut off | |
| E2 | Tab through the home page — focus ring always visible | |
| E3 | Skip link works | |
| E4 | Text-size and high-contrast controls work | |
| E5 | Browser zoom at 150% — layout holds | |
| E6 | Every page footer says the data is synthetic | |
| E7 | `./verify.sh` — or **`VERIFY.bat`** on Windows — green on the machine you will demo from | |

---

## F. Before you hand it over

| # | Check | OK? |
|---|-------|-----|
| F1 | `backend\.seed-credentials.txt` **deleted** | |
| F2 | No `.env` file in the ZIP or the repo — only `.env.example` | |
| F3 | No `.db` file in the ZIP or the repo | |
| F4 | `node_modules`, `.venv`, `dist` excluded | |

---

## Findings

Write them here as you go. Page, what you did, what happened.

| Page | Did | Expected | Got |
|------|-----|----------|-----|
| | | | |
| | | | |
| | | | |
