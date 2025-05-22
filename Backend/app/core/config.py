import os
import secrets
import warnings
from enum import Enum
from typing import Annotated, Any, Literal

from dotenv import find_dotenv, load_dotenv
from pydantic import (
    AnyUrl,
    BeforeValidator,
    HttpUrl,
    computed_field,
    model_validator,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

# Load base environment variables from .env file
load_dotenv(find_dotenv(), override=False)

# Check for .env.local and override if it exists
env_local_path = find_dotenv(".env.local")
if os.path.isfile(env_local_path):
    load_dotenv(env_local_path, override=True)


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class USER_APPROVAL_FLOW(Enum):
    EMAIL_VERIFICATION = "pending_email_verification"
    ADMIN_APPROVAL = "pending_admin_approval"


class Config(BaseSettings):
    """Application configuration settings."""

    model_config = SettingsConfigDict(
        env_ignore_empty=True,
        extra="ignore",
    )

    # ==== Application Core ====
    PROJECT_NAME: str = "Keystone"
    ENVIRONMENT: Literal["local", "staging", "production", "testing"] = "local"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    LOG_LEVEL: Literal[
        "TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"
    ] = "INFO"
    API_TIMEOUT_IN_SECONDS: int = 30
    ENABLE_FILE_LOGGING: bool = True

    # ==== Authentication ====
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    DEFAULT_USER_APPROVAL_FLOW: USER_APPROVAL_FLOW = (
        USER_APPROVAL_FLOW.EMAIL_VERIFICATION
    )
    PASSWORD_RESET_TOKEN_EXPIRY_IN_HOURS: int = 24
    INVITATION_EXPIRY_IN_HOURS: int = 24

    # ==== Server Settings ====
    API_ROOT_URL: str = "/api"
    WORKER_GRACEFUL_SHUTDOWN_TIMEOUT_IN_SECONDS: int = 30

    # ==== Frontend Integration ====
    APP_DOMAIN: str = "localhost"
    FRONTEND_WEB_PORT_DEV: int = 5173
    FRONTEND_WEB_PORT_SERVER: int = 80

    # ==== Database ====
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    # ==== Cache ====
    CACHE_ENABLED: bool = False
    REDIS_SERVER: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # ==== Email ====
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = None
    EMAILS_FROM_NAME: str | None = None
    EMAIL_TEST_USER: str = "test@example.com"

    # ==== Monitoring ====
    SENTRY_DSN: HttpUrl | None = None
    SENTRY_ENVIRONMENT: str | None = None
    SENTRY_RELEASE: str | None = None

    # ==== CORS ====
    # BACKEND_CORS_ORIGINS: Annotated[
    #     list[AnyUrl] | str, BeforeValidator(parse_cors)
    # ] = []
    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = ["http://localhost:5173"]


    # ==== Computed Properties ====
    @property
    def is_local(self) -> bool:
        """Check if running in local environment."""
        return self.ENVIRONMENT == "local"

    @computed_field
    @property
    def FRONTEND_WEB_PORT(self) -> int:
        return (
            self.FRONTEND_WEB_PORT_DEV
            if self.is_local
            else self.FRONTEND_WEB_PORT_SERVER
        )

    @computed_field
    @property
    def FRONTEND_HOST(self) -> str:
        if self.is_local:
            return f"http://{self.APP_DOMAIN}:{self.FRONTEND_WEB_PORT}"
        return f"https://{self.APP_DOMAIN}"

    @computed_field
    @property
    def all_cors_origins(self) -> list[str]:
        origins = [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS]
        origins.append(f"http://{self.APP_DOMAIN}:{self.FRONTEND_WEB_PORT}")
        if not self.is_local:
            origins.append(f"https://{self.APP_DOMAIN}")
        return [o for o in origins if o]

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return str(
            MultiHostUrl.build(
                scheme="postgresql+psycopg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        )

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI_ASYNC(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_SERVER}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @computed_field
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    # ==== Validators ====
    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        return self

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.is_local:
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)


config = Config()  # type: ignore[no-redef]
