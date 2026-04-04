# Failure Taxonomy v0.1 (spec anchor)

Purpose: classify failures for retry/backoff/stop policy and post-hoc learning keyed by TagSet.

Classes (minimum set):
- transient_io
- transient_model
- transient_rate_limit
- deterministic_contract_violation
- deterministic_validation_failure
- tool_permission_denied
- tool_execution_error
- memory_backend_unavailable
- planner_inconsistent
- unknown

Rules:
- contract violations and validation failures are not retried unless explicitly whitelisted.
- backend unavailable triggers degraded mode then recovery attempt.
- every failure must be logged with failure_class and a minimal structured reason.

Acceptance criteria:
- Exceptions map to a failure_class deterministically.
- Retry policy consumes failure_class and emits trace decisions.
