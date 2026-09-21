# Security

## Authentication

* Passwords are hashed with **bcrypt**, called directly rather than through
  `passlib`. Plaintext is never stored, logged or returned. Input is truncated to
  bcrypt's 72-byte limit before hashing, which is the limit bcrypt itself
  enforces.
* Access and refresh tokens are **HS256 JWTs** issued with **PyJWT**, carrying a
  `type` claim
  (`access` / `refresh`). A refresh token is rejected anywhere an access token is
  required, and vice versa.
* Token lifetimes are configuration, not code: `ACCESS_TOKEN_EXPIRE_MINUTES`
  (default 120) and `REFRESH_TOKEN_EXPIRE_MINUTES` (default 7 days).
* Login failures return one message for both an unknown address and a wrong
  password, so the endpoint does not confirm which addresses are registered.
* Citizen sign-up uses an emailed one-time code. Codes are **hashed at rest**,
  expire after `OTP_EXPIRY_MINUTES`, are single-use, and lock after five wrong
  attempts.

## How an account becomes an official one

This is the part people ask about first, so it is worth stating plainly.

**A role is never self-assigned.** The public sign-up handler pins
`role=UserRole.CITIZEN` in code, and the sign-up schema has no `role` field at
all — there is no request body a caller could craft to arrive as an
administrator. A test asserts both facts against the source
(`test_public_signup_hardcodes_the_citizen_role`).

The only route to Officer or Auditor is:

1. the person signs up and signs in as an ordinary **Citizen**;
2. they submit a request at `/request-access`, naming the role, their office,
   their posting ID and why they need it — this changes nothing about the
   account, it inserts a row;
3. an existing **Administrator** reviews it at `/admin/access-requests` and
   approves or declines, with an optional note;
4. only on approval does the service write the new role, and an `ActivityLog`
   entry records who decided, when, the previous role and the granted one.

**The Administrator role cannot be requested at all.** `ACCESS_REQUESTABLE_ROLES`
contains only Officer and Auditor, and the service rejects anything else even if
a caller posts it directly. New administrators are provisioned by an existing
administrator through `POST /api/auth/officials`.

**An email allowlist narrows who may ask.** `OFFICIAL_EMAIL_DOMAINS` (default
`gov.in,nic.in`) and `OFFICIAL_EMAIL_ALLOWLIST` mark which addresses count as
government ones. With `OFFICIAL_ALLOWLIST_ENFORCED=true` a request from anywhere
else is refused outright; with it false the request is still queued but the
administrator sees it flagged as an outside address. Note the matching is on the
domain, not a substring — `attacker@notgov.in` does not match `gov.in`, and
there is a test for exactly that case.

Access already granted can be taken back: an administrator can revoke an
official account to Citizen from the same screen, which is also audited. An
administrator cannot revoke themselves, and administrators cannot be revoked
from that screen at all.

## Authorisation

The role in the JWT is a **hint for the interface only**. Every protected
request re-reads the user row from the database and checks `is_active` before the
role is evaluated (`app/core/deps.py`). Editing a token to claim `"role":"admin"`
therefore achieves nothing.

Four guards are layered:

| Dependency | Admits |
|---|---|
| `get_current_user` | any active signed-in account |
| `require_internal` | Officer, Auditor, Admin — read access to internal data |
| `require_reviewer` | Officer, Auditor, Admin — write actions |
| `require_elevated` | Auditor, Admin — delete, bulk import |
| `require_admin` | Admin — provisioning official accounts |

`tools/static_check.py` fails the build if any route under `/admin` is declared
without one of these dependencies.

## Field-level masking for the Citizen role

Masking is achieved by **separation, not filtering**. The citizen endpoints are
served from `ProjectPublicSummary` / `ProjectPublicDetail`, which do not contain
`risk_score`, `risk_level`, risk factors, mitigation actions, notes, reviews or
the activity trail. There is no conditional branch that could be inverted and no
serializer flag that could be forgotten; the data simply is not in the response
model, and the citizen route handlers never load it.

