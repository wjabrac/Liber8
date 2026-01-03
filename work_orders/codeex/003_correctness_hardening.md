# CX-003 — Correctness hardening for v0 loop and storage

Goal
Make the existing v0 contracts and cognition loop correct and robust without refactoring the project structure.

Inputs
- src/memory_adapter.py
- src/cognition_loop.py
- src/contracts.py
- tests/*

Scope constraints
- Keep changes minimal and localized.
- No new external runtime dependencies.
- No Docker.
- Add tests for all new behavior.

Tasks
1) Tag-filtered retrieval
- Update FileSystemMemoryAdapter.read to filter results using TagSet.
- Minimum acceptable filter: return blocks that match at least one exact key:value from tags.tags.
- Preserve current behavior when tags.tags is empty: return all.

2) QueryPlan passthrough
- Update FileSystemMemoryAdapter.read signature to accept optional QueryPlan.
- Ensure cognition_loop passes query_plan to read.
- You may ignore QueryPlan scoring internally for now, but you must record that it is received and the limits parameter is applied (cap results).

3) Make "real backend" explicit
- In Tagger, rename the non-fake branch semantics to indicate it is a stub unless an actual HTTP call is implemented.
- If implementing HTTP call: use Python standard library only (urllib), simple JSON POST, and timeouts. Keep it behind a feature flag and do not break fake_backend.

4) Add tests
- New unit test: retrieval filtering works (two blocks, one matches, one not).
- New unit test: QueryPlan.limits is applied.
- All existing tests must continue to pass.

Acceptance criteria
- python -m unittest discover -s tests -v passes.
- Retrieval is deterministic and tag-aware.
- No new failing lint or formatting issues (do not add formatting tooling).

Do-not-do
- No global refactors.
- No replacing dataclasses with Pydantic.
