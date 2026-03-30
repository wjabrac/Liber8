"""DSPy backend for LIBR8 Cognition Engine."""

import json
from typing import List, Tuple, Dict, Any

try:
    import dspy
    DSPY_AVAILABLE = True
except ImportError:
    DSPY_AVAILABLE = False

from src.contracts import TagSet, QueryPlan, MemoryBlock, WritebackPackage
from src.cognition.interfaces import TagExtractor, QueryPlanner, RouterPolicyProvider, Synthesizer, Evaluator

class DSPyTagExtractor(TagExtractor):
    def extract(self, task: str) -> TagSet:
        if not DSPY_AVAILABLE:
            raise RuntimeError("DSPy is not installed but dspy_backend is active.")
        
        # Define DSPy signature inline or use a precompiled one
        class TaggingSignature(dspy.Signature):
            """Extract intent and analytical tags from a raw user task."""
            task = dspy.InputField(desc="Raw user request")
            intent = dspy.OutputField(desc="Single word analytical intent (e.g. read, write, complex_query)")
            complexity = dspy.OutputField(desc="low, medium, or high")

        predictor = dspy.Predict(TaggingSignature)
        result = predictor(task=task)
        
        tags_dict = {
            "intent": result.intent, 
            "complexity": result.complexity,
            "provider": "dspy"
        }
        return TagSet(schema_version="v0", tags=tags_dict, uncertainty={"intent": 0.05})

class DSPyQueryPlanner(QueryPlanner):
    def plan(self, tags: TagSet) -> QueryPlan:
        # A real DSPy implementation would dynamically tune knobs based on tags.
        # For now, we return a strict deterministic baseline wired to the DSPy interface logic.
        return QueryPlan(
            filters={"tags": tags.tags}, limits=5, recency_bias=0.5,
            diversity_rules=["unique_sources"], expansion_rules=["synonyms"],
            scoring_knobs={"freshness": 0.3, "relevance": 0.7}
        )

class DSPyRouter(RouterPolicyProvider):
    def route(self, task: str, tags: TagSet, query_plan: QueryPlan, retrieved: List[MemoryBlock]) -> Tuple[List[str], str, List[Dict[str, Any]], float]:
        if not DSPY_AVAILABLE:
            raise RuntimeError("DSPy is not installed.")
            
        class RoutingSignature(dspy.Signature):
            """Determine downstream bounds and agents for a complex cognitive task."""
            task = dspy.InputField()
            intent = dspy.InputField()
            agents = dspy.OutputField(desc="Comma separated listed of generic worker agents, e.g. researcher, synthesizer")
            reason = dspy.OutputField(desc="Why this route was chosen")

        predictor = dspy.Predict(RoutingSignature)
        result = predictor(task=task, intent=tags.tags.get("intent", "default"))
        
        agents_list = [a.strip() for a in result.agents.split(",") if a.strip()]
        if not agents_list:
            agents_list = ["synthesizer"]
            
        decomposition = [{"step": "delegated_task", "agent": a} for a in agents_list]
        return agents_list, result.reason, decomposition, 0.85

class DSPySynthesizer(Synthesizer):
    def synthesize(self, task: str, tags: TagSet, retrieved: List[MemoryBlock], tool_results: List[Dict[str, Any]]) -> str:
        if not DSPY_AVAILABLE:
            raise RuntimeError("DSPy is not installed.")
            
        class SynthesisSignature(dspy.Signature):
            """Synthesize context and tool returns into a final output."""
            task = dspy.InputField()
            context = dspy.InputField(desc="Retrieved memory context")
            tools = dspy.InputField(desc="Tool execution outputs")
            synthesis = dspy.OutputField(desc="Final synthesized response")
            
        ctx_str = "\n".join([b.content for b in retrieved])
        tool_str = json.dumps(tool_results)
        
        predictor = dspy.Predict(SynthesisSignature)
        result = predictor(task=task, context=ctx_str, tools=tool_str)
        
        return result.synthesis

class DSPyEvaluator(Evaluator):
    def evaluate(self, task: str, synthesis: str, tags: TagSet) -> WritebackPackage:
        return WritebackPackage(
            episode=synthesis, distilled_facts=[task], tags=tags, evaluation_outcome="ok",
        )
