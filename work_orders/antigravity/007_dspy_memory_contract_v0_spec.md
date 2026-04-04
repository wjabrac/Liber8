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
