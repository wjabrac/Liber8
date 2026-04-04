# CX-009 Tag-first retrieval scoring + explanations

Objective
Implement tag-first retrieval scoring per spec/retrieval_scoring_v0_1.md and ensure explanations are emitted into trace/provenance.

Scope
- Implement src/retrieval/scoring.py and src/retrieval/retriever.py
- Support diversity rules and bounded expansion rules
- Return top-k with explanation payload

Acceptance criteria
- Retriever returns list[MemoryBlock] and a parallel explanation object
- Explanations stored in PerformanceTrace.retrieval_stats and/or EventRecord.provenance
- Expansion/diversity decisions are visible in trace

Tests
- Unit tests for scoring determinism, diversity enforcement, and expansion caps.
