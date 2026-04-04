# Implementation Plan

## Goal

Map the LIBR8 architecture onto the current repository in a way that preserves one stable cognition core while allowing optional specialization, bounded workers, practical tool execution, and progressive self-learning.

## Architectural North Star

The target state is:

- one stable cognition core
- optional specialization plugins
- bounded small agents
- bounded tool execution through a gateway with MCP as the first-class tool protocol
- MicroVM-backed isolation for real model-generated and mutation-capable execution paths
- durable artifacts for replay and learning
- nested observability export through `ai.agent.invoke`, `ai.tool.invoke`, and `ai.llm.invoke`
- composite versioning across engine, procedures or skills, and plugins
- forward-fix recovery instead of rollback-first recovery
- progressive procedural promotion that reduces LLM dependence over time

## Current Repository Mapping

### Canonical cognition core

Primary implementation surface:

- `src/cognition/engine.py`
- `src/cognition/config.py`
- `src/retrieval/`
- `src/contracts/`
- `src/failures/`
- `src/replay/`
- `src/runs/`

Current status:
- `CognitionEngine` is the canonical orchestration spine.
- CLI and compatibility wrappers delegate into it.
- Retry-policy action handling is now wired into the engine.
- Artifact provenance includes the run artifact directory.

### Specialization plugins

Target role in architecture:
Optional attachments that shape style, domain context, heuristics, and enrichment.

Current status:
- Initial first-class plugin attachment support exists via `src/plugins/`.
- Plugin selection is wired into `CognitionEngine` and persisted in run provenance.
- Richer lifecycle and attachment policy are still incomplete.

Planned work:
- define a plugin contract
- decide attachment lifecycle for a run
- separate plugin enrichment from core planning authority
- ensure plugins cannot take durable-state ownership away from the core

### Small agents

Target role in architecture:
Bounded workers selected by the cognition core.

Current status:
- agent labels and routing decisions exist
- the current system records selected agents and bounded execution paths
- worker types are still lightweight and not fully formalized as independent bounded runtimes

Planned work:
- formalize agent contracts
- specify input, output, and trace expectations per agent type
- add stronger evaluation around delegated work quality

### Tools and automation

Target role in architecture:
Practical execution behind a logged and constrained boundary.

Current status:
- `ExecutionGateway` and `ToolPolicy` provide a boundary
- resolved-path containment is now shared through `src/tools/paths.py`
- MCP-backed tooling is the immediate protocol direction under the gateway
- `open_interpreter` is registered and invoked through the engine for interpreter-routed work
- MicroVM-backed execution is now the intended immediate boundary for real model-generated and mutation-capable code paths
- approval context, command output, and tool-call summaries are persisted in run artifacts

Planned work:
- document richer side-effect handling and replay policy
- add stronger conventions for tool-result writeback
- expand interpreter usage beyond the current conservative deterministic command path

## Workstreams

### Workstream 1: Preserve the stable cognition core

Objective:
Keep the cognition core architecture-stable while allowing model flexibility.

Concrete tasks:
- keep `CognitionEngine` as the sole orchestration authority
- keep DSPy and tags central to planning and routing
- ensure memory, replay, and promotion stay core-owned

Status:
In progress overall, structurally aligned in code.

### Workstream 2: Formalize specialization plugins

Objective:
Add optional plugin attachments without displacing core cognition.

Concrete tasks:
- define plugin registration
- define plugin contribution boundaries
- add plugin-aware enrichment selection
- prevent plugin ownership of orchestration or durable state

Status:
Initial implementation landed; richer isolation and lifecycle policy remain.

### Workstream 3: Formalize bounded small agents

Objective:
Turn current routing labels into explicit bounded-worker contracts.

Concrete tasks:
- define agent interfaces
- define permitted scopes and outputs
- define evaluation hooks
- add replay visibility for delegated work

Status:
Partially represented, not yet complete.

### Workstream 4: Complete the memory-lane model

Objective:
Ensure episodic, semantic, and procedural memory are all explicit and durable.

Concrete tasks:
- keep lane identity on every memory block
- define semantic writeback paths
- define procedural promotion outputs
- connect promotion decisions to replay and evaluation

Status:
Multi-lane persistence is present; broader policy around promotion and reuse still needs to mature.

