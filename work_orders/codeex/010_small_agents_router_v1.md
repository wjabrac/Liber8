# CX-010 Small-agents router v1 with decision logging

Objective
Implement a router that decomposes tasks into a sequence of small agents using TagSet features. Must log candidates, decision features, and rationale into PerformanceTrace.

Scope
- Add src/agents/base.py (Agent interface)
- Add src/router/router.py (select agents, sequence)
- Stub agents: TaggerAgent, QueryPlannerAgent, RetrieverAgent, SynthesizerAgent, WritebackAgent
- Router emits decision_points entries with candidates considered and chosen agent(s)

Acceptance criteria
- Running engine produces a trace where routing is explicit and auditable
- Router policy is data-driven (table/rules) and easy to swap later by DSPy

Tests
- Unit test that router emits decision log and returns a stable sequence in fake mode.
