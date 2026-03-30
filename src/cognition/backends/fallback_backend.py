"""Deterministic Fallback Backend.
Used when DSPy and Zep are unavailable or deactivated.
This serves as the deterministic, rule-based loop without requiring 'fake' LLM stubs.
"""

import json
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from src.contracts import TagSet, QueryPlan, MemoryBlock, WritebackPackage
from src.cognition.interfaces import TagExtractor, QueryPlanner, RouterPolicyProvider, Synthesizer, Evaluator, MemoryStore
from src.memory_adapter import FileSystemMemoryAdapter

class FallbackTagExtractor(TagExtractor):
    def extract(self, task: str) -> TagSet:
        return TagSet(
            schema_version="v0", 
            tags={"intent": "fallback_inference", "length": len(task)}, 
            uncertainty={"intent": 0.0}
        )

class FallbackQueryPlanner(QueryPlanner):
    def plan(self, tags: TagSet) -> QueryPlan:
        return QueryPlan(
            filters={"tags": tags.tags}, limits=5, recency_bias=0.5,
            diversity_rules=["unique_sources"], expansion_rules=["synonyms"],
            scoring_knobs={"freshness": 0.3, "relevance": 0.7}
        )

class FallbackRouter(RouterPolicyProvider):
    def route(self, task: str, tags: TagSet, query_plan: QueryPlan, retrieved: List[MemoryBlock]) -> Tuple[List[str], str, List[Dict[str, Any]], float]:
        return ["synthesizer"], "fallback_rule_based", [{"step": "synthesize", "agent": "synthesizer"}], 1.0

class FallbackSynthesizer(Synthesizer):
    def synthesize(self, task: str, tags: TagSet, retrieved: List[MemoryBlock], tool_results: List[Dict[str, Any]]) -> str:
        res = f"FALLBACK SYNTHESIS: Executed task '{task}'. "
        res += f"Retrieved {len(retrieved)} background contexts. "
        res += f"Tool outputs: {len(tool_results)}."
        return res

class FallbackEvaluator(Evaluator):
    def evaluate(self, task: str, synthesis: str, tags: TagSet) -> WritebackPackage:
        return WritebackPackage(
            episode=synthesis, distilled_facts=[task], tags=tags, evaluation_outcome="ok",
        )

class FallbackMemoryStore(MemoryStore):
    def __init__(self, path: Path):
        self.adapter = FileSystemMemoryAdapter(path)
        
    def read(self, tags: TagSet, plan: QueryPlan) -> List[MemoryBlock]:
        return self.adapter.read(tags, plan)

    def write(self, block: MemoryBlock) -> None:
        self.adapter.write(block)
