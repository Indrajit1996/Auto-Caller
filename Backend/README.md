# Backend - FastAPI

## Table of Contents

- [Backend - FastAPI](#backend---fastapi)
  - [Table of Contents](#table-of-contents)
  - [Quick Start](#quick-start)
  - [Requirements](#requirements)
  - [Key Dependencies](#key-dependencies)
  - [Development Environment](#development-environment)
    - [Docker Compose (Recommended)](#docker-compose-recommended)
    - [Local Setup with uv](#local-setup-with-uv)
    - [VS Code Integration](#vs-code-integration)
  - [Project Structure](#project-structure)
  - [Working with Dependencies](#working-with-dependencies)
    - [Installing Additional Packages](#installing-additional-packages)
    - [Updating Project Dependencies](#updating-project-dependencies)
  - [Database](#database)
    - [Database Configuration](#database-configuration)
    - [Migrations](#migrations)
    - [Database CLI Commands](#database-cli-commands)
    - [Working with Migrations](#working-with-migrations)
    - [Migration Branching Strategy](#migration-branching-strategy)
    - [Working with Async vs Sync Database Sessions](#working-with-async-vs-sync-database-sessions)
      - [When to use Async Sessions:](#when-to-use-async-sessions)
      - [When to use Sync Sessions:](#when-to-use-sync-sessions)
      - [Using with Background Tasks](#using-with-background-tasks)
  - [Authentication](#authentication)
    - [Authentication Dependencies](#authentication-dependencies)
    - [User Management and Authentication Flow](#user-management-and-authentication-flow)
  - [Caching with Redis](#caching-with-redis)
  - [Background Processing](#background-processing)
    - [Background Tasks](#background-tasks)
    - [Scheduled Tasks with APScheduler](#scheduled-tasks-with-apscheduler)
  - [Data Modeling](#data-modeling)
    - [Timestamp Management and Timezone Handling](#timestamp-management-and-timezone-handling)
  - [Email System](#email-system)
    - [Email Templates](#email-templates)
  - [Testing](#testing)
    - [Running Tests](#running-tests)
    - [Test Coverage](#test-coverage)

## Quick Start

Get the backend running in minutes:

1. **Clone the repository and navigate to the backend directory**

   ```bash
   cd keystone/backend
   ```

2. **Start with Docker (recommended)**

   ```bash
   # From the project root directory
   docker compose up --watch
   ```

   This will automatically:

   - Start all required services (PostgreSQL, Redis, backend)
   - Run database migrations
   - Create a default admin user (Email: `vindrajit1996@gmail.com`, Password: `Admin@1234`)

3. **Create additional admin users (optional)**

   ```bash
   # With Docker
   docker compose exec keystone-backend kcli user create --is-superuser

   # Or locally
   kcli user create --is-superuser
   ```

   You'll be prompted to enter user details for the new admin account.

4. **Access the application**

   - API Documentation:
     - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
     - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

5. **Run tests to verify setup (optional)**

   ```bash
   docker compose exec keystone-backend bash scripts/tests-start.sh
   ```

## Requirements

- **Required:**

  - [Docker](https://www.docker.com/) - Containerization platform for running the complete stack

- **Optional (for advanced usage):**

  - [uv](https://docs.astral.sh/uv/) - Python package and environment management for local development

## Key Dependencies

The backend relies on several key packages:

- **Web Framework**

  - [FastAPI](https://fastapi.tiangolo.com/) - Modern, high-performance web framework for building APIs
  - [Pydantic](https://docs.pydantic.dev/) - Data validation and settings management using Python type annotations

- **Database**

  - [SQLModel](https://sqlmodel.tiangolo.com/) - SQL databases in Python with type annotations
  - [Alembic](https://alembic.sqlalchemy.org/) - Database migration tool for SQLAlchemy
  - [asyncpg](https://magicstack.github.io/asyncpg/) - Asynchronous PostgreSQL driver
  - [psycopg](https://www.psycopg.org/) - PostgreSQL adapter for Python

- **Authentication & Security**

  - [Passlib](https://passlib.readthedocs.io/) - Password hashing library
  - [PyJWT](https://pyjwt.readthedocs.io/) - JSON Web Token implementation

- **Task Management**

  - [APScheduler](https://apscheduler.readthedocs.io/) - Task scheduling library
  - [Tenacity](https://tenacity.readthedocs.io/) - Retrying library for Python

- **Caching**

  - [FastAPI-Cache2](https://github.com/long2ice/fastapi-cache) - Caching support for FastAPI applications

- **Email**

  - [emails](https://github.com/lavr/python-emails) - Email library for humans
  - [Jinja2](https://jinja.palletsprojects.com/) - Template engine for email templates

- **Logging & Monitoring**

  - [Loguru](https://loguru.readthedocs.io/) - Python logging made simple
  - [Sentry SDK](https://docs.sentry.io/platforms/python/) - Error tracking with Sentry

- **Testing**

  - [pytest](https://docs.pytest.org/) - Testing framework
  - [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) - Pytest support for asyncio
  - [factory-boy](https://factoryboy.readthedocs.io/) - Fixtures replacement for testing
  - [pytest-cov](https://pytest-cov.readthedocs.io/) - Coverage plugin for pytest

- **Development Tools**

  - [mypy](https://mypy.readthedocs.io/) - Static type checker
  - [ruff](https://docs.astral.sh/ruff/) - Fast Python linter and code formatter
  - [pre-commit](https://pre-commit.com/) - Framework for managing Git pre-commit hooks

## Development Environment

### Docker Compose (Recommended)

The easiest way to start the development environment is with Docker Compose:

```bash
# From the project root directory
docker compose up --watch
```

This will start all required services (PostgreSQL, Redis, backend) according to the configuration in [../README.md](../README.md).

### Local Setup with uv

If you prefer to run the backend locally without Docker:

1. Install uv if you haven't already:

   ```bash
   pip install uv
   # or with homebrew
   brew install uv
   ```

2. Create and activate a virtual environment:

   ```bash
   cd keystone/backend
   uv venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   uv sync
   ```

4. Set up environment variables (create a `.env` file with required settings)
5. Run the application:

   ```bash
   uvicorn app.main:app --reload
   ```

### VS Code Integration

The project includes VS Code configurations for:

- Running and debugging the backend through the VS Code debugger
- Running tests through the VS Code Python tests tab
- Recommended extensions and settings

To use these features, simply open the backend directory in VS Code.

## Project Structure

The project follows a structured organization:

```
backend/
├── app/
│   ├── api/
│   │   ├── keystone/       # Core system functionality
│   │   │   ├── routes/     # API endpoints for core features
│   │   │   └── utils/      # Utility functions for keystone module
│   │   └── project/        # Project-specific customizations
│   │       ├── routes/     # Project-specific API endpoints
│   │       └── utils/      # Project-specific utility functions
│   ├── core/               # Core application settings and config
│   ├── db/                 # Database connection and session management
│   ├── emails/             # Email templates and sending functionality
│   ├── migrations/         # Database migration scripts
│   │   ├── keystone/       # Core system migrations
│   │   └── project/        # Project-specific migrations
│   ├── models/             # SQLModel data models
│   ├── schemas/            # Pydantic schemas for validation
│   └── utils/              # Common utility functions
├── cli/                    # Command-line interface tools
├── data_pipeline/          # Data processing and pipeline components
└── tests/                  # Test suite
    ├── api/                # API tests
    │   ├── keystone/       # Tests for core system functionality
    │   └── project/        # Tests for project-specific functionality
    └── ...                 # Other test modules
```

This structure separates core system functionality (in the `keystone` module) from project-specific customizations (in the `project` module), allowing for cleaner code organization and easier maintenance.

## Working with Dependencies

The project dependencies are defined in the [`pyproject.toml`](/Users/shmehta/Projects/keystone/backend/pyproject.toml) file. This file contains:

- Project metadata
- Runtime dependencies in the `[project]` section
- Development dependencies in the `[tool.uv]` section
- Tool configurations for linting and typing

### Installing Additional Packages

With uv:

```bash
# Add a package
uv add package_name

# Install with extras
uv add "package_name[extra]"

# Install multiple packages
uv add package1 package2 package3
```

With Docker Compose:

```bash
docker compose exec keystone-backend uv add package_name
```

Example of adding a package and updating the pyproject.toml:

1. Add a package directly:

   ```bash
   uv add pandas
   ```

2. Or manually edit `pyproject.toml`:

   ```toml
   [project]
   # ...existing dependencies...
   dependencies = [
       # ...existing entries...
       "pandas>=2.0.0,<3.0.0",
   ]
   ```

3. Then synchronize dependencies:

   ```bash
   uv sync
   # or with Docker
   docker compose exec keystone-backend uv sync
   ```

### Updating Project Dependencies

```bash
uv upgrade
# or with Docker
docker compose exec keystone-backend uv upgrade
```

## Database

### Database Configuration

Connection settings are configured via environment variables:

```
POSTGRES_SERVER=your-database-server
POSTGRES_PORT=5432
POSTGRES_USER=your-database-user
POSTGRES_PASSWORD=your-database-password
POSTGRES_DB=your-database-name
```

### Migrations

The project uses [Alembic](https://alembic.sqlalchemy.org/) for database migrations with two separate branches:

- **keystone branch**: Core system migrations
- **project branch**: Project-specific customizations

### Database CLI Commands

The application provides a convenient CLI for database operations:

```bash
# View available db commands
kcli db --help

# Check database status and table counts
kcli db status

# View current migration information
kcli db current

# Test database connection
kcli db test

# Reset database (drops all tables and recreates schema)
kcli db reset
```

With Docker:

```bash
docker compose exec keystone-backend kcli db status
```

### Working with Migrations

Create a new migration:

```bash
# Create migration in keystone branch (default)
kcli db migrate "Description of changes"

# Create migration in project branch
kcli db migrate "Description of changes" --branch project

# Create empty migration (no auto-detection)
kcli db migrate "Empty migration" --no-autogenerate
```

Apply migrations:

```bash
# Upgrade all branches to latest
kcli db upgrade

# Upgrade only keystone branch to latest
kcli db upgrade --branch keystone

# Upgrade project branch to specific revision
kcli db upgrade abc123 --branch project

# Upgrade keystone branch by 1 revision
kcli db upgrade +1 --branch keystone
```

Downgrade migrations:

```bash
# Downgrade keystone branch by 1 revision
kcli db downgrade --branch keystone

# Downgrade project branch to specific revision
kcli db downgrade abc123 --branch project

# Downgrade keystone branch by 2 revisions
kcli db downgrade -2 --branch keystone

# Downgrade project branch to base (remove all migrations)
kcli db downgrade base --branch project
```

View migration information:

```bash
# Show current migration status for all branches
kcli db current

# Show information about a specific revision
kcli db show abc123

# Show information about a branch
kcli db show keystone
```

### Migration Branching Strategy

The application uses a multi-branch migration strategy:

1. **keystone branch**: Contains core system migrations that should not be modified by customizations
2. **project branch**: Contains project-specific migrations for customizations

This approach allows for:

- Clean separation between core features and customizations
- Independent evolution of core system and project-specific features
- Easier upgrades of the core system without breaking customizations

The migrations are stored in separate directories:

- `app/alembic/versions/keystone/` - Core system migrations
- `app/alembic/versions/project/` - Project-specific migrations

### Working with Async vs Sync Database Sessions

The application supports both synchronous and asynchronous database sessions:

- **Async Sessions (AsyncSessionDep)**: Use in API routes, background tasks, and other asynchronous contexts
- **Sync Sessions (SessionDep)**: Use in CLI commands, scripts and other synchronous contexts

#### When to use Async Sessions:

- API endpoints and other web request handlers
- Background tasks in FastAPI (including those added with `BackgroundTasks`)
- Scheduled jobs with APScheduler that run within the FastAPI application
- Any code that is part of the FastAPI async runtime

```python
from app.api.deps import AsyncSessionDep

@router.get("/items/")
async def get_items(session: AsyncSessionDep):
    items = (await session.exec(select(Item))).all()
    return items
```

#### When to use Sync Sessions:

- CLI commands and standalone scripts
- External processes outside the FastAPI application
- Any context where you're not in an async function or event loop

```python
from app.api.deps import SessionDep

# In a CLI command
def process_items(session: SessionDep):
    items = session.exec(select(Item)).all()
    for item in items:
        # Process each item
        process_item(item)
```

#### Using with Background Tasks

For background tasks, use the asynchronous session:

```python
from fastapi import BackgroundTasks
from app.utils.decorators import with_async_db_session

@router.post("/items/")
async def create_item(
    item_data: ItemCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSessionDep
):
    # Create the item (in async context)
    item = Item.model_validate(item_data)
    session.add(item)
    await session.commit()
    await session.refresh(item)

    # Add background task with async session
    background_tasks.add_task(process_item_data, item.id)
    return {"id": item.id, "status": "processing"}

@with_async_db_session  # Uses async session
async def process_item_data(item_id: int, session: AsyncSession = None):
    # Process with async session
    item = await session.get(Item, item_id)
    if not item:
        return

    # Process the item
    item.status = "processed"
    session.add(item)
    await session.commit()
```

## Authentication

### Authentication Dependencies

Use these dependencies for authenticated endpoints:

```python
from app.api.deps import CurrentUser, IsSuperUser, Authenticated

# Endpoint requiring any authenticated user
@router.get("/me/", dependencies=[Authenticated])
async def read_users_me(current_user: CurrentUser):
    return current_user

# Endpoint requiring superuser privileges
@router.post("/admin-only/", dependencies=[IsSuperUser])
async def admin_only_operation(current_user: CurrentUser):
    return {"message": "Admin operation successful"}
```

### User Management and Authentication Flow

The system supports multiple approval flows for new users:

1. Email Verification: Users must verify their email before accessing the system
2. Admin Approval: An administrator must approve new user registrations

This is controlled by the `DEFAULT_USER_APPROVAL_FLOW` setting.

## Caching with Redis

Enable Redis caching by setting:

```
CACHE_ENABLED=True
REDIS_SERVER=your-redis-server
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password (optional)
REDIS_DB=0 (default)
```

Using the cache:

```python
from fastapi_cache.decorator import cache

@router.get("/items/{item_id}")
@cache(expire=300)  # Cache for 5 minutes
async def get_item(item_id: int, session: AsyncSessionDep):
    return await session.get(Item, item_id)
```

## Background Processing

### Background Tasks

For tasks that need to run after a response:

```python
from fastapi import BackgroundTasks
from app.utils.decorators import with_async_db_session  # Use async session for background tasks

@router.post("/items/")
async def create_item(
    item_data: ItemCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSessionDep
):
    # Create the item
    item = Item.model_validate(item_data)
    session.add(item)
    await session.commit()
    await session.refresh(item)

    # Add background task using async session
    background_tasks.add_task(process_item_data, item.id)
    return {"id": item.id, "status": "processing"}

@with_async_db_session  # Uses async session
async def process_item_data(item_id: int, session: AsyncSession = None):
    # Fresh session is automatically created by the decorator
    item = await session.get(Item, item_id)
    if not item:
        return

    # Process the item
    item.status = "processed"
    session.add(item)
    await session.commit()
```

### Scheduled Tasks with APScheduler

The application uses APScheduler for periodic tasks that run within the FastAPI application:

```python
# In app/jobs/example_job.py
@with_async_db_session  # Uses async session for scheduled jobs
async def example_job(session: AsyncSession = None):
    """Run daily maintenance tasks"""
    # Perform scheduled operations using async session
    items = (await session.exec(select(Item).where(Item.status == "pending"))).all()
    for item in items:
        # Process items
        item.status = "processed"
        session.add(item)

    await session.commit()
```

Common trigger patterns:

```python
# Daily at midnight
scheduler.add_job(example_job, trigger=CronTrigger(hour=0, minute=0))

# Every Monday at 9 AM
scheduler.add_job(example_job, trigger=CronTrigger(day_of_week="mon", hour=9))

# Every 30 minutes
scheduler.add_job(example_job, trigger=IntervalTrigger(minutes=30))
```

## Data Modeling

### Timestamp Management and Timezone Handling

Use the `TimestampMixin` to add created/updated timestamps to models:

```python
from app.models.mixins.timestamp_mixin import TimestampMixin

class MyModel(SQLModel, TimestampMixin, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str
    # Other fields...
```

The application uses UTC timestamps throughout for consistency.

## Email System

### Email Templates

The project uses [MJML](https://mjml.io/) for responsive email templates:

1. Email templates are located in `./backend/app/emails/templates`
2. Source files are in `src/` and compiled templates in `build/`
3. Install the [MJML extension](https://marketplace.visualstudio.com/items?itemName=attilabuti.vscode-mjml) for VS Code
4. Create new templates in the `src/` directory
5. Use VS Code command palette (`Ctrl+Shift+P`) and search for `MJML: Export to HTML`
6. Save the generated HTML in the `build/` directory

## Testing

### Running Tests

Run tests with:

```bash
# With Docker (recommended)
docker compose exec keystone-backend bash scripts/tests-start.sh

# Locally
bash ./scripts/test.sh
```

Pass additional arguments to pytest:

```bash
# Stop on first error
docker compose exec keystone-backend bash scripts/tests-start.sh -x
```

### Test Coverage

After running tests, view coverage report at `coverage/index.html`.
