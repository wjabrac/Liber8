# LIBR8 Architecture

## Purpose

LIBR8 is a central cognition system built around a stable cognition core. The core remains the primary driver of planning, recall, retrieval, enrichment selection, routing, evaluation, replay, and procedural promotion. Optional specialization plugins can attach for bounded task-specific enrichment, but they do not replace the cognition core.

## Fixed Architectural Defaults

The active defaults are now:

- `CognitionEngine` is the only canonical orchestrator.
- Production shape is a long-running service/API on Linux.
- The CLI remains an operator surface, not the production runtime shape.
- DSPy plus tags plus memory plus replay plus promotion remain the intelligence center.
- Specialization plugins are optional enrichers.
- Small agents are bounded workers chosen by the cognition core.
- Tool execution stays behind `ExecutionGateway`, with MCP first underneath it.
- Open Interpreter remains a bounded executor behind the gateway.
- Mutation-capable execution paths require a VM-backed isolation boundary at launch.
- PostgreSQL is the operational control database, not the cognition memory database.
- Internal telemetry remains primary; external telemetry is egress only.

## System Layers

### Cognition Core

Responsible for task intake, tag extraction, query planning, retrieval, routing, synthesis, evaluation, writeback, persistence, replay, and self-improvement.

### Specialization Plugins

Optional repo-internal attachments that contribute role-specific context, heuristics, or shaping without displacing the core.

### Service/API Layer

Provides the long-running runtime surface, health/readiness endpoints, operational state handling, retention visibility, and deployment-facing entrypoints.

### Execution Boundary

`ExecutionGateway` is the policy and audit layer. MCP-backed tooling is immediate beneath it. Real model-generated or mutation-capable execution must flow through a VM-backed isolation adapter.

### Operational State

Operational state is distinct from cognition memory. PostgreSQL is intended for registries, approvals, queues, artifact indexing, and service-side metadata, while cognition memory remains in the engine's own memory substrate and artifacts.

## Runtime Flow

1. task intake
2. tag extraction
3. query planning
4. retrieval and memory recall
5. enrichment and routing decisions
6. bounded agent or tool execution where needed
7. synthesis and evaluation
8. writeback and persistence
9. replay and promotion preparation

## Current Implementation Direction

The repository currently includes:

- the canonical cognition engine
- replay and markdown export tooling
- a service/API wrapper with health and run endpoints
- retention planning primitives
- structured JSON logging helpers
- operational state-store contracts and initial PostgreSQL schema seeds
- gateway hooks for isolation-required mutation paths

The remaining production work is implementation hardening rather than architectural uncertainty: VM-backed execution, Linux packaging, PostgreSQL-backed state-store implementation, secrets handling, and full integration verification.
