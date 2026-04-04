# Service API

The current service surface is intentionally small and uses the Python standard library HTTP server.

## Endpoints

- `GET /healthz`: basic service health and configuration summary
- `GET /readyz`: readiness result; returns `503` when isolation is required but not configured
- `GET /retention/preview`: age/size retention preview for current artifacts
- `GET /admin/migrations`: list available PostgreSQL schema seed files with checksums
- `GET /admin/snapshot`: return a redacted runtime snapshot of config, queues, and state-store summary
- `GET /admin/schema`: return a machine-readable endpoint catalog
- `POST /v1/runs`: submit a task payload like `{ "task": "summarize architecture" }`
- `GET /v1/runs/<task_id>`: fetch the in-service record for a submitted task
- `GET /v1/approvals`: list pending approval requests
- `POST /v1/approvals`: submit an approval request payload with `task_id`, `scope`, and `reason`
- `POST /v1/approvals/<request_id>/resolve`: resolve an approval as `approved` or `rejected`
- `GET /v1/exports`: list export jobs
- `POST /v1/exports`: submit an export job with `run_id`
- `POST /v1/exports/<job_id>/process`: process an export job immediately in-process

## Local Start

```bash
python -m src.cli serve --host 127.0.0.1 --port 8080 --storage-dir .storage --backend fallback
```

## Operator Commands

```bash
python -m src.cli service-health --storage-dir .storage --backend fallback
python -m src.cli admin-snapshot --storage-dir .storage --backend fallback
python -m src.cli list-migrations
```

## Current Limits

- task submission is synchronous inside the process
- approval queue is in-memory only
- export job queue is in-memory only
- state store is in-memory unless a different implementation is added
- the HTTP transport is suitable for internal development and operator flows, not public exposure
- VM-backed execution for mutation-capable tool paths is still pending
