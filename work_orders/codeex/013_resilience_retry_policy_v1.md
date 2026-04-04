# CX-013 Resilience: failure taxonomy + retry/backoff/stop + degraded mode

Objective
Wire failure taxonomy to retry/backoff/stop policy and degraded mode logic.

Scope
- Map exceptions to failure classes (spec/failure_taxonomy_v0_1.md)
- Implement retry engine with bounded attempts and backoff (configurable in code)
- Degraded mode: Zep unavailable -> filesystem fallback; DSPy compile error -> last-known-good policy (if present) else deterministic fallback

Acceptance criteria
- On forced failures, EventRecord.outcome=failure and failure_class populated
- Retry decisions are visible in trace decision_points
- Degraded mode is explicitly logged (outcome=degraded)

Tests
- Unit tests for classification mapping and retry stop behavior.
