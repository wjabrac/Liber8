# Production Readiness

## Current Position

LIBR8 is in an internal production-candidate state for its code architecture and control-plane shape, but not yet at final launch readiness.

Current implemented position:

- the canonical orchestrator is `CognitionEngine`
- the production target is a long-running service/API, with CLI retained as an operator surface
- retry-policy actions are implemented in the engine
- schema emission is aligned on one version
- path allowlists use resolved containment checks
- MCP-backed tooling is a first-class part of the execution boundary
- mutation-capable tool paths can be marked as isolation-required at the gateway boundary
- run artifacts include `meta.json`, `eventlog.jsonl`, `trace.jsonl`, `memory.jsonl`, `writeback.json`, `promotion.json`, and `run_manifest.json`
- replay and markdown export exist for operator inspection
- observability includes nested execution spans at `ai.agent.invoke`, `ai.tool.invoke`, and `ai.llm.invoke`
- composite version payloads are emitted across traces, memory objects, writebacks, promotion artifacts, events, and run manifests
- an initial service/API wrapper exposes `/healthz`, `/readyz`, `/retention/preview`, and `/v1/runs`
- an initial PostgreSQL schema seed exists for service-side operational state

This is not the same as final production readiness. The remaining work is primarily isolation, deployment, verification, and operational hardening.

## Readiness Checklist

### Code and Contracts

- [x] Canonical orchestrator is singular and stable.
- [x] Compatibility router delegates into the engine.
- [x] Retry-policy actions are implemented and covered by tests.
- [x] Event and memory schema versions are aligned.
- [x] Upcast occurs only on read and replay boundaries.
- [x] Composite versioning is emitted across engine, traces, writebacks, memory objects, promoted artifacts, and run manifests.

### Execution Safety

- [x] Tool execution is routed through `ExecutionGateway`.
- [x] MCP-backed tooling is immediate under the gateway.
- [x] Filesystem policy uses resolved containment instead of path-prefix matching.
- [x] Mutation-capable tools can be marked as isolation-required by policy.
- [ ] A real Linux-production MicroVM boundary is not yet implemented.
- [ ] Hyper-V-backed local execution remains a design direction, not a finished adapter.
- [ ] Destructive-command policy still needs broader adversarial validation.

### Artifacts and Replay

- [x] Each run emits a replayable artifact set.
- [x] Each run prints its exact artifact directory.
- [x] Each run emits `run_manifest.json` for operators and automation.
- [x] Basic artifact retention cleanup is available through `python -m src.cli prune-runs`.
- [x] Markdown export exists through `python -m src.cli export`.
- [ ] Replay-to-promotion automation remains incomplete.

### Service and Operations

- [x] Service/API wrapper exists.
- [x] Health and readiness endpoints exist.
- [x] Service-side operational state contracts exist.
- [x] Initial PostgreSQL schema seed exists for runs, approvals, registries, and artifact index.
- [x] Structured JSON logging helpers exist.
- [ ] Linux service packaging and supervision are not yet encoded.
- [ ] Secrets and deployment config management are not documented end to end.
- [ ] Rollback and release procedures are not yet encoded.
- [ ] Multi-process service verification and soak testing are still needed.

### Testing

- [x] Current WSL test anchor has been the validated local baseline.
- [x] Regressions cover the major refactor surfaces already completed.
- [x] CI is configured to run unittest discovery.
- [x] Focused service and retention tests now exist in the repository.
- [ ] Full service-path execution is not verified in this shell environment.
- [ ] Integration and soak tests with representative workloads are still needed.
- [ ] Sandbox escape attempts should be expanded into a larger adversarial test set.

## Recommended Next Steps

1. Implement the actual VM-backed execution adapter for mutation-capable tool paths.
2. Package the service for Linux supervision and define deployment-facing health expectations.
3. Add a real PostgreSQL-backed state store implementation behind the current service-state protocol.
4. Document secrets injection, release, rollback, and operator procedures.
5. Run integration and soak tests through the service/API path using representative workloads.
6. Expand adversarial execution-boundary tests.

## Operator Commands

Local readiness check:

```bash
python -m src.cli healthcheck --storage-dir .storage --backend fallback
```

Service readiness check:

```bash
python -m src.cli service-health --storage-dir .storage --backend fallback
```

Run retention preview:

```bash
python -m src.cli prune-runs --storage-dir .storage --keep 20 --dry-run --max-age-days 30
```

Start the service locally:

```bash
python -m src.cli serve --host 127.0.0.1 --port 8080 --storage-dir .storage --backend fallback
```
