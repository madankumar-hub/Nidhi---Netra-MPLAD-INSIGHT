# Judge readiness — an honest self-assessment

Written from the other side of the table: what a Smart India Hackathon judge is
likely to ask, what this project answers well, and where it is still thin.
Read this before the finale, not after.

---

## The scorecard

| Criterion | Verdict | Why |
|---|---|---|
| **Technical complexity** | Strong | Real full-stack system: 55 API routes, 12 tables, RBAC enforced server-side, an explainable three-layer risk engine, 40 automated tests. Not a mockup. |
| **Novelty** | Good, not unique | Transparency portals exist. The differentiator is the *pairing* — a public portal and an audit workspace on one dataset, with a hard boundary between them — plus explanations an officer can act on. |
| **Feasibility** | Strong | Runs on a laptop in one command, deploys to a free tier, uses one database and no proprietary service. Nothing here needs a research budget. |
| **Practicality** | Strong | Every finding names the register or the certificate an officer should ask for. The mitigation tracker assigns a party and a due date. This is how the work is actually supervised. |
| **Scalability** | Adequate | Stateless API, indexed queries, batch scoring separated from request handling. Honest gap: not load-tested. |
| **Impact** | Strong on paper | MPLADS is roughly ₹5 crore per MP per year across 790 MPs. Even a small improvement in detection of stalled or over-drawn works is large in absolute terms. Say the number. |
| **Demo quality** | Depends on you | The material is there. See the script below. |
| **Presentation** | Needs work | There is no deck and no architecture diagram image. That is your job before the finale. |

**Overall: this would clear the technical bar comfortably and finish in the
upper band.** What separates the upper band from a win is usually the demo and
the answer to one specific question — below.

---

## The question that decides it

> *"The problem statement says AI-powered. Where is the AI?"*

Every judge asks this. Weak teams either bluff or fold. The answer here is
neither, and it is worth rehearsing until it is thirty seconds long:

> "Three layers. Deterministic rules, statistical peer comparison, and an
> unsupervised isolation forest fitted on the live project population.
>
> We deliberately did **not** train a supervised classifier, and that was a
> considered decision. Real MPLADS data isn't available to us, so a supervised
> model would have to be trained on the anomalies we inject into our own
> synthetic dataset. It would learn our generator, and any accuracy figure we
> quoted would be meaningless. We would rather show you something honest.
>
> The isolation forest needs no labels. It learns the shape of the normal
> population and flags what sits apart from it — so it transfers to the
> ministry's real data on day one with no retraining. It works on eleven
> features at once, which is the point: it catches the record where every single
> number is inside its normal band but the *combination* occurs nowhere else.
> A threshold rule can never express that.
>
> And it explains itself. Here" — *open a flagged work* — "the score, the
> percentile, and the three features that put it there, measured against the
> cohort median."

Then show them `/admin/analytics`, where a card lists which layers are actually
live on the running instance.

**Why this wins the exchange:** you have converted the weakest-looking part of
the project into evidence of judgement. Judges see a dozen teams claim 97%
accuracy on data they generated themselves. Being the team that explains why
that number would be worthless is memorable.

---

## The other four questions

**"Is this just a dashboard?"**
Open a work, record a review, watch the status change, then show the activity
trail. It is a workflow system with an audit trail, not a chart page.

**"How do you know a citizen can't see the risk scores?"**
This is the best-defended part of the project, so invite the question. Sign in
as the citizen account and open a work — no risk score anywhere. Then open
`backend/api-examples.http` and run the 403 block: six admin endpoints, six
refusals, on a valid token. Then say the sentence that matters: *"It isn't
filtered out in the UI. The citizen response model doesn't contain those fields,
and the role is re-read from the database on every request — editing the token
achieves nothing."* There is a test that asserts exactly this
(`test_citizen_detail_carries_no_internal_fields`).

**"How does someone become an officer? Can anyone make themselves an admin?"**
No, and the demo answers it in three clicks. Sign-up creates a Citizen and the
schema has no role field. Show `/request-access` — a citizen asks for Officer or
Auditor with their office and posting ID. Then sign in as the **admin** account
and open **Access requests**: two plausible requests from `gov.in` and `nic.in`
addresses, and one from a Gmail-style address flagged as outside the government
domains. Approve one and show the audit trail entry naming who decided. Finish
with the line: *"Administrator can't be requested at all — it's not in the
requestable set, and the server rejects it even if you post it directly."*

