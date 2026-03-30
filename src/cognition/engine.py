"""Cognition Engine the primary execution spine for LIBR8."""

from __future__ import annotations

import json
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from src.contracts import EventRecord, QueryPlan, MemoryBlock, WritebackPackage, TagSet
from src.contracts.validators import (
    validate_tagset, validate_queryplan, validate_memoryblock, 
    validate_writeback, validate_eventrecord
)
from src.trace import PerformanceTrace, DecisionPoint, ProvenanceInfo, TraceLog, RetrievalStats
from src.eventlog import EventLog
from src.runs.session import write_meta
from src.runs.state import RunState
from src.retrieval.retriever import Retriever  # For ranking
from .config import EngineConfig

from src.tools.gateway import ExecutionGateway
from src.tools.registry import ToolRegistry
from src.tools.policy import ToolPolicy
from src.tools.contracts import ToolRequest
from src.failures.classifier import FailureClassifier
from src.failures.retry import RetryPolicyEngine
from src.tools.standard import register_standard_tools

from src.cognition.backends.dspy_backend import DSPyTagExtractor, DSPyQueryPlanner, DSPyRouter, DSPySynthesizer, DSPyEvaluator
from src.cognition.backends.fallback_backend import FallbackTagExtractor, FallbackQueryPlanner, FallbackRouter, FallbackSynthesizer, FallbackEvaluator, FallbackMemoryStore
from src.memory.backends.zep_backend import ZepMemoryStore


