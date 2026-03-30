"""Retriever module enforcing limits and diversity rules."""

from typing import Any, Dict, List, Tuple

from src.contracts import MemoryBlock, QueryPlan, TagSet
from .scoring import score_block


class Retriever:
    """A synchronous retriever implementation enforcing diverse scoring."""
    
    def __init__(self, memory_blocks: List[MemoryBlock], config_enabled: bool = False):
        self.memory_blocks = memory_blocks
        self.config_enabled = config_enabled
        
    def retrieve(
        self, query_tags: TagSet, plan: QueryPlan
    ) -> Tuple[List[MemoryBlock], Dict[str, Any]]:
        """
        Runs scoring against all blocks, enforces constraints from the QueryPlan,
        and returns the top-k results paired with an explicit explanation format.
        """
        scored = []
        for block in self.memory_blocks:
            score_info = score_block(block, query_tags, plan)
            if score_info["total"] > 0:
                scored.append((score_info["total"], score_info, block))
                
        # Sort purely by explicit total score, descending
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Enforce diversity and limits
        final_list = []
        seen_sources = set()
        diversity_rules = plan.diversity_rules
        
        for total, info, block in scored:
            # Constraint: diverse trusted sources representation
            if "unique_sources" in diversity_rules:
                source = block.provenance.get("source")
                if source and source in seen_sources:
                    continue  # skip if we already have this source
                if source:
                    seen_sources.add(str(source))
                    
            final_list.append((total, info, block))
            if len(final_list) >= plan.limits:
                break
                
        # Extract matching blocks
        results = [item[2] for item in final_list]
        
        # Apply Rust substitute if enabled
        if self.config_enabled:
            from src.rust_wrappers.ranker import RustRankerWrapper
            ranker = RustRankerWrapper(config_enabled=True)
            query_str = " ".join([str(v) for k,v in query_tags.tags.items()])
            results = ranker.rank(results, query_str)
        explanation = {
            "k_requested": plan.limits,
            "k_returned": len(results),
            "scores": [
                {
                    "id": item[2].id, 
                    "score": item[0], 
                    "components": item[1]["components"], 
                    "matched_tags": item[1]["matched_tags"]
                } for item in final_list
            ],
            "diversity_hits": list(seen_sources),
            "expansion_applied": plan.expansion_rules
        }
        
        return results, explanation
