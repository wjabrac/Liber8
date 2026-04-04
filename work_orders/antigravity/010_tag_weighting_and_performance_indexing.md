# AG-010 Tag weighting + performance indexing (nerve center)

Deliverable
A markdown spec that defines:
- how tags get weights (static priors + learned adjustments)
- how performance traces aggregate by tag clusters
- how failure patterns are detected by tags
- how efficacy is computed for a strategy keyed by tags

Constraints
- Must be implementable without vectors.
- Must not assume a particular DSPy optimizer; define signals generically.

Acceptance criteria
- Includes a minimal aggregation report schema.
