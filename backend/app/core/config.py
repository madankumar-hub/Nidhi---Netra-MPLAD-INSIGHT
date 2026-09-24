"""Application configuration.

All secrets and environment-specific values are read from environment
variables (optionally via a local `.env` file). Nothing sensitive is
hardcoded in the source tree - see `.env.example` for the full list.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- General ----------------------------------------------------------
    app_name: str = "Nidhi Netra"
    environment: str = "development"
    api_v1_prefix: str = "/api"

    # --- Security ---------------------------------------------------------
    jwt_secret_key: str = Field(
        default="dev-only-insecure-secret-change-me",
        description="HMAC signing key for JWTs. MUST be overridden in production.",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 120
    refresh_token_expire_minutes: int = 60 * 24 * 7

    # --- Database ---------------------------------------------------------
    database_url: str = "sqlite:///./mplad_insight.db"

    # --- Deployment -------------------------------------------------------
    #: Most platforms (Render, Railway, Fly, Heroku) inject the listening port.
    port: int = 8000
    #: Seed the database on first boot when it is empty. Useful for a one-click
    #: cloud deploy; leave off for a real deployment with real data.
    seed_on_startup: bool = False
    seed_on_startup_projects: int = 400

    # --- CORS -------------------------------------------------------------
    #: Comma-separated. Kept as a plain string because pydantic-settings tries
    #: to JSON-decode list-typed environment variables before any validator
    #: runs, which would reject the natural `a,b` form.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # --- Seed bootstrap accounts -----------------------------------------
    seed_admin_email: str = "admin@mplad.gov.in"
    seed_admin_password: str = ""
    seed_auditor_email: str = "auditor@mplad.gov.in"
    seed_auditor_password: str = ""
    seed_officer_email: str = "officer@mplad.gov.in"
    seed_officer_password: str = ""
    seed_citizen_email: str = "citizen@example.com"
    seed_citizen_password: str = ""

    # --- Official access control -----------------------------------------
    #: Only addresses on this list, or on one of the allowed domains, may ask
    #: to be granted an official role. Comma-separated; blank disables the
    #: check and every request goes to an administrator on its merits.
    official_email_allowlist: str = ""
    official_email_domains: str = "gov.in,nic.in"
    #: When true, a request from an address that is NOT allowlisted is refused
    #: outright rather than being queued for an administrator.
    official_allowlist_enforced: bool = False

    # --- Risk engine ------------------------------------------------------
    ai_enhancement_enabled: bool = False
    ai_provider: str = "anthropic"
    ai_api_key: str = ""
    ai_model: str = "claude-sonnet-4-5"
    ai_timeout_seconds: int = 20

    duplicate_backend: str = "tfidf"
    duplicate_similarity_threshold: float = 0.72

    # --- OTP --------------------------------------------------------------
    otp_enabled: bool = True
    otp_delivery: str = "console"
    otp_expiry_minutes: int = 10

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @property
    def sqlalchemy_url(self) -> str:
        """Normalise the URL platforms hand out into one SQLAlchemy accepts.

        Managed PostgreSQL services publish `postgres://user:pass@host/db`.
        SQLAlchemy dropped the bare `postgres://` prefix, and this project uses
        psycopg 3, so both are rewritten here rather than asking every operator
        to remember the right spelling.
        """
        url = self.database_url.strip()
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://") :]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://") :]
        return url

    @property
    def official_emails(self) -> List[str]:
        return [
            item.strip().lower()
            for item in self.official_email_allowlist.split(",")
            if item.strip()
        ]

    @property
    def official_domains(self) -> List[str]:
        return [
            item.strip().lower().lstrip("@")
            for item in self.official_email_domains.split(",")
            if item.strip()
        ]

    def is_official_email(self, email: str) -> bool:
        """Does this address match the configured allowlist?

        With no list and no domains configured everything matches, and the
        decision rests entirely with the reviewing administrator.
        """
        address = (email or "").strip().lower()
        if not address:
            return False
        if not self.official_emails and not self.official_domains:
            return True
        if address in self.official_emails:
            return True
        domain = address.rpartition("@")[2]
        return any(domain == allowed or domain.endswith("." + allowed) for allowed in self.official_domains)

    @property
    def is_sqlite(self) -> bool:
        return self.sqlalchemy_url.startswith("sqlite")

    @property
    def ai_configured(self) -> bool:
        """External AI is only usable when explicitly enabled AND keyed."""
        return bool(self.ai_enhancement_enabled and self.ai_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
