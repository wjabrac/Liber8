# AG-002 — Tag schema v0.1 (semantic coordinates)

Goal
Define a robust, versioned TagSet schema for Liber8 that enables sparse semantic coordinates (tags) to replace heavy embeddings for many operations.

Inputs
- spec/tag_schema_v0.md
- src/contracts.py (TagSet fields and validation)
- AG_EXTRACT/analysis/memory_primitives.md and orchestration_primitives.md (if present)
- work_orders/antigravity/001_contracts.md (context)

Deliverable
- spec/tag_schema_v0_1.md

Non-negotiables
- This is a spec document only. Do not edit code.
- Prefer precision and implementability over prose.
- Every field must have: type, constraints, normalization rules, and examples.

Required schema elements (minimum)
1) versioning
- schema_version string format (example: v0.1)
- migration notes from v0 to v0.1
- compatibility rules (forward/backward)

2) canonical tag keys
Define canonical keys and allow extensibility:
- domain: string
- action: string
- target: string
- tool: string (optional)
- resource: string (optional)
- artifact_type: string (optional)
- lane: episodic|semantic|procedural (optional for tags, mandatory for MemoryBlock)
- certainty: number 0..1 (must be representable and usable for routing)

3) value constraints
- permitted types per key (string, number, boolean, small enums)
- max length and allowed characters for strings
- normalization (case folding, whitespace, separators)
- synonym policy (how synonyms are represented without exploding tag space)

4) uncertainty representation
- define uncertainty object schema
- per-key vs per-tag uncertainty rules
- numeric range rules (0..1)
- what uncertainty means (confidence vs probability vs classifier score)

5) examples
Provide at least 6 realistic examples spanning:
- web_dev debug react high complexity forward directionality
- legal analysis evidence extraction
- tool execution with safety gating
- memory promotion candidate
- retrieval query with recency bias

Acceptance criteria
- Another developer can implement TagSet validation strictly from this spec without guessing.
- The spec includes a "Field Table" listing each key and its rules.
- The spec includes a "Normalization Rules" section and a "Migration v0 -> v0.1" section.

Do-not-do
- Do not propose switching to vectors or external ontologies.
- Do not introduce dependencies on proprietary services.