What a citizen does receive about risk is a derived two-value indicator —
`Normal` or `Under Review` — computed in `project_service.public_indicator`.

A citizen token calling any `/api/admin/*` route receives:

```json
{ "code": "insufficient_role",
  "message": "This resource is restricted to authorised officials.",
  "detail": null }
```

with HTTP 403.

## Input validation

Every request body is a Pydantic model with explicit bounds — string lengths,
numeric ranges, percentage limits, enum membership. Validation failures return a
422 with the offending field named. Query parameters are typed and constrained
(`page >= 1`, `page_size <= 200`, `sort_dir` restricted by pattern). All database
access goes through SQLAlchemy's expression language, so values are always bound
parameters and never interpolated into SQL.

## Secrets

* Nothing sensitive is committed. `.env` is git-ignored; only `.env.example` ships.
* `JWT_SECRET_KEY`, `DATABASE_URL` and `AI_API_KEY` come from the environment.
* The seed script **refuses to invent a password silently**: if a `SEED_*_PASSWORD`
  variable is unset it generates a cryptographically random one, prints it once
  and writes it to `backend/.seed-credentials.txt`, which is git-ignored and meant
  to be deleted after use.
* The application logs a hard error at startup if it is running with
  `ENVIRONMENT=production` and the development default signing key.
* `docker-compose.yml` refuses to start without `POSTGRES_PASSWORD` in the
  environment rather than defaulting to something weak.

## Error handling

All errors leave the API in one envelope — `{ code, message, detail }` — so the
client can react to `code` rather than parsing prose. Unexpected exceptions are
logged server-side with a stack trace and returned as a generic
`server_error`; the exception text is included only when `ENVIRONMENT` is not
production.

## Known gaps (honest list)

These are deliberate scope decisions for a hackathon build, not oversights:

* **No token revocation list.** Signing out discards the token client-side; a
  stolen access token remains valid until it expires. A production deployment
  would add a short access-token lifetime plus a server-side refresh-token store.
* **Rate limiting is per-process, not distributed.** Credential endpoints, the
  citizen report endpoint and the official-access request are rate limited in
  `app/core/rate_limit.py` using an in-process sliding window. Run behind more
  than one uvicorn worker and each worker keeps its own counters, so the
  effective limit multiplies by the worker count. Moving to several workers
  means moving the counters to a shared store (Redis) or enforcing the limit at
  the gateway - not enlarging the in-memory map.
* **OTP delivery is console-only by default.** Wiring `OTP_DELIVERY=email` to a
  real provider is left to deployment.
* **No CSRF tokens.** The API is token-authenticated from a separate origin with
  no cookie-based session, so the classic CSRF vector does not apply; adding
  cookie auth later would require them.
* **Transport security** (HTTPS, HSTS) is assumed to terminate at the reverse
  proxy or load balancer.


## Startup refuses an insecure production configuration

`app/main.py` aborts startup when `ENVIRONMENT` is production and
`JWT_SECRET_KEY` is still the development default shipped in `config.py`.

This is deliberate and worth stating plainly: that default is in the public
repository. A production instance running on it can be handed a token whose
payload claims `"role": "admin"`, and the signature will verify, because the
attacker holds the same key. It is a complete authentication bypass, not a
hardening gap.

An earlier version logged an error and started anyway. That is the worst of both
worlds — the deployment reports healthy, the health check passes, and the only
evidence is a line in a log nobody is reading. `tests/test_deployment_safety.py`
now fails the build if the guard is ever downgraded back to a warning.

On Render the key never has this problem: `render.yaml` declares
`JWT_SECRET_KEY` with `generateValue: true`, so the platform generates a strong
one per deployment. The guard exists for Docker, a VPS, or any deploy where
someone sets `ENVIRONMENT=production` and forgets the key.
