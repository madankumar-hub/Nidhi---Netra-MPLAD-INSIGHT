# Architecture

MPLAD Insight follows the layered (N-tier) structure inside a modular monolith
recommended by the SRS (§3), with the risk engine kept as a cleanly decoupled
internal module.

```
        [ Citizen Portal UI ]        [ Officials' Portal UI ]
                 \                            /
                  \                          /
              [ FastAPI gateway + RBAC middleware ]
                             |
             ----------------------------------
             |                                |
     [ Core CRUD services ]          [ Risk engine ]
             |                                |
             ----------------------------------
                             |
                      [ PostgreSQL ]
```

## Why a modular monolith

Microservices would add orchestration overhead that a hackathon timeline cannot
absorb and that a live demo does not reward. The layer boundaries here are strict
enough to give the same design discipline: the risk engine has **no database
imports at runtime** (it takes plain objects), the services layer holds all
business rules, and the routers do nothing but validate, authorise and delegate.
That makes `app/risk/` and the ingestion path extractable into their own services
later without touching the API layer.

Concretely, `app/risk/*` imports `Project` only under `typing.TYPE_CHECKING`, so
the whole engine can be imported, unit-tested and run with no database, no web
framework and no ORM present — which is exactly how `tests/test_risk_engine.py`
exercises it.

## Backend module map

```
backend/app/
├── main.py                 FastAPI app, error envelope, CORS, lifespan
├── core/
│   ├── config.py           Pydantic settings, all secrets from the environment
│   ├── security.py         Password hashing (bcrypt), JWT issue/verify (PyJWT)
│   ├── deps.py             DB session, current user, role guards
│   ├── enums.py            Domain vocabulary (no ORM dependency)
│   └── exceptions.py       Typed errors mapped to HTTP status codes
├── auth/
│   ├── rbac.py             Role allow-lists
│   └── otp.py              Lightweight email OTP for citizen signup (FR1)
├── database/
│   ├── base.py             Declarative base, timestamp mixin
│   ├── session.py          Engine and session factory (Postgres or SQLite)
│   └── init_db.py          Schema creation / drop
├── models/                 SQLAlchemy 2.0 typed models
├── schemas/                Pydantic request/response contracts
├── routers/
│   ├── auth.py             /api/auth/*
│   ├── public_projects.py  /api/projects/*        (citizen-safe only)
│   ├── admin_projects.py   /api/admin/projects/*
│   ├── admin_risk.py       /api/admin/.../risk, mitigation
│   ├── admin_workflow.py   reviews, notes, activity, citizen-report triage
│   └── admin_analytics.py  dashboard, analytics, delayed, pending review
├── services/               Business logic; routers stay thin
├── risk/                   The engine (see below)
└── utils/
```

### The risk engine

```
backend/app/risk/
├── types.py                FactorResult, ProjectMetrics, CohortStats, RiskResult
├── metrics.py              Pure arithmetic over one project record
├── rules.py                Deterministic threshold rules (layer 1)
├── statistical.py          Peer-cohort z-score outliers (layer 2)
├── duplicate.py            TF-IDF near-duplicate detection (layer 2)
├── ai_provider.py          Optional external narrative (layer 3)
├── mitigation_templates.py Standard action per detected indicator
└── engine.py               Orchestration, aggregation, level assignment
```

Aggregation is weighted with diminishing returns: contributions are sorted
descending and each successive factor is discounted by `1 / (1 + 0.30 · index)`.
Without it, five trivial findings would outrank one severe one.

Level thresholds: `< 25` LOW, `< 50` MEDIUM, `< 75` HIGH, `>= 75` CRITICAL.

## Frontend module map

```
frontend/src/
├── api/                    One module per API surface, all through client.ts
├── components/
│   ├── ui/                 Button, Card, Badge, Field, Table, Tabs, Modal, …
│   ├── layout/             Government identity bar, page header, emblem
│   └── charts/             Recharts wrappers with empty/table views
├── features/
│   ├── auth/               AuthContext, ProtectedRoute
│   ├── citizen/            Project card, filters, report dialog
│   ├── admin/              Admin table, panels, dialogs, activity timeline
│   ├── risk/               RiskPanel, MitigationPanel
│   ├── reviews/            ReviewPanel
│   └── notes/              NotesPanel
├── hooks/                  useApi, useMutation, useDebounce
├── i18n/                   English + Hindi dictionaries and provider
├── layouts/                PublicLayout, AdminLayout
├── pages/                  One file per route; admin pages under pages/admin
├── routes/                 Route table
├── types/                  Mirrors the backend schemas
└── utils/                  Formatting, constants, chart palette
```

`App.tsx` contains only the provider stack and the router — no page logic.

## Request lifecycle

1. The browser sends a request with `Authorization: Bearer <access token>`.
2. `get_current_user` decodes the JWT, then **loads the user row** and checks
   `is_active`. The `role` claim is not trusted.
3. A role guard (`require_internal` / `require_reviewer` / `require_elevated` /
   `require_admin`) runs for every `/api/admin/*` route.
4. The router validates the body against a Pydantic schema and calls a service.
5. The service performs the work, writes an `ActivityLog` row for anything
   auditable, and commits.
6. The response is serialised through a schema that determines exactly which
   fields leave the server — this is where field-level masking for the Citizen
   role is enforced (`ProjectPublicSummary` simply has no risk fields).

## Separation of citizen and admin surfaces

The SRS (FR7b) asks for a genuinely separate administrative detail page rather
than one component with conditional sections. That is what is implemented:

| | Citizen | Officials |
|---|---|---|
| Route | `/scheme/:id` | `/admin/scheme/:id` |
| Component | `pages/SchemeDetailPage.tsx` | `pages/admin/AdminSchemeDetailPage.tsx` |
| API | `GET /api/projects/{id}` | `GET /api/admin/projects/{id}` |
| Risk | public indicator only | score, factors, evidence, history |

The citizen endpoint does not read risk factors, notes, reviews, mitigation or
the activity log at all, so there is no code path by which they could leak.
