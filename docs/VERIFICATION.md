# Verification

What was executed, what it proves, and what it does not.

## Executed in the build environment

> Current totals: **101 tests across 12 modules**, plus 4 whole-project checks
> (static analysis, API contract, translations, TypeScript). All passing.

Everything below runs in one command from the project root:

```bash
./verify.sh          # macOS, Linux, Git Bash
```

```powershell
.\VERIFY.bat         # Windows - same five suites
```

That wraps five suites: the backend tests, the backend static check, the API
contract check, the translation check and the TypeScript check. The backend
tests alone are:

```bash
cd backend && python -m tests.run_all
```

### 1. Risk-engine unit tests — 16 of 16 passing

```bash
cd backend && python -m tests.test_risk_engine
```

These run on the standard library alone: no database, no web framework, no ORM.
That is possible because `app/risk/*` imports the `Project` model only under
`typing.TYPE_CHECKING` and otherwise works against plain attributes, so
`tests/fake_project.py` can stand in for the ORM row.

Covered:

* a healthy work scores LOW and below 25;
* schedule slippage, imminent deadline with low progress, overdue-and-open,
  formally delayed, stalled reporting, expenditure ahead of progress, underspend
  late in the window, cost overrun against the estimate, completion
  inconsistencies, incomplete records and clustered citizen reports each fire on
  the record that should trigger them;
* the statistical layer flags an allocation outlier and tags it `statistical`;
* the duplicate detector matches a near-identical description, scores it above
  0.9, and does **not** match an unrelated work;
* every factor carries a non-empty title, detected indicator, evidence,
  explanation and recommended action — the four questions the brief requires;
* scores stay within 0–100 and a severe record scores strictly higher than a
  mild one;
* the engine reports external AI as disabled when it is not configured;
* derived metrics are arithmetically correct (duration, elapsed, remaining,
  time-elapsed %, utilisation, utilisation-vs-progress gap).

### 2. Cohort simulation — 300 synthetic works

Run over a randomly generated cohort with a peer group and cohort statistics
supplied, every one of the 16 indicator codes fires at least once, all scores
stay inside 0–100, and the level distribution spans LOW through CRITICAL
(49 / 160 / 90 / 1 on the sample run). Aggregation weights were tuned against
this run so that a genuinely severe record can reach CRITICAL and a merely
untidy one cannot.

### 3. Machine-learning tests — 8 of 8 passing

```bash
cd backend && python -m tests.test_anomaly_model
```

The isolation forest is held to behaviour, not just to running without error:

* the feature vector has the declared shape and fixed order;
* the model **refuses to fit** below the minimum cohort rather than pretending,
  and reports itself unavailable;
* a planted multivariate outlier — one whose individual figures are each
  plausible but whose combination occurs nowhere else — scores above the
  population mean, clears the flag threshold, and lands at or above the 95th
  percentile, while a typical record from the same cohort is **not** flagged;
* the resulting finding names the features that drove it, with percentile and
  sigma figures present in the text;
* fitting is deterministic for a given seed, so a demo is reproducible;
* the engine records `machine_learning` as a source only when a model was
  actually supplied;
* the model's factor cannot dominate the score on its own.

### 4. Security tests — 9 of 9 passing

```bash
cd backend && python -m tests.test_security
```

Password hashing round-trips, per-hash salting (two hashes of the same password
are never equal), over-long passwords are handled rather than rejected, and a
malformed hash returns False instead of raising.

On the token side: access and refresh tokens are typed separately so one cannot
be presented where the other is required; a refresh token carries no role claim;
an expired token is rejected; garbage input is rejected; and — the one that
matters — a token whose payload has been re-encoded to claim `"role": "admin"`
is rejected, because the signature no longer matches.

### 5. Schema contract tests — 7 of 7 passing

```bash
cd backend && python -m tests.test_schema_contracts
```

These assert the citizen/admin separation **in code** rather than leaving it to
review. A list of internal field names — `risk_score`, `risk_level`,
`review_status`, `factors`, `notes`, `reviews`, `mitigations`,
`open_risk_factors`, `open_mitigations`, `schedule_variance`, `last_reviewed_at`,
`activity` — is checked against the serialised output of
`ProjectPublicSummary` and `ProjectPublicDetail`; the test fails if any of them
appears. The same list is asserted *present* on the admin models, so the two
cannot be accidentally converged.

