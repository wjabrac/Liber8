param(
  [Parameter(Mandatory=$true)]
  [string]$RepoRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Ensure-Dir([string]$p) {
  if (-not (Test-Path $p)) { New-Item -ItemType Directory -Force -Path $p | Out-Null }
}

function Write-MD([string]$path, [string]$body) {
  Ensure-Dir (Split-Path $path -Parent)
  $body | Out-File -Encoding utf8 -FilePath $path
  Write-Host "WROTE: $path"
}

$root = (Resolve-Path $RepoRoot).Path
$woCodeex = Join-Path $root "work_orders\codeex"
$woAG = Join-Path $root "work_orders\antigravity"
$spec = Join-Path $root "spec"

Ensure-Dir $woCodeex
Ensure-Dir $woAG
Ensure-Dir $spec

# ----------------------------------------------------------------------------
# SPEC ANCHORS (contracts-as-law)
# ----------------------------------------------------------------------------

Write-MD (Join-Path $spec "performance_trace_v0.md") @"
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
"@

Write-MD (Join-Path $spec "cognition_engine_spine_v0.md") @"
# Cognition Engine Spine v0 (spec anchor)

Premise: DSPy + Zep are the always-on cognition engine for sensemaking + planning, with tag-coordinate memory as the nerve center.
Constraint: when DSPy/Zep are unavailable, system enters degraded mode briefly but preserves contracts + logs.

Spine (always executed in this order):
1) Tag extraction (DSPy-optimized; deterministic fallback)
2) Query planning (DSPy-optimized; deterministic fallback)
3) Retrieval (Zep adapter; filesystem fallback)
4) Routing / decomposition into small agents (DSPy-optimized; deterministic fallback)
5) Synthesis / action selection (model or deterministic; must be logged)
6) Writeback packaging (lane policy; must be logged)
7) Persistence (Zep adapter; filesystem fallback)
8) Trace emission + invariants validation (fail-closed)

Key rule:
- Tags are the coordinate system for routing, retrieval, evaluation, and failure classification.

Acceptance criteria:
- Implementation exposes a single CognitionEngine interface that can run in (a) dspy+zep mode, (b) degraded fallback mode, without changing call sites.
"@

Write-MD (Join-Path $spec "retrieval_scoring_v0_1.md") @"
# Retrieval Scoring v0.1 (spec anchor)

Objective: tag-first retrieval (no vectors required) with explainable scoring and bounded expansion/diversity rules.

Score components (normalized to 0..1 then combined):
- tag_overlap: weighted overlap between query TagSet and MemoryBlock TagSet
- recency: decay function over created_at/updated_at
- lane_bonus: optional lane preference (episodic/semantic/procedural) based on query intent
- provenance_bonus: optional preference for trusted sources
- penalty terms: low confidence blocks, expired valid_until

Required outputs:
- for each candidate: {id, score, components:{tag_overlap, recency, lane_bonus, ...}, matched_tags:[...]}
- explanation payload stored in EventRecord.provenance and/or PerformanceTrace.retrieval_stats

Constraints:
- diversity rules: enforce configurable uniqueness (e.g., unique_sources)
- expansion rules: bounded expansions (synonyms/hierarchy) with hard caps and trace logging

Acceptance criteria:
- Retriever returns top-k results with explanation payload.
- Diversity/expansion behavior is observable in traces.
"@

Write-MD (Join-Path $spec "failure_taxonomy_v0_1.md") @"
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
"@

Write-MD (Join-Path $spec "execution_gateway_policy_v0.md") @"
# Execution Gateway Policy v0 (spec anchor)

Goal: safe, auditable tool execution with an allowlist and per-tool policies.

Requirements:
- ToolRegistry with explicit enablement
- ToolPolicy: read_only vs write, network_allowed flag, path allowlists
- Every tool call logs: inputs summary, outputs summary, duration, errors, and policy decision
- Default tooling should be non-destructive; destructive tools require explicit user approval in the client environment

Acceptance criteria:
- ExecutionGateway rejects unknown tools by default.
- Tool calls are recorded in EventRecord.tool_calls and PerformanceTrace.
"@

