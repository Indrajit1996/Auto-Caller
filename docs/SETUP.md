# New Project Setup

When using this framework for a new project, update the following:

## 1. Core Configuration

```bash
# Project Identity
PROJECT_NAME="Your Project Name"
STACK_NAME=your-project-name

# Admin Access
FIRST_SUPERUSER=admin@your-domain.com
FIRST_SUPERUSER_PASSWORD=your-secure-password
```

## 2. Frontend Configuration

- Update `/api` proxy in `frontend/vite.config.js` to `http://$STACK_NAME-backend:8000`
- Update the `index.html` title in `frontend/index.html`

## 3. NGINX Configuration

- Update the upstream `backend` server in `frontend/nginx/nginx.conf` to `$STACK_NAME-backend:8000`

## 4. Service Ports Configuration

You can customize the ports for each service in the `.env` file. This is useful if you have conflicts with existing services:

```bash
# Use different ports to avoid conflicts
BACKEND_WEB_PORT_DEV=9000
FRONTEND_WEB_PORT_DEV=3000
DB_PORT_DEV=5433
MAILPIT_WEB_PORT_DEV=8026
MAILPIT_SMTP_PORT_DEV=1026
REDIS_PORT_DEV=6380
```

## 5. Redis Configuration

Configure Redis for caching and session management:

```bash
# Cache configuration
CACHE_ENABLED=True                # Set to False to disable caching
REDIS_SERVER=$STACK_NAME-redis    # Redis server hostname
REDIS_PORT=6379                   # Redis server port
REDIS_PASSWORD=your-redis-password # Set password for production
REDIS_DB=0                        # Redis database number
```

## 6. Security

```bash
# Generate new secure keys
SECRET_KEY=generate-new-secret-key
POSTGRES_PASSWORD=generate-new-db-password
```

## 7. Email Configuration

```bash
# Production email settings
SMTP_HOST=your-smtp-server
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
EMAILS_FROM_EMAIL=noreply@your-domain.com
```

## 8. IDE Configuration (VSCode)

- Download eslint and prettier plugins for your IDE
- Enable format on save in your IDE settings. `"editor.formatOnSave": true`

## Security Notes

- Generate new SECRET_KEY using `openssl rand -base64 32`
- Generate new POSTGRES_PASSWORD using `openssl rand -base64 32`
- Never commit .env file to version control
- Update all default passwords and credentials
- For production, always set a strong password for Redis if it's exposed