Also covered: settings load and parse a comma-separated `CORS_ORIGINS` (a real
pydantic-settings trap this caught before packaging); external AI reports itself
as unconfigured; `RiskAssessmentOut` validates from a plain object and splits the
stored `analysis_sources` string into a list; the generic `Page[T]` wrapper
works; and six categories of invalid input are rejected — malformed email, empty
password, out-of-range sanction year with a negative allocation, progress above
100%, a status outside the enum, and a note below the minimum length.

### 6. Access-control tests — 8 of 8 passing

```bash
cd backend && python -m tests.test_access_control
```

The schema tests above prove a citizen response *cannot carry* internal fields.
These prove the route layer refuses the request in the first place, which is the
claim a reviewer will actually probe. `app/routers/*.py` is parsed with `ast` and
every route is matched against the guard it declares, so the assertions are about
the shipped code rather than a description of it.

Covered: every `/admin` route declares one of `require_internal`,
`require_reviewer`, `require_elevated` or `require_admin`; the write and decision
routes take the stricter two rather than the read guard; `admin` can never appear
in the set of roles a citizen is allowed to request; and the role used for
authorisation is re-read from the database on each request rather than taken from
the token claim.

### 7. Export tests — 13 of 13 passing

```bash
cd backend && python -m tests.test_pdf_export
```

The writer is hand-rolled, so these check what a broken PDF writer gets wrong:
the `%PDF-1.4` header and `%%EOF` trailer, cross-reference offsets that land
exactly on an object header, `/Size` matching the object count, pagination across
200 rows, and parenthesis/backslash escaping — an unescaped bracket terminates a
PDF string early and corrupts the file.

Two are regressions from defects this suite caught before packaging: text is
measured with the real Helvetica AFM advance widths rather than an average-width
estimate (which let `MPLAD-RJ-700` run into the next column), and the report's
column widths are read out of `export_service.py` with `ast` and asserted to fit
inside the 761.89pt text area of a landscape A4 page.

Devanagari is transliterated rather than rendered — the built-in PDF fonts are
single-byte. The test asserts it degrades to a valid file instead of crashing,
and the limitation is recorded in `docs/ASSUMPTIONS.md`.

Two more cover provenance. `docs/DATA_INGESTION.md` promises every export says
the data is synthetic; the PDF footer did, and for a while the CSV said it
nowhere — so a file of government-shaped numbers could travel with nothing
marking it as invented, and the documentation was simply wrong. The CSV now
carries a `data_source` column on every row, and these tests fail if the column
is dropped, if it is declared but never written, or if the wording stops
disclaiming official status.

### 8. Geography tests — 7 of 7 passing

```bash
cd backend && python -m tests.test_geography
```

These exist because the original seed placed each work at a random point in a
box spanning roughly 8.5–32.5N, 70–92E — which contains Pakistan, Nepal, China,
Bangladesh and both seas. Coordinates are now anchored to district headquarters
with bounded jitter.

Covered: every seeded district has a coordinate; every coordinate is inside
India; no two districts share a point; 200 generated points per district all land
within 40km of their own headquarters and inside India; jitter never produces a
repeated point; and an unknown district returns `None` rather than an invented
location — an absent coordinate is honest, a confident wrong one is not.

Nothing in the current UI plots these. They are kept correct because the API
serves them and the CSV import accepts them.

### 9. Vocabulary coverage tests — 9 of 9 passing

```bash
cd backend && python -m tests.test_vocabulary_coverage
```

The translation check below proves the *dictionary* is complete. It cannot prove
the *vocabularies* are, because those live in `seed/reference_data.py` and in the
risk rules rather than in a translation file — and `translateEnum` falls through
to the raw English value when a key is missing. A gap is therefore invisible at
runtime and surfaces only as an English word on a Hindi page, in front of a
judge. That is exactly how "Drinking Water Facility" survived in the category
filter until someone switched language and looked.

These tests close the loop by reading the Python source of record and the
TypeScript map and failing when they drift: every state, district, parliamentary
constituency, work category, executing agency and risk-factor title the backend
can emit must have an entry. Two more guard the guard — one asserts the regex
parser actually found the maps (a silently-empty parse would make every other
assertion pass), one fails if any value was left as Latin text.

