# CX-016 DSPy↔Zep fusion prototype (primary cognition path)

Objective
Implement the primary cognition backend using DSPy for decision points and Zep for memory persistence/retrieval, while preserving the contracts spine and traces.

Scope
- Add adapters:
  - src/integrations/dspy_backend.py (Tagger + QueryPlanner + Router policy interfaces)
  - src/integrations/zep_adapter.py (MemoryAdapter implementation)
- Ensure the engine can run with:
  - cognition_backend=dspy+zep (primary)
  - cognition_backend=fallback (degraded)
- Optimization signals:
  - write per-run optimization_signals.jsonl keyed by TagSet

Acceptance criteria
- When configured with endpoints/credentials, engine uses Zep adapter for read/write
- Decision_points indicate DSPy origin for tag/query/router decisions
- If backend fails, degraded mode triggers and is logged

Tests
- Use mocks; do not require live Zep server for unit tests.
