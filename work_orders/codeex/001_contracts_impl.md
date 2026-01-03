# CX-001 — Implement contracts + event log (v0)

Goal
Implement the v0 contracts and event logging primitives as code with tests.

Inputs
- spec/contracts_v0.md
- spec/tag_schema_v0.md
- spec/failure_classes_v0.md

Deliverables (code)
- src/contracts.(py|ts)  (pick the project’s dominant language)
- src/eventlog.(py|ts)
- tests/test_contracts.*
- tests/test_eventlog.*

Requirements
- JSON-serializable structures.
- Strict validation (Pydantic/Zod/etc.).
- No external services required to run tests.

Acceptance criteria
- Unit tests pass locally.
- A single EventRecord can be created, validated, serialized, and written to disk.
- No changes to existing runtime behavior beyond additive modules.

Do-not-do
- No broad refactors.
- No Docker requirement.
- No network calls in unit tests.
