# CX-011 Writeback lanes policy v0.1 (episodic/semantic/procedural)

Objective
Implement lane selection, TTL/valid_until, and writeback packaging. Store promotion/demotion decisions in trace.

Scope
- Implement src/memory/policy.py with lane selection rules
- Update writeback path to set MemoryBlock.lane and valid_until
- Ensure WritebackPackage is written into EventRecord.provenance.writeback

Acceptance criteria
- Every successful run writes at least one MemoryBlock with lane populated
- TTL rules are enforced (expired blocks excluded from retrieval)
- Promotion/demotion notes are present in writeback package

Tests
- Unit tests for TTL exclusion and lane decisions.
