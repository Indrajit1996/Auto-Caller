# Production Environment Setup

1. Change app environment to production in `.env`:

```bash
ENVIRONMENT=production
```

2. Update the `FRONTEND_HOST` environment variable in `.env`:

```bash
FRONTEND_HOST=https://your-frontend-domain.com
```

- Add your frontend domain to the CORS origins in the `.env` file:

```bash
BACKEND_CORS_ORIGINS="http://your-frontend-domain.com,https://your-frontend-domain.com"
```

3. Security

- Check security notes in the [Project Setup Guide](./SETUP.md) for generating new secure keys.

```bash
# Generate new secure keys
SECRET_KEY=generate-new-secret-key
POSTGRES_PASSWORD=generate-new-db-password
```

4. Redis Configuration

For production, it's important to secure your Redis instance:

```bash
# Redis production configuration
CACHE_ENABLED=True
REDIS_SERVER=$STACK_NAME-redis
REDIS_PORT=6379
REDIS_PASSWORD=your-secure-redis-password  # Always set a strong password in production
REDIS_DB=0
```

5. Email Configuration

```bash
SMTP_HOST=your-smtp-server
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
EMAILS_FROM_EMAIL=noreply@your-domain.com
SMTP_TLS=True  # Enable TLS for production
SMTP_SSL=False
SMTP_PORT=587  # Common TLS port for SMTP
```

6. Build and deploy using Docker Compose:

```bash
# Build and start all services with production configuration
docker compose -f compose.yml -f compose.prod.yml up -d
```

7. Service Ports in Production

In production, you might want to use different ports than in development:

```bash
# Production ports
FRONTEND_WEB_PORT_SERVER=80      # Standard HTTP port
BACKEND_WEB_PORT_SERVER=8000     # API port, typically behind a reverse proxy
```

Remember that in production, you should always:

- Use HTTPS for all public-facing services
- Set strong passwords for all services
- Configure proper logging and monitoring
- Set up automated backups for the database
- Use a reliable email service provider