class CognitionEngine:
    """The main entrypoint and orchestrator for the cognition spine."""

    def __init__(self, config: EngineConfig):
        self.config = config
        
        if config.cognition_backend == "dspy+zep":
            self.tagger = DSPyTagExtractor()
            self.planner = DSPyQueryPlanner()
            self.router = DSPyRouter()
            self.synthesizer = DSPySynthesizer()
            self.evaluator = DSPyEvaluator()
        else:
            self.tagger = FallbackTagExtractor()
            self.planner = FallbackQueryPlanner()
            self.router = FallbackRouter()
            self.synthesizer = FallbackSynthesizer()
            self.evaluator = FallbackEvaluator()
            
        # Tools
        registry = ToolRegistry()
        register_standard_tools(registry)
        
        policy = ToolPolicy(
            mode=config.tool_policy_mode, 
            network_allowed=config.network_allowed, 
            path_allowlists=config.path_allowlists
        )
        self.gateway = ExecutionGateway(registry, policy)
        
        # Resilience
        self.classifier = FailureClassifier()
        self.retry_engine = RetryPolicyEngine(config)

    def run(self, task: str, run_dir: Path) -> EventRecord:
        """Executes a new cognitive spine cycle with durability."""
        run_dir = Path(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)
        
        state = RunState(task=task, status="running", current_step=1)
        state.save(run_dir)
        
        return self._execute_run(run_dir, state)

    def resume_run(self, run_dir: Path) -> EventRecord:
        """Resumes an interrupted engine spin from persistent state."""
        state = RunState.load(Path(run_dir))
        if state.status == "completed":
            raise RuntimeError("Cannot resume a completed run.")
        if state.status == "pending":
            state.status = "running"
            
        return self._execute_run(Path(run_dir), state)

    def _execute_run(self, run_dir: Path, state: RunState) -> EventRecord:
        run_id = run_dir.name
        
        meta = {
            "run_id": run_id,
            "engine_version": self.config.engine_version,
            "config_hash": self.config.config_hash,
            "cognition_backend": self.config.cognition_backend,
        }
        write_meta(run_dir, meta)
        
        if self.config.cognition_backend == "dspy+zep":
            try:
                memory_store = ZepMemoryStore(api_url="http://localhost:8000")
            except RuntimeError:
                memory_store = FallbackMemoryStore(run_dir / "memory.jsonl")
        else:
            memory_store = FallbackMemoryStore(run_dir / "memory.jsonl")
            
        trace_log = TraceLog(run_dir / "trace.jsonl")
        event_log = EventLog(run_dir / "eventlog.jsonl")
        
        final_failure_class = None
        
        while state.attempt <= self.config.retry_max_attempts and state.status == "running":
            try:
                # Step 1: Tagging
                if state.current_step == 1:
                    tags = self.tagger.extract(state.task)
                    validate_tagset(tags)
                    state.state_snapshot["tags"] = tags.to_dict()
                    dp = DecisionPoint("tag_extraction", {"task": state.task[:50]}, {"tags": tags.to_dict()})
                    state.state_snapshot["dp_1"] = dp.to_dict()
                    state.current_step = 2
                    state.save(run_dir)
                
                # Step 2: Planning
                if state.current_step == 2:
                    tags = TagSet.from_dict(state.state_snapshot["tags"])
                    query_plan = self.planner.plan(tags)
                    validate_queryplan(query_plan)
                    state.state_snapshot["query_plan"] = query_plan.to_dict()
                    dp = DecisionPoint("query_planning", {"tags": tags.to_dict()}, {"query_plan": query_plan.to_dict()})
                    state.state_snapshot["dp_2"] = dp.to_dict()
                    state.current_step = 3
                    state.save(run_dir)
                    
                # Step 3: Retrieval
                if state.current_step == 3:
                    tags = TagSet.from_dict(state.state_snapshot["tags"])
                    query_plan = QueryPlan.from_dict(state.state_snapshot["query_plan"])
                    candidates = memory_store.read(tags, query_plan)
                    
                    retriever = Retriever(
                        candidates, 
                        config_enabled=self.config.rust_acceleration_toggles.get("retrieval_ranking", False)
                    )
                    retrieved, ret_exp = retriever.retrieve(tags, query_plan)
                    
                    r_stats = RetrievalStats(
                        k_requested=ret_exp["k_requested"], k_returned=ret_exp["k_returned"],
                        scores=ret_exp["scores"], diversity_hits=ret_exp["diversity_hits"],
                        expansion_applied=ret_exp["expansion_applied"]
                    )
                    state.state_snapshot["retrieval_stats"] = r_stats.__dict__
                    state.state_snapshot["retrieved"] = [b.to_dict() for b in retrieved]
                    
                    dp = DecisionPoint("retrieval", {"candidates": len(candidates)}, {"retrieved_count": len(retrieved)})
                    state.state_snapshot["dp_3"] = dp.to_dict()
                    state.current_step = 4
                    state.save(run_dir)
                    
                # Step 4: Routing
                if state.current_step == 4:
                    tags = TagSet.from_dict(state.state_snapshot["tags"])
                    query_plan = QueryPlan.from_dict(state.state_snapshot["query_plan"])
                    retrieved = [MemoryBlock.from_dict(b) for b in state.state_snapshot["retrieved"]]
                    
                    agents, r_reason, decomp, router_conf = self.router.route(state.task, tags, query_plan, retrieved)
                    state.state_snapshot["selected_agents"] = agents
                    dp = DecisionPoint(
                        "routing", {"task": state.task[:50]}, 
                        {"agents": agents, "reason": r_reason, "confidence": router_conf}
                    )
                    state.state_snapshot["dp_4"] = dp.to_dict()
                    state.current_step = 5
                    state.state_snapshot["tool_calls"] = []
                    state.save(run_dir)
                    
                # Step 5: Execution (Tools)
                if state.current_step == 5:
                    agents = state.state_snapshot["selected_agents"]
                    tool_calls = state.state_snapshot.get("tool_calls", [])
                    
                    if "researcher" in agents and len(tool_calls) == 0:
                        from src.tools.contracts import ApprovalContext
                        ctx = ApprovalContext(approved_by="engine_policy", reason="default_research_phase")
                        req = ToolRequest("list_directory", {"path": "."})
                        res, dp = self.gateway.execute(req, ctx)
                        state.state_snapshot["dp_5"] = dp.to_dict()
                        state.state_snapshot["tool_calls"].append({
                            "tool_call_id": res.tool_call_id,
                            "name": req.name,
                            "status": res.status,
                            "duration_ms": res.duration_ms,
                            "error_class": res.error_class,
                            "output_summary": str(res.output)[:100] if res.output else None
                        })
                    
                    state.current_step = 6
                    state.save(run_dir)
                    
                # Step 6: Synthesis
                if state.current_step == 6:
                    tags = TagSet.from_dict(state.state_snapshot["tags"])
                    retrieved = [MemoryBlock.from_dict(b) for b in state.state_snapshot["retrieved"]]
                    tool_calls = state.state_snapshot.get("tool_calls", [])
                    
                    synthesis = self.synthesizer.synthesize(state.task, tags, retrieved, tool_calls)
                    state.state_snapshot["synthesis"] = synthesis
                    dp = DecisionPoint("synthesis", {"context_len": len(retrieved)}, {"result_preview": synthesis[:100]})
                    state.state_snapshot["dp_6"] = dp.to_dict()
                    state.current_step = 7
                    state.save(run_dir)
                    
                # Step 7: Writeback
                if state.current_step == 7:
                    tags = TagSet.from_dict(state.state_snapshot["tags"])
                    synthesis = state.state_snapshot["synthesis"]
                    
                    writeback = self.evaluator.evaluate(state.task, synthesis, tags)
                    validate_writeback(writeback)
                    state.state_snapshot["writeback"] = writeback.to_dict()
                    dp = DecisionPoint("writeback", {"synthesis_preview": synthesis[:10]}, {"evaluation": writeback.evaluation_outcome})
                    state.state_snapshot["dp_7"] = dp.to_dict()
                    state.current_step = 8
                    state.save(run_dir)
                    
                # Step 8: Persistence
                if state.current_step == 8:
                    synthesis = state.state_snapshot["synthesis"]
                    tags = TagSet.from_dict(state.state_snapshot["tags"])
                    
                    stable_id = hashlib.sha256(f"{run_dir.name}_{synthesis}".encode()).hexdigest()[:16]
                    memory_block = MemoryBlock(
                        id=f"mem_{stable_id}",
                        content=synthesis, tags=tags, provenance={"source": "cognition_engine"}, lane="episodic", confidence=0.8
                    )
                    validate_memoryblock(memory_block)
                    memory_store.write(memory_block)
                    
                    state.status = "completed"
                    state.save(run_dir)
                    break
                    
            except Exception as e:
                final_failure_class, ctx = self.classifier.classify(e)
                decision, retry_dp = self.retry_engine.evaluate(final_failure_class, state.attempt)
                state.state_snapshot[f"error_dp_{state.attempt}"] = retry_dp.to_dict()
                
                if decision == "exponential_backoff":
                    time.sleep(self.config.retry_backoff_base_sec ** state.attempt)
                    state.attempt += 1
                    state.save(run_dir)
                elif decision == "enter_degraded_mode":
                    state.status = "degraded"
                    if not isinstance(memory_store, FallbackMemoryStore):
                        memory_store = FallbackMemoryStore(run_dir / "memory_fallback.jsonl")
                        state.attempt += 1 # allow next cycle in degraded memory
                        state.save(run_dir)
                    else:
                        break
                else:
                    state.status = "failed"
                    state.save(run_dir)
                    break
                    
        # Trace reconstruction
        provenance = ProvenanceInfo(
            git_commit="", engine_version=self.config.engine_version,
            cognition_backend=self.config.cognition_backend, config_hash=self.config.config_hash
        )
        safe_tags = TagSet.from_dict(state.state_snapshot["tags"]) if "tags" in state.state_snapshot else TagSet("v0", {})
        query_plan = QueryPlan.from_dict(state.state_snapshot["query_plan"]) if "query_plan" in state.state_snapshot else QueryPlan({"tags":{}}, 0, 0.0)
        
        # reconstruct DP logs dynamically
        dps = []
        for i in range(1, 8):
            if f"dp_{i}" in state.state_snapshot:
                raw_dp = state.state_snapshot[f"dp_{i}"]
                dps.append(DecisionPoint(raw_dp["name"], raw_dp["inputs_summary"], raw_dp["choice"], rationale=raw_dp.get("rationale", ""), latency_ms=raw_dp.get("latency_ms", 0)))
                
        eval_outcome = state.state_snapshot.get("writeback", {}).get("evaluation_outcome", "error")
        retrieval_stats = RetrievalStats(**state.state_snapshot["retrieval_stats"]) if "retrieval_stats" in state.state_snapshot else None
        outcome_word = state.status if state.status in ["success", "completed", "failed", "degraded"] else "failure"
        if outcome_word == "completed": outcome_word = "success"
        if outcome_word == "failed": outcome_word = "failure"

        trace = PerformanceTrace(
            run_id=run_id, task=state.task, tags=safe_tags, decision_points=dps,
            outcome=outcome_word, evaluation_outcome=eval_outcome,
            validators=["contracts_v1_strict"], provenance=provenance,
            failure_class=final_failure_class.value if final_failure_class else None,
            retrieval_stats=retrieval_stats
        )
        trace_log.append(trace)
        
        event = EventRecord(
            task=state.task, tags=safe_tags, query_plan=query_plan,
            retrieved_ids=[b["id"] for b in state.state_snapshot.get("retrieved", [])], 
            actions=state.state_snapshot.get("selected_agents", []),
            tool_calls=state.state_snapshot.get("tool_calls", []), validations=["contracts_v1_strict"],
            outcome=outcome_word, failure_class=final_failure_class.value if final_failure_class else None,
            retries=state.attempt - 1, provenance={"trace_id": trace.trace_id, "backend": self.config.cognition_backend}
        )
        validate_eventrecord(event)
        event_log.append(event)
        
        return event

