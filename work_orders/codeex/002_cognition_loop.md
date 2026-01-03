# CX-002 — Minimal cognition loop (DSPy + memory adapter) smoke test

Goal
Create a runnable end-to-end vertical slice:
task -> tag extraction -> memory retrieval -> synthesis -> writeback -> event log.

Inputs
- src/contracts.*
- src/eventlog.*
- spec/*

Deliverables (code)
- src/cognition_loop.(py|ts)
- src/memory_adapter.(py|ts)  (start with a stub + filesystem; swap to Zep/mem0 later)
- src/tagger.(py|ts)          (DSPy module wrapper)
- tests/test_smoke.*

Runtime requirements
- No Docker.
- Must run with local model endpoint configuration (env-based), but tests should allow a deterministic fake backend.

Acceptance criteria
- One command runs the loop and produces:
  - a valid EventRecord
  - at least one memory read and one memory write (even if filesystem-backed)
  - deterministic output under “fake backend” mode

Do-not-do
- No IDE integration work.
- No additional orchestration frameworks yet (LangGraph/Temporal only after loop is proven).
