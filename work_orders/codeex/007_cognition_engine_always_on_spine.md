# CX-007 CognitionEngine always-on spine (DSPy+Zep primary, degraded fallback)

Objective
Implement the CognitionEngine spine per spec/cognition_engine_spine_v0.md. DSPy+Zep are primary; fallback is brief degraded operation using deterministic tagger and filesystem memory adapter.

Scope
- Add src/cognition/engine.py (or equivalent) exposing CognitionEngine.run(task, run_dir, config)
- Wire in existing contracts (TagSet, QueryPlan, MemoryBlock, EventRecord)
- Store PerformanceTrace v0 alongside EventRecord and link in provenance

Files
- src/cognition/engine.py
- src/cognition/config.py (optional)
- src/trace.py (PerformanceTrace model + writer)
- src/cognition_loop.py updated to call CognitionEngine

Acceptance criteria
- A single un() produces:
  - .runs/<run_id>/meta.json
  - .runs/<run_id>/eventlog.jsonl
  - .runs/<run_id>/trace.jsonl (PerformanceTrace entries)
  - .runs/<run_id>/memory.jsonl (or adapter-backed store)
- If DSPy/Zep not available, engine logs outcome=degraded and completes using fallbacks.
- Invariants/contract validation is fail-closed: invalid records do not get written silently.

Tests
- Add/extend smoke test to assert trace + meta.json + eventlog outputs exist and parse.
