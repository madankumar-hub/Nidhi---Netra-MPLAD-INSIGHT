# Demo script

A ten-minute walkthrough for SIH judging, in the order that makes the argument
land. Read the "say this" lines as prompts, not a script to recite.

SIH judges score on six things: problem understanding, innovation, technical
feasibility, impact, user experience, and a live working demo. This route hits
all six without ever opening a slide.

---

## Before the judges arrive

1. `./verify.sh` (or `VERIFY.bat` on Windows) — confirms nothing is broken.
2. Start the API and the web app (see `README.md`).
3. Open two browser windows:
   - **Window A** — signed out, on the home page. This is the citizen.
   - **Window B** — signed in as an administrator, on the dashboard.
4. In Window A, search for a district **that is in the dataset** and leave the
   result on screen. The seeded districts are listed in
   `backend/seed/reference_data.py`; in Rajasthan they are **Jaipur, Jodhpur,
   Udaipur and Kota**. Sirohi is *not* seeded — searching it returns nothing.
   Check the district you plan to use returns results before the judges arrive.

**Have ready:** your admin password, and one work ID that the risk engine has
flagged CRITICAL.

---

## 1. Open with the problem, not the product (1 min)

Stay on the citizen home page, signed out.

> "MPLADS gives every MP ₹5 crore a year. The sanction lists are public, but
> they're published as scanned PDFs, per constituency, with no way to search
> across them and no way to see whether the money was actually spent. If you
> want to know what was sanctioned in your own district, you file an RTI and
> wait thirty days."

Then search your district.

> "This is Udaipur. Every sanctioned work, the money allocated against it, and
> what's actually been spent."

Use whichever seeded district you know best — Jaipur, Jodhpur, Udaipur or Kota
in Rajasthan. Naming a district you can talk about is worth more than naming the
one you happen to live in, and a search that returns nothing is the worst
possible opening.

That single move covers **problem understanding** and **impact** at once. It is
the strongest thirty seconds you have — do not rush it.

---

## 2. The citizen side (2 min)

- Filter by district and status. Point out it is server-side, not a
  client-side trick: the result count changes.
- Open one work. Walk the money: allocated → spent → remaining, and the
  expenditure timeline. Scroll to the site photograph and sanction document.
- Point at the public status badge.

> "A citizen sees 'Normal' or 'Under review'. They never see a risk score. An
> algorithmic suspicion is not a public accusation — that distinction is
> enforced in the API, not just hidden in the UI."

- Switch the language to **हिन्दी**. Let it sit for a second.

> "Every status, every risk category, every label — and the district, the work
> category and the executing agency too, not just the menus."

If they press on the work titles still being in English, that is the prepared
answer, not a stumble:

> "Controlled vocabulary is translated — states, districts, categories,
> agencies, and the eighteen risk findings. The title of an individual work is
> free text an officer typed, so it shows as recorded. Machine-translating six
> hundred of those would give you worse Hindi, not better."

That covers **user experience** on the judges' own terms.

---

## 3. The separation, proved (1 min)

This is the moment that separates you from teams who *claim* access control.

In Window A, with the citizen signed in, open the browser devtools console and
call an admin endpoint directly:

```js
await fetch('/api/admin/projects', {
  headers: { Authorization: `Bearer ${localStorage.getItem('mplad.access_token')}` }
}).then(r => r.status)
```

Use that exact path. Verified live on 21 Sep: `/api/admin/projects`,
`/api/admin/projects/flagged`, `/api/admin/activity`, `/api/admin/dashboard` and
`/api/admin/users` all return 403 to a citizen token, and the citizen detail
response carries none of the internal fields. Do not improvise a URL — one that
does not exist returns 404 before the guard runs, which makes a working endpoint
look broken in front of a panel.

> "403. The role is re-read from the database on every single request — the
> role in the token is a hint for the UI, nothing more. And the citizen
> endpoints don't filter risk fields out; they're served by schemas that never
> had those fields. There is no code path where a filter can be forgotten."

---

## 4. The risk engine (3 min)

Switch to Window B. Open the flagged work you picked.

Walk the four questions the panel answers:

1. **What is the risk?** — category and level
2. **Why was it detected?** — the rule or the statistical finding
3. **What data caused it?** — the metric, its value, the threshold
4. **What should be done?** — the recommended action

> "Every flag names the number that triggered it. An officer can disagree with
> the system and see exactly what to check."

Then the layer badges — this is your **innovation** point:

