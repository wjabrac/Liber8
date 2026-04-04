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