# ----------------------------------------------------------------------------
# CODEX WORK ORDERS (Phase 3+)
# ----------------------------------------------------------------------------

Write-MD (Join-Path $woCodeex "007_cognition_engine_always_on_spine.md") @"
# CX-007 CognitionEngine always-on spine (DSPy+Zep primary, degraded fallback)

Objective
Implement the CognitionEngine spine per spec/cognition_engine_spine_v0.md. DSPy+Zep are primary; fallback is brief degraded operation using deterministic tagger and filesystem memory adapter.

Scope
- Add `src/cognition/engine.py` (or equivalent) exposing `CognitionEngine.run(task, run_dir, config)`
- Wire in existing contracts (TagSet, QueryPlan, MemoryBlock, EventRecord)
- Store PerformanceTrace v0 alongside EventRecord and link in provenance

Files
- src/cognition/engine.py
- src/cognition/config.py (optional)
- src/trace.py (PerformanceTrace model + writer)
- src/cognition_loop.py updated to call CognitionEngine

Acceptance criteria
- A single `run()` produces:
  - `.runs/<run_id>/meta.json`
  - `.runs/<run_id>/eventlog.jsonl`
  - `.runs/<run_id>/trace.jsonl` (PerformanceTrace entries)
  - `.runs/<run_id>/memory.jsonl` (or adapter-backed store)
- If DSPy/Zep not available, engine logs `outcome=degraded` and completes using fallbacks.
- Invariants/contract validation is fail-closed: invalid records do not get written silently.

Tests
- Add/extend smoke test to assert trace + meta.json + eventlog outputs exist and parse.
"@

Write-MD (Join-Path $woCodeex "008_run_sessions_and_meta_json.md") @"
# CX-008 Run sessions + meta.json

Objective
Create a consistent per-run directory and metadata file used by replay/export and by future optimization.

Scope
- Add `src/runs/session.py` with `create_run_dir(base_dir)->Path` and `write_meta(run_dir, meta)`
- meta.json includes: run_id, created_at, git_commit, engine_version, config_hash, cognition_backend

Acceptance criteria
- CLI and CognitionEngine always create and populate meta.json
- git commit is captured when available (empty string acceptable if not)

Tests
- Unit test meta.json schema presence and required keys.
"@

Write-MD (Join-Path $woCodeex "009_retriever_scoring_and_explanations.md") @"
# CX-009 Tag-first retrieval scoring + explanations

Objective
Implement tag-first retrieval scoring per spec/retrieval_scoring_v0_1.md and ensure explanations are emitted into trace/provenance.

Scope
- Implement `src/retrieval/scoring.py` and `src/retrieval/retriever.py`
- Support diversity rules and bounded expansion rules
- Return top-k with explanation payload

Acceptance criteria
- Retriever returns list[MemoryBlock] and a parallel explanation object
- Explanations stored in PerformanceTrace.retrieval_stats and/or EventRecord.provenance
- Expansion/diversity decisions are visible in trace

Tests
- Unit tests for scoring determinism, diversity enforcement, and expansion caps.
"@

Write-MD (Join-Path $woCodeex "010_small_agents_router_v1.md") @"
# CX-010 Small-agents router v1 with decision logging

Objective
Implement a router that decomposes tasks into a sequence of small agents using TagSet features. Must log candidates, decision features, and rationale into PerformanceTrace.

Scope
- Add `src/agents/base.py` (Agent interface)
- Add `src/router/router.py` (select agents, sequence)
- Stub agents: TaggerAgent, QueryPlannerAgent, RetrieverAgent, SynthesizerAgent, WritebackAgent
- Router emits decision_points entries with candidates considered and chosen agent(s)

Acceptance criteria
- Running engine produces a trace where routing is explicit and auditable
- Router policy is data-driven (table/rules) and easy to swap later by DSPy

Tests
- Unit test that router emits decision log and returns a stable sequence in fake mode.
"@

Write-MD (Join-Path $woCodeex "011_writeback_lanes_policy_v0_1.md") @"
# CX-011 Writeback lanes policy v0.1 (episodic/semantic/procedural)

Objective
Implement lane selection, TTL/valid_until, and writeback packaging. Store promotion/demotion decisions in trace.

