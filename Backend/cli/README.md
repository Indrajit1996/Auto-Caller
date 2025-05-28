# Keystone CLI (kcli)

Command-line interface for the Keystone application.

## Quick Start

When running in Docker:

```bash
# Format
docker exec keystone-backend kcli [command]

# Examples
docker exec keystone-backend kcli db status
docker exec keystone-backend kcli server run --reload
```

On local development environment:

```bash
python -m cli [command]
# or
kcli [command]
```

## Available Command Groups

- **db**: Database management and migrations
- **data**: Data pipelines, imports, and seeding
- **server**: Server configuration and runtime management
- **user**: User and permission management

## Common Uses

### Database Operations

```bash
# Check database status
kcli db status

# Reset database and seed with data
kcli db reset --seed

# Create and run migrations
kcli db migrate "add new column"
kcli db upgrade
```

### Data Management

```bash
# Run importers
kcli data import csv_importer --file data/users.csv

# Seed specific data
kcli data seed user_seeder --count 50

# Run entire data pipeline
kcli data run-pipeline
```

### Server Operations

```bash
# Start the server
kcli server run --reload

# View configuration
kcli server config
```

### User Administration

```bash
# Create users
kcli user create-superuser
kcli user create-first-superuser
```

## Help System

Get detailed help for any command:

```bash
kcli --help
kcli [command] --help
```
