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
