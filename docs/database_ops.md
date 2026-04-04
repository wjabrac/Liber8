# Database Ops

## Current CLI Surfaces

```bash
python -m src.cli list-migrations
python -m src.cli admin-snapshot --storage-dir .storage --backend fallback
```

## Current SQL Assets

- `sql/postgres/001_service_schema.sql`
- `sql/postgres/002_workflow_schema.sql`

## Intended Use

- inspect migration files and checksums before deployment
- apply them with the production PostgreSQL operator workflow
- verify service config and queue state through the redacted admin snapshot

## Current Limitation

The repository can enumerate and document migrations, but it does not yet apply them directly because live database execution is environment-specific and should not be guessed.
