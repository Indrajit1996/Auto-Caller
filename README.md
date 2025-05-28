# Keystone

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/) [![React](https://img.shields.io/badge/React-blue?style=flat&logo=react)](https://reactjs.org/) [![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)

Full-stack web application with FastAPI backend and React frontend.

📚 **Documentation:** [Setup Guide](docs/SETUP.md) | [Production Setup](docs/PRODUCTION.md) | [Frontend Development](frontend/README.md) | [Backend Development](backend/README.md)

## Table of Contents

- [Keystone](#keystone)
  - [Table of Contents](#table-of-contents)
  - [Quick Start](#quick-start)
  - [Development Setup](#development-setup)
    - [Prerequisites](#prerequisites)
    - [Environment Setup](#environment-setup)
    - [Screen Layout Configuration](#screen-layout-configuration)
    - [Service Ports Configuration](#service-ports-configuration)
    - [Redis Configuration](#redis-configuration)
    - [Docker Compose Configuration](#docker-compose-configuration)

## Quick Start

```bash
git clone https://github.com/DTNetwork/keystone.git
cd keystone
cp .env.example .env
docker compose up --watch
```

Access services:

- Frontend: [http://localhost:5173](http://localhost:5173)
- API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Mail UI: [http://localhost:8025](http://localhost:8025)

Default logins:

- Admin user: admin@dtn.asu.edu / Admin@1234
- Regular user: user@dtn.asu.edu / User@1234

## Development Setup

### Prerequisites

- Docker and Docker Compose

If not using Docker, you will need the following:

- Node.js 22+ (for local frontend development) - [Download Node.js](https://nodejs.org/en/download/)
- Python 3.10+ (for local backend development) - [Download Python](https://www.python.org/downloads/)

### Environment Setup

1. Copy environment configuration:

```bash
cp .env.example .env
```

### Screen Layout Configuration

Set the following environment variable to enable seven-screen layout:

```text
VITE_SEVEN_SCREEN_DASHBOARD_LAYOUT_ENABLED=true
```

### Service Ports Configuration

You can customize the ports for each service in the `.env` file. This is useful if you have conflicts with existing services on your machine or need specific port assignments:

| Service     | Environment Variable  | Default Port |
| ----------- | --------------------- | ------------ |
| Backend     | BACKEND_WEB_PORT_DEV  | 8000         |
| Frontend    | FRONTEND_WEB_PORT_DEV | 5173         |
| Database    | DB_PORT_DEV           | 5432         |
| Mail Server | MAILPIT_WEB_PORT_DEV  | 8025         |
| Mail SMTP   | MAILPIT_SMTP_PORT_DEV | 1025         |
| Redis       | REDIS_PORT_DEV        | 6379         |

Example of changing ports in your `.env` file:

```bash
# Use different ports to avoid conflicts
BACKEND_WEB_PORT_DEV=9000
FRONTEND_WEB_PORT_DEV=3000
DB_PORT_DEV=5433
```

### Redis Configuration

The application uses Redis for caching and session management. Redis configuration can be customized in the `.env` file:

```bash
# Cache configuration
CACHE_ENABLED=True              # Set to False to disable caching
REDIS_SERVER=keystone-redis     # Redis server hostname
REDIS_PORT=6379                 # Redis server port
REDIS_PASSWORD=                 # Redis password (leave empty for no password)
REDIS_DB=0                      # Redis database number
```

For more detailed information about Redis configuration and usage, refer to the [Backend Development documentation](backend/README.md).

### Docker Compose Configuration

The project uses multiple Docker Compose files for different environments:

- `compose.yml` - Base configuration shared across all environments
- `compose.override.yml` - Development environment overrides (applied automatically when running `docker compose up`)
- `compose.prod.yml` - Production environment configuration

For development, simply run:

```bash
docker compose up --watch
```

For production deployment, use:

```bash
docker compose -f compose.yml -f compose.prod.yml up -d
```