Proven against a deliberate regression: deleting a district and leaving one
category untranslated failed three tests by name.

### 10. Sample CSV tests — 9 of 9 passing

```bash
cd backend && python -m tests.test_sample_csv
```

`samples/mplad-works-sample.csv` is imported live in front of judges, so it is
held to the same standard as code. The file is parsed with the same rules
`BulkImportDialog.parseCsv` applies — and the required-column list is read out of
that component, so a rename on either side fails here rather than on stage.

Then every controlled value is checked against its source of record: categories
against `reference_data.CATEGORIES`, agencies against `AGENCIES`, statuses against
`ProjectStatus`, and each district against both `DISTRICT_COORDINATES` and
`vocabulary.ts`. This is the check that matters, because a *near-miss* category
imports perfectly well and then groups with nothing, adds a count-of-one entry to
the filter dropdown, and shows English on a Hindi page. Nothing errors; it is
simply wrong, and only visible if someone looks.

Also asserted: coordinates land within 40km of the district headquarters, and the
rows are internally consistent (nothing spends more than it was allocated, a
Completed work is at 100%, a Not Started work is at 0%).

The counterpart file `mplad-works-with-errors.csv` must keep *failing* — 2 rows
accepted, 4 rejected, each naming its line number — or the rejection screen has
nothing to show during the demo.

### 11. Accessibility tests — 5 of 5 passing

```bash
cd backend && python -m tests.test_accessibility
```

The GIGW 3.0 claim rests partly on structural affordances that are invisible
until someone navigates by keyboard, so they are easy to add on one layout and
forget on the other. That is what happened: the citizen portal had a skip link
and the officials portal did not, meaning an officer tabbing through the app hit
the whole sidebar on every route change.

Asserted per layout: a `.skip-link` exists, its `href="#target"` points at an
`id` **in the same file** (a skip link to a missing id looks right in review and
does nothing when pressed), and there is exactly one `<main>` landmark. Plus: the
`.skip-link` rule declares a focus state and is hidden when unfocused, and the
accessibility bar still offers text-size and contrast controls.

Proven against the regression — removing the officials-portal skip link fails two
tests by name.

Worth recording: the first version of the focus test looked for a literal
`.skip-link:focus` selector and failed against perfectly correct CSS, because the
rule uses Tailwind's `focus:` variant inside `@apply`. The test was wrong, not the
stylesheet. It now accepts either form.

### 12. Deployment safety tests — 8 of 8 passing

```bash
cd backend && python -m tests.test_deployment_safety
```

These guard the gap between "works on a laptop" and "safe on a public URL".
Every one of them protects against a deployment that looks completely healthy —
green health check, pages loading — while being wrong in a way nobody notices
until it matters.

The most serious: **production now refuses to start on the development signing
key.** That default lives in this repository, so a production instance still
using it is not a misconfiguration, it is an authentication bypass — anyone who
can read the source can mint a token claiming `"role": "admin"` and it will
verify. The previous behaviour logged an error and started anyway, which is not
a control; a log line nobody reads protects nothing.

Also asserted: `.env.example` carries no real value for any key ending in
PASSWORD / SECRET / API_KEY / TOKEN; the four seed passwords are blank there, so
copying the file cannot set a known password on a deployment; `.gitignore` has
an **exact** rule for each of `.env`, `*.db`, `*.sqlite`, `*.pem`, `*.key`,
`.venv/`, `node_modules/`, `dist/` and the credentials file, and still has the
`!.env.example` negation; no file under `app/` or `seed/` hardcodes a
credential; every secret in `render.yaml` is `generateValue` or `sync: false`;
error detail is suppressed in production; and console OTP delivery is gated on
the environment, since returning the OTP to the caller in production would let
anyone sign in as anyone.

Each guard was proven by reintroducing the fault it exists for. That exercise
found two of these tests were themselves broken: the `.gitignore` check used a
substring match, so deleting the `.env` rule still passed — the string survives
inside `.env.*` — and the `.env.example` scanner flagged
`ACCESS_TOKEN_EXPIRE_MINUTES=120` as a leaked credential because "TOKEN" appears
in the name. A test that cannot fail reads as coverage while providing none, and
one that cries wolf gets switched off. Both are fixed and re-proven.

### 13. Backend static analysis — passing

```bash
cd backend && python tools/static_check.py
```

