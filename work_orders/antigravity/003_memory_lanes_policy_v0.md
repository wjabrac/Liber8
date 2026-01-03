# AG-003 — Memory lanes and promotion/demotion policy v0

Goal
Define how Liber8 stores and evolves memory across lanes (episodic, semantic, procedural) and how tasks move from heavy reasoning to lightweight heuristics to pro forma execution.

Inputs
- spec/contracts_v0.md (or current)
- src/contracts.py (MemoryBlock and WritebackPackage)
- AG_EXTRACT/analysis/memory_primitives.md and resilience_primitives.md (if present)
- The "three-tier" concept already discussed in project notes

Deliverable
- spec/memory_lanes_policy_v0.md

Required sections
1) lane definitions
- episodic: time-bound, traceable context with provenance
- semantic: distilled durable facts and stable mappings
- procedural: reusable steps, scripts, decision rules

2) write requirements per lane
For each lane, specify required fields for MemoryBlock.provenance, TagSet keys that should be present, and confidence thresholds.

3) promotion triggers
Define triggers that promote content:
- Tier 3 to Tier 2 (heavy to heuristic): repeated success with similar tags; validator ok; low variance outputs
- Tier 2 to Tier 1 (heuristic to pro forma): stable deterministic steps; minimal need for model calls; explicit preconditions
For each trigger, define required evidence recorded in EventRecord (fields to check).

4) demotion and invalidation triggers
Define when promoted knowledge is demoted or invalidated:
- validator failures
- environment drift
- contradicting newer evidence
- low confidence tags

5) retention and expiry
- recommended retention windows for episodic blocks
- garbage collection conditions
- what "valid_until" means and how it is set

6) retrieval prioritization rules
- lane ordering default
- recency bias behavior
- diversity rules
- minimum viable scoring knobs

Acceptance criteria
- Policy is implementable using only existing contract fields, or explicitly calls out new fields needed (and why).
- Includes at least 3 concrete promotion and 3 demotion examples with tags and outcomes.
- No architectural redesign sections.

Do-not-do
- Do not require external databases or heavy infrastructure.
- Do not require Docker.
