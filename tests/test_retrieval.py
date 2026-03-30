import unittest
from datetime import datetime, timezone, timedelta
from src.contracts import MemoryBlock, TagSet, QueryPlan
from src.retrieval.retriever import Retriever

class TestRetrievalScoring(unittest.TestCase):
    def test_diversity_and_overlap_scoring(self):
        query_tags = TagSet("v0", {"topic": "ai", "domain": "software"})
        plan = QueryPlan(
            filters={},
            limits=2,
            recency_bias=0.5,
            diversity_rules=["unique_sources"],
            expansion_rules=["synonyms"],
            scoring_knobs={"freshness": 0.5, "relevance": 0.5}
        )
        
        # Block 1: Perfect overlap, trusted source A
        b1 = MemoryBlock(
            content="AI in software",
            tags=TagSet("v0", {"topic": "ai", "domain": "software"}),
            provenance={"source": "Source_A", "trusted": True},
            lane="semantic",
            confidence=0.9
        )
        
        # Block 2: Perfect overlap, trusted source A (should be filtered by diversity)
        b2 = MemoryBlock(
            content="AI in software 2",
            tags=TagSet("v0", {"topic": "ai", "domain": "software"}),
            provenance={"source": "Source_A", "trusted": True},
            lane="semantic",
            confidence=0.9
        )
        
        # Block 3: Partial overlap, source B
        b3 = MemoryBlock(
            content="AI in hardware",
            tags=TagSet("v0", {"topic": "ai", "domain": "hardware"}),
            provenance={"source": "Source_B"},
            lane="semantic",
            confidence=0.9
        )
        
        retriever = Retriever([b1, b2, b3])
        results, explanation = retriever.retrieve(query_tags, plan)
        
        # Should return exactly 2 items due to limit
        self.assertEqual(len(results), 2)
        
        # Should drop b2 due to diversity "unique_sources" rule since b1 scored higher/first and has "Source_A"
        # Wait, b1 and b2 have exact same recency and overlap, they score equally.
        # But b3 has a different source. So final should be b1 (or b2) and b3.
        self_ids = {r.id for r in results}
        self.assertIn(b3.id, self_ids)
        
        # Check explanation
        self.assertEqual(explanation["k_returned"], 2)
        self.assertEqual(len(explanation["diversity_hits"]), 2)

if __name__ == "__main__":
    unittest.main()