> "Three layers, labelled separately and never blended. Deterministic rules.
> Statistical outliers against the peer group — same category, same district.
> And an unsupervised isolation forest.
>
> Our SRS originally said XGBoost. We changed it deliberately. XGBoost is
> supervised, and there is no labelled corpus of confirmed MPLAD fraud in
> India. Training one would have meant fitting the model to our own
> assumptions and then calling the result evidence. So we went unsupervised —
> the model finds statistical outliers without being told what fraud looks
> like, and every flag is explained by robust z-scores on named features.
>
> We also don't claim an accuracy figure, because without labels there is
> nothing to measure accuracy against. What we claim is that every flag is
> reproducible and explainable."

**Say this before they find it.** Volunteered, it reads as judgment. Discovered,
it reads as a discrepancy.

---

## 5. The workflow is real (2 min)

- Add a review note. Change the review status. Add a mitigation action.
- Open **Activity log**. The entries you just created are there with your name.

> "None of this is React state. Reload the page and it is still there, because
> an audit trail that disappears on refresh is not an audit trail."

- Use **Export → CSV**, then **Export → PDF report**, on the flagged list. Open
  both files.

> "CSV for analysis, PDF for the file an officer actually forwards. The PDF
> generator is written against the spec rather than pulled in as a dependency,
> so deployment stays a one-command job."

- Open **Access requests**. Approve or reject one, with a note.
- Open **Accounts**. This is the other half: who holds an official role now,
  and revoking one. Revoking returns the account to Citizen and keeps its
  history.

> "Officials can't sign themselves up. A citizen requests a role, an
> administrator decides, and the decision is written to the audit trail with
> the administrator's name on it. Administrator itself can never be requested —
> it's excluded in code, and there's a test that fails if anyone adds it."

---

## 6. Close on engineering (1 min)

> "`./verify.sh` runs the whole test suite and five check suites — including
> one that parses every admin route and fails if any of them is missing a role
> guard, one that fails if a single user-visible string is hardcoded in
> English, and one that catches a class of runtime bug we actually shipped
> once."

Run it if they seem interested. A green wall of checks is a strong last image.

---

## Questions you should expect

**"Is this real data?"**
No, and the footer says so on every page and on every export. It is synthetic,
built to mirror the real scheme's structure, with anomalies deliberately
injected so the detection engine has something to find.

Then keep going, because the follow-up is "so how would you get real data in?":

> "Three ways in today - a form for one record, CSV bulk import for an extract,
> and the same thing as an API for a scheduled job. `samples/` has a working
> CSV I can import right now. What is missing is the adapter that pulls from
> data.gov.in, and that is a per-source column mapping, not a redesign - the
> risk engine reads the model, not the seed script, so a real record is scored
> by exactly the same rules."

`docs/DATA_INGESTION.md` has the detail.

**If you have two spare minutes, do it instead of saying it.** Search **Sirohi**
on the citizen side first — no results. Then, in the officials portal,
**Projects → Bulk import**, upload `samples/mplad-works-with-errors.csv`:

> "Six rows. Four rejected, each with its line number and what is wrong with it.
> Nothing has been sent to the server yet — the reviewer decides after seeing
> this. And the API re-validates every row anyway; the browser check is a
> courtesy, not the security boundary."

Cancel that one, then import `samples/mplad-works-sample.csv` — ten rows, no
errors. Go back to the citizen window and search Sirohi again: ten works, with a
district that was empty ninety seconds ago.

That sequence answers "is this real data?", "can it take real data?" and "what
happens when the data is dirty?" in one move, and the judges watched it
happen.

**"What's your model's accuracy?"**
There is no labelled ground truth for MPLAD fraud, so an accuracy number would
be fabricated. The model surfaces statistical outliers for human verification.
Flags are ranked, explained, and auditable — they are not verdicts.

**"Will this scale?"**
Postgres is configured and blueprinted for deployment; SQLite is the local dev
default. Filters are indexed and pagination is server-side. The honest limit
today is that rate limiting is per-process, so multiple workers need a shared
counter store — that is the next hardening step and it is written down in
`docs/SECURITY.md`.

**"What would you do next?"**
In order: the data.gov.in ingestion adapter, embedding a Devanagari font so the
PDF export can be bilingual, and moving the rate-limit counters to Redis so the
API can run multiple workers.

**"Make me an editor right now."**
Do not edit code in front of them. Sign in as administrator, open **Access
requests**, approve one. The whole point is that the role changes through the
workflow, not through a developer.
