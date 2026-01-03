# contracts_v0.md

## EventRecord
Fields:
- id (string, UUID)
- timestamp (string, ISO-8601)
- task (string)
- tags (TagSet)
- query_plan (QueryPlan)
- retrieved_ids (list[string])
- actions (list[string])
- tool_calls (list[object], JSON-serializable)
- validations (list[string])
- outcome (string)
- failure_class (string|null)
- retries (int, >= 0)
- cost (number, >= 0)
- latency (number, >= 0)
- provenance (object, JSON-serializable)

Invariants:
- All fields are JSON-serializable.
- `tags` and `query_plan` must be valid v0 contracts.

## TagSet
Fields:
- schema_version (string)
- tags (object with string keys)
- uncertainty (object with string keys and float values 0..1, optional)

Invariants:
- keys in `tags` and `uncertainty` are strings.

## QueryPlan
Fields:
- filters (object with string keys)
- limits (int >= 0)
- recency_bias (number 0..1)
- diversity_rules (list[string])
- expansion_rules (list[string])
- scoring_knobs (object, JSON-serializable)

## MemoryBlock
Fields:
- id (string, UUID)
- content (string)
- tags (TagSet)
- provenance (object, JSON-serializable)
- lane (string: episodic|semantic|procedural)
- confidence (number 0..1)
- created_at (string, ISO-8601)
- updated_at (string, ISO-8601)
- valid_until (string, ISO-8601, optional)

## WritebackPackage
Fields:
- episode (string)
- distilled_facts (list[string])
- procedural_snippet (string|null)
- tags (TagSet)
- evaluation_outcome (string)
- promotion_notes (string|null)
- demotion_notes (string|null)
