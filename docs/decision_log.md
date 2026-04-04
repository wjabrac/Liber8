# Decision Log

This document is the consolidated record of decisions that currently govern the LIBR8 build.

## 1. Core Architecture Decisions

- `CognitionEngine` is the only canonical orchestrator.
- The cognition core remains the mind of the system.
- The core continues to own DSPy reasoning, tags, memory, retrieval, routing, evaluation, writeback, replay, self-learning, and proceduralization.
- Tags remain the internal coordinate system for retrieval, routing, evaluation, enrichment selection, failure classification, and promotion decisions.
- LIBR8 is not a swarm-first architecture.
- Small agents remain bounded workers selected by the cognition core.
- LIBR8 is not a one-model architecture.
- Different models may be assigned by role.

## 2. Terminology Decisions

- The term `brain` is dropped.
- The correct term is `specialization plugin`.
- A specialization plugin is an optional enrichment or role-specific helper attached to a run.
- A specialization plugin does not replace the cognition core, the main planner, the memory authority, or the orchestrator.

## 3. Runtime and Interface Decisions

- Production runtime shape is a long-running service/API on Linux.
- The CLI remains an operator surface for local runs, replay, export, maintenance, and service control.
- Local UI and speech-to-text are later outer shells over the same core.
- These outer shells are convenience surfaces only.
- They do not change the cognition core.

## 4. Model and Plugin Decisions

- Different models may be used for different roles.
- Examples include planning, execution, programming, strategy, critique, charm or tone, and marketing.
- Specialization plugins may add domain framing, style shaping, tone shaping, role-specific enrichment, and bounded execution support.
- Specialization plugins are repo-internal only for now.
- Role- or plugin-scoped long-term memories are allowed as long as shared truth remains centralized.

## 5. Small-Agent Decisions

- Small agents remain explicit bounded workers.
- They remain in-process with explicit contracts for now.
- They do not become remote workers or independent orchestration loops at this stage.

## 6. Tool and Open Interpreter Decisions

- Open Interpreter is treated as a bounded tool executor.
- Open Interpreter does not become the orchestrator.
- All tool use remains behind `ExecutionGateway`.
- The gateway remains the governance boundary for policy, approvals, path controls, sanitization, logging, result normalization, and failure handling.
- MCP-backed tooling is immediate.
- MCP is the first-class tool protocol under `ExecutionGateway` from day one, not a gateway replacement.

## 7. Backend and Fallback Decisions

- The intended operating model is primary DSPy plus memory backend, with a real fallback mode.
- Fallback mode must preserve the same contracts and artifact shapes as the primary path.
- Backend switching is part of the design and is considered a feature.

## 8. Memory Decisions

- Memory remains central to cognition.
- The memory architecture continues to use episodic, semantic, and procedural memory.
- SQLite is the authoritative runtime store for episodic and semantic state.
- Versioned files or Markdown are the authoritative store for promoted procedures, curated skills, and durable human-readable artifacts.
- Zep or graph-oriented memory remains valuable as a retrieval layer, sync layer, or accelerator, but not as the only durable source of truth.
- PostgreSQL is additive operational state, not cognition memory.

## 9. Telemetry and Analytics Decisions

- Internal telemetry derived from tags, traces, memory rows, and run artifacts remains primary.
- Analytics should remain artifact-derived and tag-derived by default.
- SQLite-backed telemetry and DSPy-structured outputs are a core strength because they make analysis cheap and native.
- External telemetry systems are optional egress sinks, not the analytics brain.
- Observability export goes beyond flat artifacts immediately.
- The system emits structured nested execution spans at `ai.agent.invoke`, `ai.tool.invoke`, and `ai.llm.invoke`.
- These spans become the high-fidelity trace substrate for analytics, replay, drift analysis, and proceduralization.

## 10. Sandbox and Security Decisions

- Project-root-only limits are not the long-run answer for executing model-generated code.
- MicroVM-backed isolation is required at launch for model-generated code and mutation-capable shell actions.
- The cognition core does not need to wait on MicroVM rollout to exist.
- Real execution paths go straight to the stronger sandbox rather than relying on project-root-only isolation.
- Hyper-V is the immediate built-in local direction on this machine.
- The initial production posture is safe internal production candidate, not public exposure.

## 11. Approval and Execution-Policy Decisions

- Tool approval is environment-aware.
- Development may be more automatic under policy.
- Production should be more gated.
- Writes and higher-risk actions remain approval-aware.
- Service-side approvals, promotion review, and export jobs belong in the operational control plane.

## 12. Promotion and Proceduralization Decisions

- Promotion and proceduralization remain core compounding mechanisms.
- The system goal is to make future runs increasingly programmatic.
- The default promotion authority is auto-generate, validate, then require human approval before activation.
- Promotion storage follows a mixed model: procedural memory for runtime use and versioned files for durable, auditable promoted procedures.
- Procedural promotion remains central to reducing LLM dependence over time.

## 13. Failure-Policy Decisions

- The agreed direction is selective fallback.
- Recoverable backend or availability failures should degrade or fallback automatically.
- Contract, validation, policy, and safety failures should stop cleanly.
- Circuit-breaker thinking is part of the intended failure model.
- The build should avoid silent retry spirals and silent quality degradation.
- Migration policy is forward-fix rather than rollback-first.
- Because the system is stateful and tool-active, recovery should prefer graceful degradation and forward correction over reverting execution state.

## 14. Versioning Decisions

- Versioning is composite and explicit.
- Artifacts carry decoupled version identities such as core engine version, active skill or procedure version, and plugin version where relevant.
- This version payload attaches to traces, memory objects, writebacks, and promoted procedures.

## 15. Observability Decisions

- Strong internal run artifacts remain mandatory: `meta.json`, `eventlog.jsonl`, `trace.jsonl`, `memory.jsonl`, and `writeback.json`.
- Structured replayable artifacts remain mandatory.
- Nested execution spans are part of the immediate observability layer rather than a later addition.

## 16. Prototype-Operation Defaults

- Concurrency remains single-run at a time for now.
- CI gate remains unit plus smoke.
- Release process remains manual tagged releases until automated release handling is added.
- Rollback is currently forward-fix plus artifact-backed diagnosis, with stronger state-aware rollback later if needed.
- Config authority remains checked-in non-secret defaults plus environment overrides plus secret injection outside the repo.

## 17. Build and Alignment Decisions

- All entry surfaces should continue aligning around one truthful control path.
- The architecture prefers one canonical orchestration path with wrapper-based compatibility rather than multiple independent execution paths.
- The build should continue moving toward a stable, replayable, contract-driven runtime rather than toward more parallel control surfaces.
