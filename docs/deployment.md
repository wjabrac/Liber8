# Deployment Notes

## Intended Production Shape

- Linux VM
- long-running service/API
- `CognitionEngine` as the canonical cognition core
- PostgreSQL for service-side operational state
- VM-backed execution for mutation-capable tool paths

## Current Repository Scaffolding

- `.env.example` for non-secret defaults and overrides
- `deploy/systemd/libr8.service` as an initial Linux supervision template
- `sql/postgres/001_service_schema.sql` as the initial operational schema seed
- `sql/postgres/002_workflow_schema.sql` for review queue and export job state
- `python -m src.cli list-migrations` to enumerate the current SQL assets

## Not Yet Implemented

- final VM execution adapter
- PostgreSQL-backed runtime verification against a live database
- secret-manager integration
- release and rollback automation

## Related Docs

- [Service API](/home/willux/LIBR8_WORKSPACE/LIBR8/docs/service_api.md)
- [Secrets and Config](/home/willux/LIBR8_WORKSPACE/LIBR8/docs/secrets_and_config.md)
- [Release and Rollback](/home/willux/LIBR8_WORKSPACE/LIBR8/docs/release_and_rollback.md)
