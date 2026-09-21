"""MPLAD Insight - FastAPI application entry point.

AI-Powered Anomaly, Fraud & Inefficiency Detection System for the MPLAD
Scheme (SIH 2026, problem statement SIH26102).
"""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.exceptions import AppError
from app.database.init_db import init_database
from app.routers import (
    admin_access,
    admin_analytics,
    admin_projects,
    admin_risk,
    admin_workflow,
    auth,
    public_projects,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
#: The development fallback in `config.py`. Named here so the startup guard and
#: its test both refer to the same string rather than repeating a literal.
INSECURE_DEFAULT_SECRET = "dev-only-insecure-secret-change-me"

logger = logging.getLogger("mplad")

DESCRIPTION = """
Transparency and oversight platform for the MPLAD Scheme.

**Two clearly separated surfaces**

* `/api/auth/*` - authentication (citizen email+OTP signup, official credentials)
* `/api/projects/*` - **Citizen portal.** Public-safe project data only:
  funds, progress, timeline, agency and a simplified public indicator.
* `/api/admin/*` - **Officials only.** Risk scores and factors, mitigation
  tracking, reviews, internal notes and the audit trail. The Citizen role is
  rejected with HTTP 403 on every route in this group, regardless of what the
  client sends.

**On the risk engine.** Scores and levels are produced by a deterministic
rule-based layer plus a statistical peer-comparison layer, both of which run
with no external service. An optional external-AI layer can add a narrative
over findings that have already been computed; it never sets the score. All
findings are indicators flagged for investigation, never assertions of fraud.
"""

def _seed_if_empty() -> None:
    """One-click cloud deploys start with an empty database. When
    SEED_ON_STARTUP is set, populate it once so the site is not blank."""
    from sqlalchemy import func, select

    from app.database.session import SessionLocal
    from app.models.project import Project

    db = SessionLocal()
    try:
        existing = int(db.execute(select(func.count()).select_from(Project)).scalar_one())
        if existing:
            logger.info("Database already holds %d project(s); skipping the seed.", existing)
            return
    finally:
        db.close()

    logger.info("Empty database detected - seeding %d works.", settings.seed_on_startup_projects)
    from seed.seed_data import run_seed

    run_seed(projects=settings.seed_on_startup_projects, reset=False)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_database()
    if settings.seed_on_startup:
        try:
            _seed_if_empty()
        except Exception:  # pragma: no cover - never block startup on seeding
            logger.exception("Seeding on startup failed; the API will start empty.")
    logger.info("%s started (environment=%s)", settings.app_name, settings.environment)

    # A production deployment running on the development signing key is not a
    # warning, it is a total authentication bypass: the default is in this
    # repository, so anyone who can read the source can mint a token claiming
    # `"role": "admin"` and it will verify. Logging an error and starting anyway
    # meant the deployment looked healthy while being wide open - a log line
    # nobody reads is not a control. Refuse to start instead.
    if settings.is_production and settings.jwt_secret_key == INSECURE_DEFAULT_SECRET:
        raise RuntimeError(
            "JWT_SECRET_KEY is still the development default while ENVIRONMENT is "
            "production. Anyone reading this repository could forge an administrator "
            "token. Set JWT_SECRET_KEY to a strong random value and restart:\n"
            '  python -c "import secrets; print(secrets.token_urlsafe(48))"'
        )
    yield


app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
    description=DESCRIPTION,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)


@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Response-Time-ms"] = f"{(time.perf_counter() - started) * 1000:.1f}"
    return response


# ---------------------------------------------------------------------------
# Uniform error envelope: { code, message, detail }
# ---------------------------------------------------------------------------
@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message, "detail": None},
    )


@app.exception_handler(StarletteHTTPException)
async def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    codes = {401: "unauthenticated", 403: "forbidden", 404: "not_found", 405: "method_not_allowed"}
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": codes.get(exc.status_code, "http_error"),
            "message": str(exc.detail),
            "detail": None,
        },
    )


#: Field names as a citizen sees them on the form, not as the schema spells them.
FIELD_LABELS = {
    "email": "Email address",
    "full_name": "Full name",
    "password": "Password",
    "otp": "Verification code",
    "justification": "Reason for access",
    "requested_role": "Requested role",
    "employee_id": "Employee ID",
}

#: Pydantic/email-validator messages are accurate but unreadable on a form.
MESSAGE_OVERRIDES = (
    ("value is not a valid email address", "must be a valid email address, for example name@example.com"),
    ("field required", "is required"),
    ("Field required", "is required"),
)


def humanize_validation_error(error: dict) -> str:
    """Turn one pydantic error into a sentence a citizen can act on."""
    raw_field = ".".join(str(part) for part in error.get("loc", [])[1:])
    label = FIELD_LABELS.get(raw_field, raw_field.replace("_", " ").capitalize() or "Request")
    message = str(error.get("msg", "is invalid"))
    for needle, replacement in MESSAGE_OVERRIDES:
        if needle in message:
            message = replacement
            break
    else:
        message = message[0].lower() + message[1:] if message else "is invalid"
    return f"{label} {message}."


@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    first = errors[0] if errors else {}
    return JSONResponse(
        status_code=422,
        content={
            "code": "validation_error",
            "message": humanize_validation_error(first),
            "detail": None if settings.is_production else str(errors),
        },
    )


@app.exception_handler(Exception)
async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:  # pragma: no cover
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "code": "server_error",
            "message": "An unexpected error occurred. Please try again.",
            "detail": None if settings.is_production else str(exc),
        },
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
prefix = settings.api_v1_prefix
app.include_router(auth.router, prefix=prefix)
app.include_router(public_projects.router, prefix=prefix)
app.include_router(admin_projects.router, prefix=prefix)
app.include_router(admin_risk.router, prefix=prefix)
app.include_router(admin_workflow.router, prefix=prefix)
app.include_router(admin_analytics.router, prefix=prefix)
app.include_router(admin_access.router, prefix=prefix)


@app.get("/", tags=["System"])
def root() -> dict:
    return {
        "name": settings.app_name,
        "problem_statement": "SIH26102",
        "version": "1.0.0",
        "docs": "/docs",
        "api_prefix": prefix,
    }


@app.get(f"{prefix}/health", tags=["System"])
def health() -> dict:
    from sqlalchemy import text

    from app.database.session import engine

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_ok = True
    except Exception:  # pragma: no cover - reported, not raised
        database_ok = False
    return {
        "status": "ok" if database_ok else "degraded",
        "database": "connected" if database_ok else "unavailable",
        "environment": settings.environment,
    }
