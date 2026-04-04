"""Deterministic Fallback Backend.
Used when DSPy and Zep are unavailable or deactivated.
This serves as the deterministic, rule-based loop without requiring 'fake' LLM stubs.
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.contracts import SCHEMA_VERSION, MemoryBlock, QueryPlan, TagSet, WritebackPackage
from src.cognition.interfaces import Evaluator, MemoryStore, QueryPlanner, RouterPolicyProvider, Synthesizer, TagExtractor
from src.memory_adapter import FileSystemMemoryAdapter


class FallbackTagExtractor(TagExtractor):
    def extract(self, task: str) -> TagSet:
        lowered = task.lower()
        intent = "fallback_inference"
        if any(word in lowered for word in ("code", "debug", "patch", "python", "program", "refactor")):
            intent = "programming"
        elif any(word in lowered for word in ("research", "investigate", "compare")):
            intent = "research"
        elif any(word in lowered for word in ("plan", "strategy", "sequence")):
            intent = "planning"
        return TagSet(
            schema_version=SCHEMA_VERSION,
            tags={"intent": intent, "length": len(task)},
            uncertainty={"intent": 0.0},
        )


class FallbackQueryPlanner(QueryPlanner):
    def plan(self, tags: TagSet) -> QueryPlan:
        lane_filters = ["semantic", "episodic"]
        if tags.tags.get("intent") == "programming":
            lane_filters.append("procedural")
        return QueryPlan(
            filters={"tags": tags.tags, "lanes": lane_filters}, limits=5, recency_bias=0.5,
            diversity_rules=["unique_sources"], expansion_rules=["synonyms"],
            scoring_knobs={"freshness": 0.3, "relevance": 0.7},
        )


class FallbackRouter(RouterPolicyProvider):
    def route(self, task: str, tags: TagSet, query_plan: QueryPlan, retrieved: List[MemoryBlock]) -> Tuple[List[str], str, List[Dict[str, Any]], float]:
        intent = str(tags.tags.get("intent", "fallback_inference"))
        if intent == "programming":
            return ["interpreter", "synthesizer"], "fallback_programming_route", [{"step": "execute", "agent": "interpreter"}, {"step": "synthesize", "agent": "synthesizer"}], 0.95
        if intent == "research":
            return ["researcher", "critic", "synthesizer"], "fallback_research_route", [{"step": "research", "agent": "researcher"}, {"step": "critique", "agent": "critic"}, {"step": "synthesize", "agent": "synthesizer"}], 0.9
        return ["synthesizer"], "fallback_rule_based", [{"step": "synthesize", "agent": "synthesizer"}], 1.0


class FallbackSynthesizer(Synthesizer):
    def synthesize(self, task: str, tags: TagSet, retrieved: List[MemoryBlock], tool_results: List[Dict[str, Any]]) -> str:
        res = f"FALLBACK SYNTHESIS: Executed task '{task}'. "
        res += f"Retrieved {len(retrieved)} background contexts. "
        res += f"Tool outputs: {len(tool_results)}."
        return res


class FallbackEvaluator(Evaluator):
    def evaluate(self, task: str, synthesis: str, tags: TagSet) -> WritebackPackage:
        lowered = task.lower()
        procedural_snippet = None
        promotion_notes = "stored in episodic and semantic lanes"
        if any(word in lowered for word in ("repeat", "routine", "procedure", "automation", "how")):
            procedural_snippet = f"Procedure for task: {task}"
            promotion_notes = "stored in episodic, semantic, and procedural lanes"
        return WritebackPackage(
            episode=synthesis,
            distilled_facts=[task, synthesis[:80]],
            procedural_snippet=procedural_snippet,
            tags=tags,
            evaluation_outcome="ok",
            promotion_notes=promotion_notes,
            demotion_notes=None,
        )


class FallbackMemoryStore(MemoryStore):
    def __init__(self, path: Path):
        self.adapter = FileSystemMemoryAdapter(path)

    def read(self, tags: TagSet, plan: QueryPlan) -> List[MemoryBlock]:
        return self.adapter.read(tags, plan)

    def write(self, block: MemoryBlock) -> None:
        self.adapter.write(block)

