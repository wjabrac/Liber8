# PerformanceTrace v0 (spec anchor)

Purpose: make the TagSet the nerve center for performance, failure, and efficacy tracking; enable DSPy↔Zep cognition optimization without hard-coding internals too early.

Required properties (JSON-serializable):
- trace_id (uuid)
- run_id (uuid or timestamp)
- created_at (UTC ISO)
- task (string)
- tags (TagSet)
- decision_points: list of
  - name (e.g., tag_extraction, query_planning, routing, synthesis, writeback)
  - inputs_summary (small JSON)
  - choice (small JSON)
  - rationale (string, optional)
  - latency_ms (number, optional)
- retrieval_stats (optional):
  - k_requested, k_returned
  - scores: list of {id, score, components}
  - diversity_hits: list
  - expansion_applied: list
- outcome:
  - outcome (success|failure|degraded)
  - failure_class (optional)
  - evaluation_outcome (string)
  - validators: list of strings
- costs (optional placeholders):
  - model_calls (int)
  - tokens_in, tokens_out (numbers)
  - cost_usd (number)
- provenance:
  - git_commit
  - engine_version
  - cognition_backend (dspy+zep|fallback)
  - config_hash

Non-goals:
- This spec does not mandate DSPy module shapes or Zep storage layout.
- It mandates what must be measurable and replayable.

Acceptance criteria:
- A run produces at least one PerformanceTrace object linked from EventRecord.provenance.
- Trace payload size is bounded; large artifacts are referenced by file path.
