# Release and Rollback

## Current Posture

Release handling is still operator-driven, but the repository now includes enough service and artifact scaffolding to define a basic forward-fix process.

## Release Steps

1. Validate unit and focused service-path tests in the canonical Linux or WSL environment.
2. Apply PostgreSQL schema migrations if operational DB changes are included.
3. Stage updated environment variables and secret material.
4. Deploy code to the Linux service host.
5. Restart the service supervisor.
6. Confirm `/healthz` and `/readyz`.
7. Submit a representative internal task and verify run artifacts are emitted.

## Rollback Principle

Prefer forward-fix when the state surface is ambiguous.

Rollback is safest when all of the following are true:

- schema is unchanged or backward compatible
- no new mutation-capable execution path was enabled
- operational config can be restored cleanly

## Fast Recovery Steps

1. Disable risky execution features through config if the issue is isolation- or tool-related.
2. Preserve current run artifacts for diagnosis.
3. Revert to the last known-good service package only if schema and config compatibility are clear.
4. Re-run health checks and one representative task.
5. Capture the failure exemplar for replay and promotion review.