Scope
- Implement `src/memory/policy.py` with lane selection rules
- Update writeback path to set MemoryBlock.lane and valid_until
- Ensure WritebackPackage is written into EventRecord.provenance.writeback

Acceptance criteria
- Every successful run writes at least one MemoryBlock with lane populated
- TTL rules are enforced (expired blocks excluded from retrieval)
- Promotion/demotion notes are present in writeback package

Tests
- Unit tests for TTL exclusion and lane decisions.
"@

Write-MD (Join-Path $woCodeex "012_execution_gateway_v1.md") @"
# CX-012 ExecutionGateway v1 (allowlist + audited tool calls)

Objective
Implement an ExecutionGateway and ToolRegistry per spec/execution_gateway_policy_v0.md. Default tools are non-destructive.

Scope
- Add `src/execution/gateway.py`, `src/execution/tools.py`, `src/execution/policy.py`
- Provide NullTool, FileReadTool (read-only within allowlisted paths)
- Capture all tool calls into EventRecord.tool_calls and PerformanceTrace decision_points

Acceptance criteria
- Unknown tools are rejected by default
- Tool calls include inputs/outputs summaries and durations
- No Docker required

Tests
- Unit test tool allowlist and policy enforcement.
"@

Write-MD (Join-Path $woCodeex "013_resilience_retry_policy_v1.md") @"
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
"@

Write-MD (Join-Path $woCodeex "014_replay_and_export_v1.md") @"
# CX-014 Replay + export v1

Objective
Enable deterministic replay for fake mode and produce a readable run report for debugging and optimization.

Scope
- Implement `src/replay.py` to rerun from `.runs/<run_id>/meta.json`
- Implement `src/export.py` to export a markdown report summarizing:
  - tags, routing decisions, retrieval stats, failures, writeback summary
- Keep artifacts referenced by path; do not duplicate large payloads

Acceptance criteria
- `libr8 replay <run_dir>` works in fake mode deterministically
- `libr8 export <run_dir>` writes `report.md`

Tests
- Smoke test ensures report.md is produced and contains key sections.
"@

Write-MD (Join-Path $woCodeex "015_ci_workflow_tests.md") @"
# CX-015 CI workflow: run tests on push/PR

Objective
Add GitHub Actions workflow to run unit tests.

Scope
- Add `.github/workflows/ci.yml` running:
  - python (minimum one version)
  - `python -m unittest discover -s tests -v`

Acceptance criteria
- CI runs and passes on default branch for current tests.
"@

Write-MD (Join-Path $woCodeex "016_dspy_zep_fusion_prototype.md") @"
# CX-016 DSPy↔Zep fusion prototype (primary cognition path)

Objective
Implement the primary cognition backend using DSPy for decision points and Zep for memory persistence/retrieval, while preserving the contracts spine and traces.

Scope
- Add adapters:
  - `src/integrations/dspy_backend.py` (Tagger + QueryPlanner + Router policy interfaces)
  - `src/integrations/zep_adapter.py` (MemoryAdapter implementation)
- Ensure the engine can run with:
  - cognition_backend=dspy+zep (primary)
  - cognition_backend=fallback (degraded)
- Optimization signals:
  - write per-run `optimization_signals.jsonl` keyed by TagSet

Acceptance criteria
- When configured with endpoints/credentials, engine uses Zep adapter for read/write
- Decision_points indicate DSPy origin for tag/query/router decisions
- If backend fails, degraded mode triggers and is logged

Tests
- Use mocks; do not require live Zep server for unit tests.
"@

Write-MD (Join-Path $woCodeex "017_rust_candidates_boundary.md") @"
# CX-017 Rust candidates boundary (design-only)

Objective
Define the boundary where Rust can later replace hot-path components without rewriting the engine.

Scope
- Add `docs/rust_boundary.md` describing:
  - candidate modules (retrieval ranking, index build, jsonl parsing, trace aggregation)
  - required surface (inputs/outputs)
  - fallback behavior if Rust module absent
- Do not introduce Rust build tooling yet.

Acceptance criteria
- Document exists and references concrete Python module entry points intended to be swapped later.
"@

# ----------------------------------------------------------------------------
# ANTIGRAVITY WORK ORDERS (Phase 3+ specs and policies)
# ----------------------------------------------------------------------------

