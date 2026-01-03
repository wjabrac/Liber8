# AG-001 — Contract extraction (v0)

Goal
Produce implementable, versioned contracts from AG_EXTRACT primitives analysis, without proposing a final architecture.

Inputs
- AG_EXTRACT/analysis/*.md
- AG_EXTRACT/orchestration/**
- AG_EXTRACT/execution/**
- AG_EXTRACT/memory/**
- AG_EXTRACT/evaluation/**
- AG_EXTRACT/resilience/**
- AG_EXTRACT/walkthrough.md (if present)

Deliverables (write these files)
- spec/contracts_v0.md
- spec/tag_schema_v0.md
- spec/failure_classes_v0.md

Requirements
- Prefer verbatim references and path citations to AG_EXTRACT artifacts.
- Define the minimum fields and invariants required for interoperability.

Define (minimum)
1) EventRecord
- id, timestamp, task, tags, query_plan, retrieved_ids, actions, tool_calls, validations, outcome, failure_class, retries, cost, latency, provenance

2) TagSet
- schema_version, required keys, allowed values, numeric ranges, uncertainty representation, migration notes

3) QueryPlan
- filters, limits, recency bias, diversity rules, expansion rules, scoring knobs

4) MemoryBlock
- content, tags, provenance, timestamps, validity/expiry, confidence, lane/type (episodic/semantic/procedural)

5) WritebackPackage
- episode, distilled facts, procedural snippet (if any), tags, evaluation outcome, promotion/demotion notes

Acceptance criteria
- All three spec files exist and are coherent as a single contract set.
- Contracts are implementable without guessing missing fields.
- No “final architecture” section. No refactors. No code changes.

Do-not-do
- No pruning of primitives based on perceived importance.
- No recommendations to adopt external frameworks as foundations.
- No destructive changes anywhere in repo.
