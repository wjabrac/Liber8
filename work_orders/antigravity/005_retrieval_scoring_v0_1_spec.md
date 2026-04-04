# AG-005 Retrieval scoring v0.1 spec (tag-first, explainable)

Deliverable
A markdown spec that fully defines:
- scoring components and combination rule
- diversity enforcement semantics
- expansion semantics + hard caps (bounded and logged)
- required explanation payload structure (for traces)

Constraints
- No vectors required; tag-first is primary.
- Must be implementable as a pure function over TagSet + candidate TagSets + metadata.

Acceptance criteria
- Includes at least 5 edge cases (missing tags, expired blocks, low confidence, identical provenance, conflicts).
- Includes an example explanation payload.
