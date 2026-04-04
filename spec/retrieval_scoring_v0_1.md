# Retrieval Scoring v0.1 (spec anchor)

Objective: tag-first retrieval (no vectors required) with explainable scoring and bounded expansion/diversity rules.

Score components (normalized to 0..1 then combined):
- tag_overlap: weighted overlap between query TagSet and MemoryBlock TagSet
- recency: decay function over created_at/updated_at
- lane_bonus: optional lane preference (episodic/semantic/procedural) based on query intent
- provenance_bonus: optional preference for trusted sources
- penalty terms: low confidence blocks, expired valid_until

Required outputs:
- for each candidate: {id, score, components:{tag_overlap, recency, lane_bonus, ...}, matched_tags:[...]}
- explanation payload stored in EventRecord.provenance and/or PerformanceTrace.retrieval_stats

Constraints:
- diversity rules: enforce configurable uniqueness (e.g., unique_sources)
- expansion rules: bounded expansions (synonyms/hierarchy) with hard caps and trace logging

Acceptance criteria:
- Retriever returns top-k results with explanation payload.
- Diversity/expansion behavior is observable in traces.