**"Would this work with real data?"**
`POST /api/admin/projects/bulk-import` takes the same shape MPLADS publishes on
data.gov.in. The model is unsupervised so it refits on whatever arrives. Be
straight that the mapping layer for the official schema is not written yet.

**"What would you do with three more months?"**
Have a real answer ready. Suggested: the data.gov.in ingestion adapter, a
geographic map view, real OTP delivery,
Alembic migrations, load testing, and the official-portal ingestion adapter.
Judges respect a team that knows its own gaps — and the gaps are listed in
`docs/SECURITY.md` and `docs/DEPLOYMENT.md` already.

---

## The demo — six minutes

Judges visit for a few minutes at a time. Have this rehearsed so tightly you can
do it in four when they are in a hurry.

| Time | What | Say |
|---|---|---|
| 0:00 | Citizen homepage | "Any citizen can look up any sanctioned work. This is live data from the database, not a mockup." |
| 0:40 | Search → open a work | "Follow the money: allocated, spent, remaining, and the expenditure timeline. Progress against the sanctioned schedule." |
| 1:20 | Point at the status badge | "This is all a citizen sees about risk — 'Normal' or 'Under review'. No score. That is deliberate." |
| 1:50 | Sign in as auditor → dashboard | "The same data, for the officer. Delayed works, works awaiting review, open indicators." |
| 2:30 | Open a flagged work → Risk tab | **The centrepiece.** Walk one factor through all four blocks: what, why, what data, what to do. |
| 3:30 | Scroll to the ML factor | The thirty-second answer above. |
| 4:15 | Mitigation tab → resolve an action | "Every recommendation becomes a tracked action with an owner and a due date." |
| 4:45 | Record a review → Activity tab | "Persisted, and it appears in the audit trail with who and when." |
| 5:15 | Analytics page | "Every figure computed from the database. And this card shows which analysis layers are actually running." |
| 5:45 | Close | The impact number, and one honest gap you are working on. |

**Rehearse the transitions, not the words.** The clicks are what go wrong under
pressure.

---

## Before the finale — a checklist

Highest value first.

- [ ] **Deploy it** and put the URL on a QR code on your poster. A judge who
      opens it on their own phone remembers you. (`docs/DEPLOYMENT.md`)
- [ ] **Rehearse the AI answer** until it is thirty seconds, not ninety.
- [ ] **Make an architecture diagram image.** The text one in
      `docs/ARCHITECTURE.md` is accurate but you cannot point at it on a slide.
- [ ] **Learn the impact number** — MPLADS outlay per MP per year × number of
      MPs. Say it in the first minute.
- [ ] **Screen-record the demo** on your phone as a Wi-Fi fallback.
- [ ] **Run `python -m tests.run_all` in front of them** if a technical judge
      digs in. 40 passing tests ends that line of questioning.
- [ ] **Decide who speaks.** One narrator, one on the keyboard. Teams that talk
      over each other lose the thread.

---

## What is genuinely still missing

Do not let a judge find these before you name them.

| Gap | Effort | Worth doing before the finale? |
|---|---|---|
| No map view, though coordinates are stored | ~2 hours | Deliberately out of scope. Coordinates are correct, district-accurate and covered by `tests/test_geography.py`, and the API serves them — so a map is presentation work, not data work |
| No email notification when access is approved | ~2 hours | Nice to have; the decision is visible in-app already |
| ~~No PDF export (FR12 says CSV/PDF)~~ | done | Built: `app/services/pdf_writer.py`, landscape A4, no dependency |
| Bulk import has no UI (FR15 is API-only) | ~half a day | Only if time allows; the endpoint exists |
| Duplicate detection is TF-IDF, SRS says sentence-transformers | ~2 hours | Optional — the pluggable backend is already there |
| No load test behind the "<500 ms" claim | ~2 hours | Do it if a judge is likely to press on scale |
| No ingestion adapter for the real data.gov.in schema | ~1 day | Strong answer to "would this work for real?" |
| No SMS or regional-language access | ~1 day | SRS lists it as future scope; say so rather than build it |

Naming your own gaps before the judge does reads as maturity. Pretending they
are not there reads as inexperience, and judges have seen both many times.
