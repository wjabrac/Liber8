# LIBR8

LIBR8 is a central cognition system organized around one stable cognition core.

The core remains the primary driver of thought, planning, memory recall, retrieval, enrichment selection, routing, evaluation, replay, and self-improvement. Optional specialization plugins may attach to a run, but they do not replace the core.

## Primary Documents

- [Architecture](/home/willux/LIBR8_WORKSPACE/LIBR8/docs/architecture.md)
- [Implementation Plan](/home/willux/LIBR8_WORKSPACE/LIBR8/docs/implementation_plan.md)
- [Decision Log](/home/willux/LIBR8_WORKSPACE/LIBR8/docs/decision_log.md)
- [Environment](/home/willux/LIBR8_WORKSPACE/LIBR8/ENVIRONMENT.md)
- [Production Readiness](/home/willux/LIBR8_WORKSPACE/LIBR8/docs/production_readiness.md)
- [Service API](/home/willux/LIBR8_WORKSPACE/LIBR8/docs/service_api.md)
- [Deployment](/home/willux/LIBR8_WORKSPACE/LIBR8/docs/deployment.md)
- [Secrets and Config](/home/willux/LIBR8_WORKSPACE/LIBR8/docs/secrets_and_config.md)
- [Release and Rollback](/home/willux/LIBR8_WORKSPACE/LIBR8/docs/release_and_rollback.md)
- [Database Ops](/home/willux/LIBR8_WORKSPACE/LIBR8/docs/database_ops.md)

## Current Architectural Rule

- `CognitionEngine` is the canonical orchestrator.
- DSPy and tag-centered reasoning remain central to cognition.
- Memory, replay, and procedural promotion are core functions.
- Specialization plugins are optional attachments.
- Small agents are bounded workers chosen by the cognition core.
- Tool execution sits behind `ExecutionGateway`, with MCP as the first-class tool protocol.
- Real model-generated and mutation-capable execution paths move straight to MicroVM-backed isolation.
- Operational service state is additive and distinct from cognition memory.
- Observability includes nested spans and composite version identities, not only flat run artifacts.

## Runtime Shape

Production is a long-running service/API on Linux. The CLI remains an operator surface for local runs, replay, export, and maintenance.

A standard run flows through:

1. task intake
2. tag extraction
3. query planning
4. retrieval and memory recall
5. enrichment and routing decisions
6. bounded agent or tool execution where needed
7. synthesis and evaluation
8. writeback and persistence
9. replay and promotion preparation

## Repository Map

- `src/cognition/`: canonical cognition engine and backend configuration.
- `src/service/`: service/API wrapper, transport, and state-store contracts.
- `src/contracts/`: schema, serialization, validation, and migration.
- `src/failures/`: failure classification and retry policy.
- `src/tools/`: tool gateway, policy, registry, and path controls.
- `src/ops/`: retention and operational logging helpers.
- `src/retrieval/`: retrieval and ranking.
- `src/replay/`: replay and aggregation.
- `tests/`: smoke, contract, engine, gateway, service, and regression coverage.
- `sql/postgres/`: operational control-plane schema seeds.
- `docs/`: architecture and planning notes.

## Current State

The repository is now moving beyond a code-only production candidate. It includes a service/API wrapper, retention planning primitives, operational state-store contracts, and export/replay tooling, but it still needs a real production isolation backend, Linux deployment packaging, and end-to-end service verification before launch.