* 83 modules parse.
* Every `from app...` / `from seed...` import resolves to a module that exists
  and to a name that module actually defines — no unresolved imports anywhere.
* 64 routes, no duplicate `(method, path)` pair.
* Every route under `/admin` carries an explicit role-guard dependency (47 routes
  are guarded). The check **fails the build** if one is added without a guard.
* No call passes a keyword argument that `**model_dump()` already supplies — a
  check added after that exact defect shipped a `TypeError` on every project
  detail page.
* All 10 response schemas validated `from_attributes` line up field-by-field with
  the ORM models they are built from.

### 14. Frontend type check — clean

The full `src/` tree type-checks under `strict`, `noUnusedLocals` and
`noUnusedParameters`. It caught and fixed real defects before packaging:
several files referenced the `React` namespace without importing it, which would
have failed `npm run build` under `jsx: react-jsx`.

### 15. API contract cross-check — 55 of 55 calls resolve

```bash
python tools/check_api_contract.py
```

Parses the FastAPI decorators on one side and the frontend API client on the
other, normalises path parameters and query builders, and asserts that every call
the web client makes resolves to a real route with a matching method. There are
no fabricated endpoints.

The check also reports the 5 backend routes the web client never calls, rather
than failing on them: `/api/auth/refresh` is used by the token interceptor rather
than the client surface, and `/api/auth/change-password`, `/api/auth/officials`,
`/api/admin/dashboard` and the risk-history route are deliberate API-only
endpoints. Reported, not hidden — an unused route should be a decision.

### 16. Chart palette validation — passing

The categorical series palette was checked for lightness band, chroma floor,
adjacent-pair colour-vision-deficiency separation, normal-vision separation and
contrast against the chart surface. Status colours (risk levels, execution
states) are a reserved set, never reused as a series colour, and are always
paired with a text label so meaning is never carried by colour alone.

## Not executed in the build environment

The sandbox this was assembled in has no access to PyPI or the npm registry
(`Host not in allowlist: pypi.org` / `registry.npmjs.org`), so `pip install`
and `npm install` could not run. That means these steps were **not** executed
here and should be run once on your machine:

```bash
cd backend
pip install -r requirements.txt
python -m seed.seed_data --reset --projects 600
uvicorn app.main:app --reload --port 8000
# then: open http://localhost:8000/docs

cd ../frontend
npm install
npm run build      # tsc -b && vite build
npm run dev
```

The static checks above were built specifically to cover what a missing runtime
otherwise leaves unverified — import resolution, route/guard coverage,
schema-to-model alignment, and the frontend-to-backend contract. What they cannot
prove is runtime behaviour inside SQLAlchemy and Pydantic: query execution,
relationship loading and serialisation of live ORM objects.

## Post-install smoke test

Run this once the dependencies are installed; it exercises the paths the static
checks cannot reach, including the citizen/admin separation.

```bash
# 1. Health and database connectivity
curl -s localhost:8000/api/health

# 2. Public search works without a token
curl -s "localhost:8000/api/projects?search=water&page_size=3" | head -c 400

# 3. Sign in (use the address and password from .seed-credentials.txt)
CITIZEN=$(curl -s -X POST localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"citizen@example.com","password":"<password>"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

AUDITOR=$(curl -s -X POST localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"auditor@mplad.gov.in","password":"<password>"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 4. THE IMPORTANT ONE: a citizen must be refused internal data.
#    Expect 403 insufficient_role on every one of these.
for path in /api/admin/dashboard /api/admin/projects /api/admin/projects/1/risk \
            /api/admin/projects/1/notes /api/admin/projects/1/activity \
            /api/admin/projects/1/mitigation /api/admin/projects/1/reviews; do
  printf '%-45s %s\n' "$path" \
    "$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $CITIZEN" "localhost:8000$path")"
done

# 5. The same paths must succeed for an auditor (200).
for path in /api/admin/dashboard /api/admin/projects/1/risk /api/admin/projects/1/notes; do
  printf '%-45s %s\n' "$path" \
    "$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $AUDITOR" "localhost:8000$path")"
done

# 6. The citizen detail response must contain no internal fields.
curl -s localhost:8000/api/projects/1 | python - <<'PY'
import json, sys
data = json.load(sys.stdin)
leaked = [k for k in ("risk_score", "risk_level", "factors", "notes",
                      "reviews", "mitigations", "activity", "review_status")
          if k in data]
print("LEAKED FIELDS:", leaked if leaked else "none")
PY

# 7. Writes persist: add a note, then read it back.
curl -s -X POST localhost:8000/api/admin/projects/1/notes \
  -H "Authorization: Bearer $AUDITOR" -H 'Content-Type: application/json' \
  -d '{"content":"Smoke-test note","note_type":"General Note"}' > /dev/null
curl -s -H "Authorization: Bearer $AUDITOR" localhost:8000/api/admin/projects/1/notes | head -c 300

# 8. Status change is persisted and audited.
curl -s -X POST localhost:8000/api/admin/projects/1/status \
  -H "Authorization: Bearer $AUDITOR" -H 'Content-Type: application/json' \
  -d '{"status":"Delayed","reason":"Smoke test"}' > /dev/null
curl -s -H "Authorization: Bearer $AUDITOR" localhost:8000/api/admin/projects/1/activity | head -c 300
```