### Workstream 5: Complete self-learning and proceduralization

Objective:
Reduce LLM dependence over time by promoting successful repeated structure.

Concrete tasks:
- identify replay-derived success patterns
- promote reusable procedures and macros
- store promotion artifacts durably
- route future tasks toward programmatic paths first where appropriate

Status:
`promotion.json` now captures explicit promotion output per run; the broader replay-driven learning loop is still incomplete.

### Workstream 6: Add explicit enrichment selection

Objective:
Make enrichment intentional rather than generic.

Concrete tasks:
- define enrichment sources
- define enrichment selection policy based on tags, plugin choice, and small-agent needs
- log enrichment choices in trace artifacts

Status:
Initial enrichment selection support landed and is recorded in run provenance.

### Workstream 7: Open Interpreter integration

Objective:
Treat Open Interpreter as a practical bounded executor behind the tool boundary.

Concrete tasks:
- define interpreter invocation contract
- route interpreter calls through the tool boundary
- log approvals, outputs, and side effects
- make interpreter usage replay-safe

Status:
A bounded `open_interpreter` tool is registered and invoked through the engine, but the remaining implementation work is to move real code-generation and mutation-capable paths onto the immediate MicroVM-backed boundary and align MCP-backed tooling under the same governance model.

### Workstream 8: Observability and Versioning

Objective:
Make traces, analytics, replay, and proceduralization depend on high-fidelity nested spans and composite version identities from day one.

Concrete tasks:
- emit nested execution spans at `ai.agent.invoke`, `ai.tool.invoke`, and `ai.llm.invoke`
- attach composite version identities for engine, procedures or skills, and plugins
- carry those version identities through traces, memory objects, writebacks, and promoted procedures
- keep replay and drift analysis anchored on those spans and version payloads

Status:
Core implementation is now present in contracts, engine traces, writebacks, memory objects, promotion artifacts, and run manifests; deeper replay analytics and drift tooling still need to mature.

### Workstream 9: Artifact completeness

Objective:
Ensure every run emits enough durable information for replay, debugging, and learning.

Concrete tasks:
- maintain `meta.json`
- maintain `eventlog.jsonl`
- maintain `trace.jsonl`
- maintain `memory.jsonl`
- maintain `writeback.json`
- maintain `promotion.json`

Status:
`writeback.json` and `promotion.json` now land per run; follow-up work is mostly around richer artifact semantics rather than missing files.

## Gap Analysis

### Already aligned with the architecture

- one canonical orchestrator
- DSPy-oriented reasoning path
- tag-centered planning and routing
- memory substrate with fallback path
- replay-oriented artifacts
- bounded tool execution boundary
- artifact directory surfaced to operators
- explicit enrichment provenance
- explicit promotion artifact persistence
- interpreter execution routed through the tool boundary

### Not yet fully aligned

- richer specialization plugin lifecycle and isolation
- deeper multi-model role selection policy
- fully explicit small-agent contracts
- immediate MicroVM-backed execution implementation for real code paths
- MCP-backed tooling fully expressed as the first-class protocol surface under the gateway
- nested observability spans fully wired through execution paths
- composite version identities fully attached across runtime and promoted artifacts
- forward-fix migration and recovery policy fully reflected in operators and automation
- full replay-driven procedural promotion pipeline
- stronger interpreter side-effect modeling and replay semantics beyond the current sandboxed command path
- fully realized three-lane memory behavior across every system path

## Validation Plan

Recommended targeted validation in WSL:

```bash
source .venv/bin/activate
python -m unittest \
  tests.test_regressions_steps_2_5 \
  tests.test_regressions_steps_6_9 \
  tests.test_cli_smoke \
  tests.test_contracts \
  tests.test_eventlog \
  tests.test_memory_adapter \
  tests.test_router_smoke \
  tests.test_architecture_gap_fill \
  tests.test_open_interpreter_tool
```

Recommended full-suite pass:

```bash
source .venv/bin/activate
python -m unittest discover tests
```

## Definition of Done

The architecture plan is complete when the repository can demonstrate:

- one stable cognition core
- optional specialization without orchestration drift
- bounded small-agent execution
- tool execution behind a logged boundary
- durable replay-ready artifacts
- procedural promotion from repeated successful runs
- reduced LLM dependence on later similar tasks