Write-MD (Join-Path $woAG "005_retrieval_scoring_v0_1_spec.md") @"
# AG-005 Retrieval scoring v0.1 spec (tag-first, explainable)

Deliverable
A markdown spec that fully defines:
- scoring components and combination rule
- diversity enforcement semantics
- expansion semantics + hard caps (bounded and logged)
- required explanation payload structure (for traces)

Constraints
- No vectors required; tag-first is primary.
- Must be implementable as a pure function over TagSet + candidate TagSets + metadata.

Acceptance criteria
- Includes at least 5 edge cases (missing tags, expired blocks, low confidence, identical provenance, conflicts).
- Includes an example explanation payload.
"@

Write-MD (Join-Path $woAG "006_event_audit_invariants_v0_spec.md") @"
# AG-006 Event/Audit invariants v0 spec

Deliverable
A markdown spec listing invariants that MUST hold for:
- TagSet
- QueryPlan
- MemoryBlock
- WritebackPackage
- EventRecord
- PerformanceTrace

Include
- fail-closed rules (what aborts the run)
- what gets logged when an invariant fails
- how degraded mode is represented

Acceptance criteria
- Clear checklist form.
- No assumptions beyond the contracts.
"@

Write-MD (Join-Path $woAG "007_dspy_memory_contract_v0_spec.md") @"
# AG-007 DSPy↔Memory contract v0 spec

Deliverable
A markdown spec defining the interface between:
- DSPy decision modules (tagger, query planner, router, writeback importance)
and
- memory retrieval/persistence (Zep or fallback)

Must define
- inputs/outputs at each decision point
- what “optimization signals” are emitted
- how success is graded from traces
- how TagSet indexes performance and failure

Acceptance criteria
- Defines at least 3 success metrics and how to compute them from traces.
- Includes a minimal learning-loop diagram in text form.
"@

Write-MD (Join-Path $woAG "008_memory_lanes_policy_v0_1_spec.md") @"
# AG-008 Memory lanes policy v0.1 spec

Deliverable
A markdown spec for:
- lane definitions (episodic/semantic/procedural)
- promotion/demotion triggers
- TTL/valid_until rules
- provenance requirements per lane
- writeback quality gates (avoid storing junk)

Acceptance criteria
- Includes examples of a MemoryBlock in each lane
- Includes an example promotion (episodic -> semantic)
- Includes procedural snippet extraction guidance
"@

Write-MD (Join-Path $woAG "009_failure_retry_policy_v0_1_spec.md") @"
# AG-009 Failure taxonomy + retry policy v0.1 spec

Deliverable
A markdown spec that:
- defines failure classes (aligned with spec/failure_taxonomy_v0_1.md)
- maps classes to retry/backoff/stop behavior
- defines degraded mode transitions and recovery

Acceptance criteria
- Includes at least 6 failure scenarios and expected trace entries.
"@

Write-MD (Join-Path $woAG "010_tag_weighting_and_performance_indexing.md") @"
# AG-010 Tag weighting + performance indexing (nerve center)

Deliverable
A markdown spec that defines:
- how tags get weights (static priors + learned adjustments)
- how performance traces aggregate by tag clusters
- how failure patterns are detected by tags
- how efficacy is computed for a strategy keyed by tags

Constraints
- Must be implementable without vectors.
- Must not assume a particular DSPy optimizer; define signals generically.

Acceptance criteria
- Includes a minimal aggregation report schema.
"@

Write-MD (Join-Path $woAG "011_trimming_playbook.md") @"
# AG-011 Trimming playbook: fuse DSPy+Zep, remove overhead

Deliverable
A markdown playbook describing methodology:
- identify redundant representations and duplicate computation
- cache plan (keys + invalidation)
- payload-size discipline in trace/eventlog
- criteria for Rust replacement (evidence thresholds)

Acceptance criteria
- Stepwise checklist executable using trace outputs.
"@

Write-Host ""
Write-Host "Done. Phase 3+ work orders created under:"
Write-Host "  $woAG"
Write-Host "  $woCodeex"
Write-Host "and spec anchors updated under:"
Write-Host "  $spec"