Steps 4 and 6 are the ones that matter most: they are the machine-checkable form
of the citizen/admin separation the brief insists on.

---

## Translation check — `tools/check_i18n.py`

Key parity between `en.ts` and `hi.ts` was never the real problem: an earlier
build had perfect parity (345/345) while the UI still rendered English, because
status values arrive from the API as raw enum strings and were being printed
directly. This check therefore does three things:

1. **Parity** — every key exists in both dictionaries.
2. **Untranslated values** — no Hindi value is byte-identical to its English
   counterpart, apart from a short allowlist of proper nouns (`MPLADS`, `CSV`).
3. **Hardcoded English** — no user-visible literal sits in a `.tsx` file outside
   a `t()` or `tEnum()` call. This scans JSX text nodes and the attributes that
   render to screen (`label`, `title`, `placeholder`, `description`, `hint`).

Check 3 is what would have caught the original bug. It is deliberately sensitive
enough to flag a two-word button label.

API enum values are translated through `src/i18n/enums.ts`, which maps every
wire value from `app/core/enums.py` — statuses, risk levels, risk categories,
likelihood, impact, note types, report categories, roles and activity verbs.
An unmapped value falls through to English rather than rendering blank, so a new
backend enum degrades gracefully instead of breaking the page.

---

## Rate-limiting tests — 9 of 9 passing

```bash
cd backend && python -m tests.test_rate_limit
```

The limiter is plain Python with FastAPI imported lazily, so these run with no
web framework installed. Covered: requests under the limit pass; the request
past the limit is refused with a sane `Retry-After`; callers are counted
independently; the window genuinely expires; idle callers are evicted rather
than accumulating forever.

Two of the tests are about policy rather than mechanics:

* `test_credential_endpoints_are_rate_limited` parses `app/routers/auth.py` with
  `ast` and fails if `login`, `request_signup_otp`, `complete_signup` or
  `request_official_access` is missing a limiter dependency. Adding a new auth
  route without a limit breaks the build.
* `test_login_limit_is_strict_enough_to_matter` fails if the configured limit
  would permit more than 600 sign-in attempts per hour — a limit loose enough to
  allow online guessing is not a limit.

### What it does not prove

The limiter is in-process. Under multiple uvicorn workers each worker holds its
own counters and the effective limit multiplies by the worker count. This is
stated in `docs/SECURITY.md` and is the next hardening step, not a claim of
distributed rate limiting.

---

## TypeScript check without the npm registry

The build environment has no access to the npm registry, so `node_modules`
cannot be installed there. Rather than skip type checking, `tools/typecheck/`
holds minimal declaration files for `react`, `react-dom` and `react-router-dom`,
and `generate_stubs.py` **generates** the `lucide-react` and `recharts`
declarations by scanning the app's own import statements.

Generating rather than hand-writing those two matters: the stub contains exactly
the symbols the app imports, so importing an icon that does not exist fails the
offline check too.

What this catches: unresolved imports and paths, unused locals and parameters,
hook misuse, our own component prop mismatches, and — most valuable — any
`t('...')` call whose key is not in the dictionary, because `TranslationKey` is
a union of the real keys.

What it does not catch: DOM prop typos, since `IntrinsicElements` is permissive.
`npm install && npm run build` on a normal machine uses the real typings and is
the authoritative check.
