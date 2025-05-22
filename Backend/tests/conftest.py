from collections.abc import Generator
from datetime import timedelta
from unittest.mock import Mock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import Session
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import config
from app.core.db import SessionLocal
from app.models.user import User, UserStatus
from cli.db_commands.commands import _reset_db
from data_pipeline.seeders.user_seeder import UserFactory, pwd_context

# Test-specific overrides
config.SECRET_KEY = "test_secret_key"
config.CACHE_ENABLED = False
config.EMAILS_FROM_EMAIL = "test@example.com"

# ------------------------------------------------------------------------------
# DATABASE FIXTURES
# ------------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def override_db_session():
    """Override the async database session for testing."""
    # Create a test async engine with NullPool
    test_async_engine = create_async_engine(
        config.SQLALCHEMY_DATABASE_URI_ASYNC,
        poolclass=NullPool,
    )

    # Create a new AsyncSessionLocal with our test engine
    test_async_session_local = async_sessionmaker(
        bind=test_async_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    # Patch the AsyncSessionLocal in app.core.db
    with patch("app.core.db.AsyncSessionLocal", test_async_session_local):
        with patch("app.api.deps.AsyncSessionLocal", test_async_session_local):
            yield


@pytest.fixture(scope="session", autouse=True)
def prepare_db():
    """Prepare database by creating all tables."""
    _reset_db()
    yield


@pytest.fixture(scope="session")
def session_db() -> Generator[Session, None, None]:
    """Create a database session for session-scoped fixtures."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_db() -> Generator[Session, None, None]:
    """Create a new database session for a test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ------------------------------------------------------------------------------
# USER FIXTURES
# ------------------------------------------------------------------------------


@pytest.fixture(scope="function")
def test_superuser(test_db: Session) -> User:
    """Create a superuser for testing."""
    user = UserFactory.build(
        status=UserStatus.ACTIVE,
        hashed_password=pwd_context.hash("admin"),
        is_superuser=True,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_normal_user(test_db: Session) -> User:
    """Create a normal user for testing."""
    user = UserFactory.build(
        status=UserStatus.ACTIVE,
        hashed_password=pwd_context.hash("password"),
        is_superuser=False,
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="module")
def module_superuser(session_db: Session) -> User:
    """Create a superuser for testing."""
    user = UserFactory.build(
        status=UserStatus.ACTIVE,
        hashed_password=pwd_context.hash("admin"),
        is_superuser=True,
    )
    session_db.add(user)
    session_db.commit()
    session_db.refresh(user)
    return user


@pytest.fixture(scope="module")
def module_normal_user(session_db: Session) -> User:
    """Create a normal user for testing."""
    user = UserFactory.build(
        status=UserStatus.ACTIVE,
        hashed_password=pwd_context.hash("password"),
        is_superuser=False,
    )
    session_db.add(user)
    session_db.commit()
    session_db.refresh(user)
    return user


# ------------------------------------------------------------------------------
# APP AND CLIENT FIXTURES
# ------------------------------------------------------------------------------


@pytest.fixture(scope="session")
def test_app():
    """Create a FastAPI app for testing."""
    from starlette.routing import _DefaultLifespan

    from app.main import app

    app.router.lifespan_context = _DefaultLifespan(app.router)
    return app


@pytest.fixture(scope="module")
def client(test_app):
    """Create a test client with overridden dependencies."""
    with TestClient(test_app) as client:
        yield client


def get_authorized_client(user_id: UUID, client: TestClient) -> TestClient:
    """Create an authenticated test client with a user token."""
    from app.core.config import config
    from app.core.security import create_access_token

    expiry = timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        user_id,
        expires_delta=expiry,
    )
    headers = {"Authorization": f"Bearer {token}"}
    client.headers.update(headers)
    return client


@pytest.fixture(scope="function")
def unauthorized_client(client: TestClient) -> TestClient:
    """Create an unauthenticated test client."""
    # Clear any existing headers
    client.headers.clear()
    return client


@pytest.fixture(scope="function")
def authorized_client(client: TestClient, test_normal_user):
    """Create an authenticated test client with a normal user token."""
    return get_authorized_client(test_normal_user.id, client)


@pytest.fixture(scope="function")
def superuser_client(client: TestClient, test_superuser):
    """Create an authenticated test client with a superuser token."""
    return get_authorized_client(test_superuser.id, client)


@pytest.fixture(scope="module")
def module_authorized_client(client: TestClient, module_normal_user):
    """Create an authenticated test client with a normal user token."""
    return get_authorized_client(module_normal_user.id, client)


@pytest.fixture(scope="module")
def module_superuser_client(client: TestClient, module_superuser):
    """Create an authenticated test client with a superuser token."""
    return get_authorized_client(module_superuser.id, client)


# ------------------------------------------------------------------------------
# UTILITY FIXTURES
# ------------------------------------------------------------------------------


@pytest.fixture(scope="function")
def mock_send_email():
    """Mock the email sending functionality."""
    mock = Mock()
    patches = [
        patch("app.emails.utils.send_email", mock),
        patch("app.api.keystone.utils.auth.send_email", mock),
        patch("app.api.keystone.routes.auth.send_email", mock),
        patch("app.api.keystone.utils.invitation.send_email", mock),
        patch("app.api.keystone.routes.utils.send_email", mock),
    ]

    for patcher in patches:
        patcher.start()

    yield mock

    for patcher in patches:
        patcher.stop()
