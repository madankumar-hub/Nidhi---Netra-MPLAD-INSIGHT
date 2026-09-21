# Engineering assumptions and declared deviations

Where the SRS left something open, or where a literal reading would have produced
a worse system, a decision was taken and is recorded here rather than left silent.

## 1. The machine-learning layer is unsupervised, by design

**SRS FR8/FR9 name XGBoost and sentence-transformers.**

What ships is a deterministic rule layer, a statistical peer-comparison layer,
and an **unsupervised isolation forest** — not a supervised classifier.

The reasoning:

* A supervised classifier would have to be trained on the anomalies this project
  itself injects into the synthetic dataset (SRS §2.4 — real data is not
  available). It would learn the generator, and a reported accuracy figure would
  measure nothing. Presenting that as detection performance would be dishonest.
* An isolation forest has no such problem. It is unsupervised: it fits the shape
  of whatever population is in the database and flags what sits apart from it.
  The same code, pointed at real MPLADS data, retrains on that population with
  no labelled examples and no change.
* It must work with no network, no model artefact and no training step — which is
  what makes the live demo reliable. The forest is implemented from the original
  paper in ~200 lines with no external dependency, so `pip install` never needs a
  compiler and the layer is never "unavailable".
* The requirement the system must actually meet is *explainability to a reviewing
  officer* (FR11). Every factor — rule, statistical or model — answers the same
  four questions, and the model's answer to "what data caused it" is the ranked
  per-feature deviation from the cohort median.

The upgrade paths are real, not rhetorical:

* `DUPLICATE_BACKEND=embeddings` plus `pip install sentence-transformers`
  switches the duplicate detector; `duplicate.active_backend()` reports which one
  is genuinely in use, and falls back to TF-IDF if the package is missing.
* A supervised classifier slots in as a fifth `AnalysisSource` producing
  `FactorResult` objects, once real labelled outcomes exist. Nothing in the
  routers, schemas or UI changes.

Nothing in the product claims a predictive accuracy figure, because none has been
measured.

## 2. "Confidence" means data completeness, not predictive certainty

`RiskAssessment.data_completeness_percent` records how many mandatory monitoring
fields were present when the assessment ran. It is labelled "Record completeness"
in the interface. It is deliberately *not* called confidence, because the engine
makes no probabilistic claim.

## 3. Amounts are held in rupees lakh

MPLAD sanctions are conventionally stated in lakh. All monetary columns are
`Float` in lakh and are formatted `₹ n.nn L`, with a crore roll-up above 100 lakh
on summary tiles. A production financial system would use `Numeric(14, 2)` to
avoid floating-point drift; that change is a column-type edit and a migration.

## 4. The public risk indicator is derived, not stored

FR6 asks for a simplified public-safe indicator. Rather than persist a second
"public" score that could drift out of step with the internal one, the indicator
is computed on read from review status, execution status and the internal level.
One source of truth, no synchronisation bug.

## 5. Citizen sign-up returns the OTP in development

`OTP_DELIVERY=console` (the default) logs the code and returns it as `dev_otp`
so the demo runs without a mail provider. That field is **never** populated when
`ENVIRONMENT=production`. Production delivery is wired by setting
`OTP_DELIVERY=email` and connecting a provider in `app/auth/otp.py`.

## 6. Seed passwords are generated, not hardcoded

The brief forbids hardcoded credentials; the SRS wants a system that is
meaningful immediately after setup. Both are satisfied by reading the seed
passwords from the environment and, when they are absent, generating
cryptographically random ones that are printed once and written to a git-ignored
file.

## 7. Review outcome and execution status are kept consistent

Recording a review with the outcome *Delayed* also moves the execution status to
Delayed (unless the work is already completed or cancelled), and writes both
transitions to the audit trail. Without this the two fields drift apart and the
delayed-works list stops being trustworthy.

## 8. Assessments are versioned; human mitigation work survives re-scoring

Re-assessing a work inserts a new assessment and clears `is_current` on the old
one. Engine-recommended mitigation actions are regenerated, but actions an
officer wrote themselves are carried forward if unresolved — a background
re-score must never silently discard someone's open task.

## 9. The emblem is a placeholder

`components/layout/Emblem.tsx` is an abstract civic mark. The State Emblem of
India is protected under the State Emblem of India (Prohibition of Improper Use)
Act, 2005 and is not reproduced here. The SRS asks for an "emblem placeholder",
which is what this is.

## 10. Members of Parliament in the dataset are fictional

Names are generated by combining fixed first- and surname lists. No real public
figure is associated with any record, and the footer of every citizen page states
that the data is synthetic.

## 11. Schema is created from metadata; Alembic is the production path

`Base.metadata.create_all()` keeps first-run setup to a single command. The
models are written in SQLAlchemy 2.0 typed style, which Alembic's autogenerate
reads cleanly; `docs/DATABASE.md` has the three commands to adopt it.

## 12. Bulk import is API-only

FR15 is implemented as `POST /api/admin/projects/bulk-import`. There is no upload
screen, because a file-upload and column-mapping UI is a feature in its own right
and a half-built one would be worse than none. The endpoint validates every row
and reports created, skipped and per-row errors.

## 13. Hindi is the second language, with English fallback

SRS §8 lists regional-language access as future scope; the brief asks for English
and Hindi now. The i18n layer is a typed key dictionary with runtime fallback to
English for any missing key, so adding a third language is one file and one entry
in `LANGUAGES`.

### Where the translation stops, and why

Three things arrive from the API as English strings, and they are handled
differently on purpose.

**Enums** — `In Progress`, `Schedule Risk`, `CRITICAL`. Defined in
`app/core/enums.py`, translated by `i18n/enums.ts`. The English value travels on
the wire; only the rendered text changes.

**Controlled vocabularies** — 15 states, 58 districts, 58 constituencies, 20 work
categories, 12 executing agencies and the 18 risk-factor titles. These are stored
as plain strings on the row, so they *look* like free text, but each is a closed
list maintained in `seed/reference_data.py` or in the risk rules, and MPLADS
publishes all of them in Hindi. They are translated by `i18n/vocabulary.ts`, and
`tests/test_vocabulary_coverage.py` fails the build if the backend gains a value
the map does not cover.

**Genuine free text** — the title and description of an individual work, the MP's
name, the contractor, the block, and the evidence line under each risk factor
("progress is 34% against a planned 71%"). These are per-record, written by an
officer or generated with measured numbers in them. They stay as entered.

That last boundary is deliberate, not an omission. Machine-translating 600 unique
work titles would produce worse Hindi than leaving them alone, and a government
portal shows a sanctioned work's title as it was recorded. The result is the same
split a bilingual government report uses: a Hindi finding above an English
evidence line. If a reviewer asks why a work title is still in English, that is
the answer.


## PDF export is English-only

`app/services/pdf_writer.py` uses the built-in PDF Helvetica faces, which are
single-byte (WinAnsi). Devanagari cannot be rendered without embedding and
subsetting a TrueType font, which is a substantially larger piece of work than
the rest of the writer.

So the PDF export is English regardless of the interface language. Unmappable
characters are transliterated where there is a sensible equivalent (the rupee
sign becomes "Rs.", curly quotes become straight ones) and dropped otherwise,
rather than producing a file a reader will refuse to open. A test asserts that
Devanagari input still produces a valid document.

The rest of the application is fully bilingual; this is the one surface that is
not, and embedding a Devanagari font is the documented fix.
