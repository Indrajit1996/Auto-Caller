from app.core.config import Config


def test_config_defaults():
    """Test that default config values are set correctly."""
    config = Config()  # type: ignore[no-redef]
    assert config.PROJECT_NAME == "Keystone"
    assert config.API_ROOT_URL == "/api"
    assert config.ENVIRONMENT in ["local", "staging", "production", "testing"]


def test_sqlalchemy_uri_computation():
    """Test that database URI is computed correctly."""
    config = Config(
        POSTGRES_SERVER="localhost",
        POSTGRES_USER="user",
        POSTGRES_PASSWORD="pass",
        POSTGRES_DB="db",
        POSTGRES_PORT=5432,
    )  # type: ignore[no-redef]

    # Check the regular URI
    assert "postgresql+psycopg" in config.SQLALCHEMY_DATABASE_URI
    assert "user:pass@localhost:5432/db" in config.SQLALCHEMY_DATABASE_URI

    # Check the async URI
    assert "postgresql+asyncpg" in config.SQLALCHEMY_DATABASE_URI_ASYNC
    assert "user:pass@localhost:5432/db" in config.SQLALCHEMY_DATABASE_URI_ASYNC


def test_frontend_url_computation():
    """Test that frontend URLs are computed correctly."""
    # Test local environment
    local_config = Config(
        ENVIRONMENT="local",
        APP_DOMAIN="localhost",
        FRONTEND_WEB_PORT_DEV=3000,
    )  # type: ignore[no-redef]
    assert local_config.FRONTEND_HOST == "http://localhost:3000"

    # Test production environment
    prod_config = Config(
        ENVIRONMENT="production",
        APP_DOMAIN="example.com",
    )  # type: ignore[no-redef]
    assert prod_config.FRONTEND_HOST == "https://example.com"


def test_cors_origins_parsing():
    """Test that CORS origins are parsed correctly."""
    # Test CSV string
    config = Config(BACKEND_CORS_ORIGINS="http://localhost:3000,https://example.com")  # type: ignore[no-redef]
    assert "http://localhost:3000" in config.all_cors_origins
    assert "https://example.com" in config.all_cors_origins

    # Test list of URLs
    config = Config(
        BACKEND_CORS_ORIGINS=["http://localhost:3000", "https://example.com"]
    )  # type: ignore[no-redef]
    assert "http://localhost:3000" in config.all_cors_origins
    assert "https://example.com" in config.all_cors_origins
