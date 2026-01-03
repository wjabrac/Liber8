# CX-004 — Small-agent decomposition and router

Goal
Decompose the cognition loop into small agents with explicit contracts, then implement a router that composes them.

Inputs
- src/contracts.py
- src/cognition_loop.py (reference)
- spec/tag_schema_v0_1.md (when available; until then use v0)
- spec/memory_lanes_policy_v0.md (when available)

Deliverables (code)
- src/agents/tagger_agent.py
- src/agents/retrieval_agent.py
- src/agents/synthesis_agent.py
- src/agents/writeback_agent.py
- src/orchestration/router.py
- tests/test_router_smoke.py

Agent contracts
- Each agent must accept only primitives (strings, dicts) plus contract objects, and must return contract objects.
- No agent should write to disk directly except the writeback agent and event logging at the router level.
- Each agent should have a small, testable surface.

Router behavior (minimum)
- Input: task string, storage_dir path, fake_backend flag
- Output: EventRecord
- Steps:
  a) tagger_agent returns TagSet
  b) retrieval_agent returns retrieved MemoryBlocks plus QueryPlan
  c) synthesis_agent returns synthesis string plus WritebackPackage
  d) writeback_agent writes MemoryBlock and returns written block id
  e) router emits EventRecord and writes event log

Robustness requirements
- Router must catch ValidationError and record failure_class.
- Router must not crash on empty memory store.
- Router must be deterministic in fake_backend mode.

Acceptance criteria
- New smoke test proves router runs end-to-end and writes both memory.jsonl and eventlog.jsonl.
- Existing tests still pass.
- Router produces EventRecord with correct action sequence and retrieved_ids list.

Do-not-do
- No IDE integration.
- No Docker.
- No external services required.
