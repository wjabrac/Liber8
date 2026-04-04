"""Cognition Engine the primary execution spine for LIBR8."""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

from src.cognition.enrichment import select_enrichment
from src.contracts import SCHEMA_VERSION, EventRecord, MemoryBlock, QueryPlan, TagSet, WritebackPackage, _now_iso
from src.contracts.validators import (
    validate_eventrecord,
    validate_memoryblock,
    validate_queryplan,
    validate_tagset,
    validate_writeback,
)
from src.eventlog import EventLog
from src.failures.classifier import FailureClassifier
from src.failures.retry import RetryPolicyEngine
from src.execution.isolation import build_isolation_boundary
from src.memory.backends.zep_backend import ZEP_AVAILABLE, ZepMemoryStore
from src.plugins import PluginContext, PluginRegistry
from src.retrieval.retriever import Retriever
from src.runs.session import write_meta
from src.runs.state import RunState
from src.tools.contracts import ApprovalContext, ToolRequest
from src.tools.gateway import ExecutionGateway
from src.tools.policy import ToolPolicy
from src.tools.registry import ToolRegistry
from src.tools.standard import register_standard_tools
from src.trace import DecisionPoint, ExecutionSpan, PerformanceTrace, ProvenanceInfo, RetrievalStats, TraceLog

from .config import EngineConfig
from src.cognition.backends.dspy_backend import DSPyEvaluator, DSPyQueryPlanner, DSPyRouter, DSPySynthesizer, DSPyTagExtractor
from src.cognition.backends.fallback_backend import FallbackEvaluator, FallbackMemoryStore, FallbackQueryPlanner, FallbackRouter, FallbackSynthesizer, FallbackTagExtractor


class CognitionEngine:
    """The main entrypoint and orchestrator for the cognition spine."""

    def __init__(self, config: EngineConfig):
        self.config = config
        self.active_backend = config.cognition_backend
        self.memory_store = None
        self.plugin_registry = PluginRegistry()
        self._configure_backend(self.active_backend)

        registry = ToolRegistry()
        register_standard_tools(registry)
        policy = ToolPolicy(
            mode=config.tool_policy_mode,
            network_allowed=config.network_allowed,
            path_allowlists=config.path_allowlists,
            enforce_isolation_for_writes=config.enforce_isolation_for_writes,
        )
        isolation_boundary = build_isolation_boundary(config.execution_isolation_backend)
        self.gateway = ExecutionGateway(registry, policy, isolation_boundary=isolation_boundary)

        self.classifier = FailureClassifier()
        self.retry_engine = RetryPolicyEngine(config)

    def _configure_backend(self, backend: str) -> None:
        if (
            self.active_backend == backend
            and all(hasattr(self, attr) for attr in ("tagger", "planner", "router", "synthesizer", "evaluator"))
        ):
            return

        self.active_backend = backend
        if backend == "dspy+zep":
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

    def _initialize_memory_store(self, run_dir: Path, state: RunState):
        if state.state_snapshot.get("memory_backend") == "fallback" or self.active_backend != "dspy+zep" or not ZEP_AVAILABLE:
            self.memory_store = FallbackMemoryStore(run_dir / "memory.jsonl")
        else:
            self.memory_store = ZepMemoryStore(api_url="http://localhost:8000")
        return self.memory_store

    def _switch_to_fallback_backend(self, run_dir: Path, state: RunState) -> None:
        self._configure_backend("fallback")
        state.state_snapshot["active_backend"] = self.active_backend
        state.state_snapshot["degraded_mode"] = True
        state.state_snapshot["backend_tier_switched"] = True
        state.state_snapshot["memory_backend"] = "fallback"
        self.memory_store = FallbackMemoryStore(run_dir / "memory.jsonl")

    def _apply_retry_decision(self, decision: str, run_dir: Path, state: RunState, failure_context: Any) -> None:
        if decision == "exponential_backoff":
            time.sleep(self.config.retry_backoff_base_sec ** state.attempt)
            state.attempt += 1
            state.save(run_dir)
            return

        if decision == "retry_fixed":
            time.sleep(self.config.retry_backoff_base_sec)
            state.attempt += 1
            state.save(run_dir)
            return

        if decision == "switch_tool":
            state.state_snapshot["disable_tools"] = True
            state.state_snapshot["degraded_mode"] = True
            state.state_snapshot["tool_switch_context"] = failure_context
            state.state_snapshot["selected_agents"] = [agent for agent in state.state_snapshot.get("selected_agents", []) if agent not in {"researcher", "interpreter"}]
            state.current_step = min(state.current_step, 5)
            state.attempt += 1
            state.save(run_dir)
            return

        if decision == "ask_for_approval":
            state.state_snapshot["approval_required"] = failure_context
            state.state_snapshot["disable_tools"] = True
            state.state_snapshot["degraded_mode"] = True
            state.state_snapshot["selected_agents"] = [agent for agent in state.state_snapshot.get("selected_agents", []) if agent not in {"researcher", "interpreter"}]
            state.current_step = min(state.current_step, 5)
            state.attempt += 1
            state.save(run_dir)
            return

        if decision == "switch_tier":
            if self.active_backend != "fallback":
                self._switch_to_fallback_backend(run_dir, state)
                state.attempt += 1
                state.save(run_dir)
                return
            state.status = "failed"
            state.save(run_dir)
            return

        if decision == "enter_degraded_mode":
            state.state_snapshot["degraded_mode"] = True
            state.state_snapshot["memory_backend"] = "fallback"
            self.memory_store = FallbackMemoryStore(run_dir / "memory.jsonl")
            state.attempt += 1
            state.save(run_dir)
            return

        state.status = "failed"
        state.save(run_dir)

    def _select_role_models(self, plugin_roles: List[str]) -> Dict[str, str]:
        role_models = dict(self.config.role_model_policy)
        role_models.setdefault("planning", "dspy_planner" if self.active_backend == "dspy+zep" else "fallback_planner")
        role_models.setdefault("execution", "local_executor")
        for role in plugin_roles:
            role_models.setdefault(role, role_models.get(role, f"fallback_{role}"))
        return role_models

    def _merge_agent_preferences(self, agents: List[str], plugins: List[Dict[str, Any]]) -> List[str]:
        merged = list(agents)
        for plugin in plugins:
            for agent in plugin.get("preferred_agents", []):
                if agent not in merged:
                    merged.append(agent)
        return merged

    def _write_json_artifact(self, path: Path, payload: Dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def _build_interpreter_command(self, task: str) -> str:
        safe_task = " ".join(task.split())[:80]
        safe_task = safe_task.replace('"', "").replace("&", "and").replace("|", " ")
        return f"echo LIBR8 interpreter task: {safe_task}"

    def _version_info(self, state: RunState) -> Dict[str, str]:
        plugins = [plugin.get("name") for plugin in state.state_snapshot.get("plugins", []) if plugin.get("name")]
        plugin_version = "builtin_v1" if plugins else "none"
        procedure_version = "none"
        promotion = state.state_snapshot.get("promotion", {})
        if promotion.get("promoted"):
            procedure_version = f"generated:{state.state_snapshot.get('run_id', 'runtime')}"
        return {
            "core_engine": self.config.engine_version,
            "cognition_backend": self.active_backend,
            "plugin_set": plugin_version,
            "active_procedure": procedure_version,
        }

    def _ensure_span_root(self, state: RunState) -> str:
        root_id = state.state_snapshot.get("span_root_id")
        if root_id:
            return root_id
        root_id = str(uuid.uuid4())
        state.state_snapshot["span_root_id"] = root_id
        state.state_snapshot["span_root_started_at"] = _now_iso()
        state.state_snapshot.setdefault("execution_spans", [])
        return root_id

    def _record_span(self, state: RunState, name: str, status: str, attributes: Dict[str, Any], parent_span_id: str | None = None) -> None:
        root_id = self._ensure_span_root(state)
        state.state_snapshot.setdefault("execution_spans", []).append(
            {
                "name": name,
                "span_id": str(uuid.uuid4()),
                "parent_span_id": parent_span_id if parent_span_id is not None else root_id,
                "started_at": _now_iso(),
                "ended_at": _now_iso(),
                "status": status,
                "attributes": attributes,
            }
        )

    def _finalize_spans(self, state: RunState, outcome: str) -> List[ExecutionSpan]:
        root_id = self._ensure_span_root(state)
        span_payloads = list(state.state_snapshot.get("execution_spans", []))
        span_payloads.insert(
            0,
            {
                "name": "ai.agent.invoke",
                "span_id": root_id,
                "parent_span_id": None,
                "started_at": state.state_snapshot.get("span_root_started_at", _now_iso()),
                "ended_at": _now_iso(),
                "status": outcome,
                "attributes": {
                    "task": state.task,
                    "selected_agents": state.state_snapshot.get("selected_agents", []),
                    "plugins": [plugin.get("name") for plugin in state.state_snapshot.get("plugins", [])],
                },
            },
        )
        return [ExecutionSpan(**payload) for payload in span_payloads]

    def _build_promotion_artifact(self, task: str, tags: TagSet, writeback: Any, state: RunState) -> Dict[str, Any]:
        promoted = bool(writeback.procedural_snippet)
        version_info = self._version_info(state)
        return {
            "schema_version": "1.0",
            "version_info": version_info,
            "task": task,
            "tags": tags.to_dict(),
            "evaluation_outcome": writeback.evaluation_outcome,
            "promoted": promoted,
            "promotion_targets": ["procedural_memory"] if promoted else [],
            "procedural_snippet": writeback.procedural_snippet,
            "distilled_facts": list(writeback.distilled_facts),
            "plugins": [plugin.get("name") for plugin in state.state_snapshot.get("plugins", [])],
            "role_models": state.state_snapshot.get("role_models", {}),
        }

    def _build_run_manifest(self, run_dir: Path, state: RunState) -> Dict[str, Any]:
        artifact_paths = {
            "meta": str(run_dir / "meta.json"),
            "eventlog": str(run_dir / "eventlog.jsonl"),
            "trace": str(run_dir / "trace.jsonl"),
            "memory": str(run_dir / "memory.jsonl"),
            "writeback": str(run_dir / "writeback.json"),
            "promotion": str(run_dir / "promotion.json"),
            "run_state": str(run_dir / "run_state.json"),
            "run_manifest": str(run_dir / "run_manifest.json"),
        }
        version_info = self._version_info(state)
        return {
            "schema_version": SCHEMA_VERSION,
            "version_info": version_info,
            "run_id": run_dir.name,
            "status": state.status,
            "backend": self.active_backend,
            "degraded_mode": bool(state.state_snapshot.get("degraded_mode")),
            "artifacts": artifact_paths,
            "plugins": [plugin.get("name") for plugin in state.state_snapshot.get("plugins", [])],
            "role_models": state.state_snapshot.get("role_models", {}),
            "summary": {
                "outcome": "degraded" if state.state_snapshot.get("degraded_mode") else state.status,
                "retries": max(state.attempt - 1, 0),
                "tool_call_count": len(state.state_snapshot.get("tool_calls", [])),
                "retrieved_count": len(state.state_snapshot.get("retrieved", [])),
                "persisted_memory_count": len(state.state_snapshot.get("persisted_memory_ids", [])),
                "evaluation_outcome": state.state_snapshot.get("writeback", {}).get("evaluation_outcome"),
            },
        }

    def _persist_memory_blocks(self, memory_store, writeback, tags: TagSet, synthesis: str, run_dir: Path, state: RunState) -> List[str]:
        blocks: List[MemoryBlock] = []
        stable_id = hashlib.sha256(f"{run_dir.name}_{synthesis}".encode()).hexdigest()[:16]
        version_info = self._version_info(state)
        blocks.append(
            MemoryBlock(
                id=f"mem_{stable_id}",
                content=synthesis,
                tags=tags,
                provenance={"source": "cognition_engine", "kind": "episode"},
                lane="episodic",
                confidence=0.8,
                version_info=version_info,
            )
        )

        for index, fact in enumerate(writeback.distilled_facts):
            blocks.append(
                MemoryBlock(
                    id=f"sem_{stable_id}_{index}",
                    content=fact,
                    tags=tags,
                    provenance={"source": "cognition_engine", "kind": "distilled_fact"},
                    lane="semantic",
                    confidence=0.85,
                    version_info=version_info,
                )
            )

        if writeback.procedural_snippet:
            blocks.append(
                MemoryBlock(
                    id=f"proc_{stable_id}",
                    content=writeback.procedural_snippet,
                    tags=tags,
                    provenance={"source": "cognition_engine", "kind": "procedure"},
                    lane="procedural",
                    confidence=0.9,
                    version_info=version_info,
                )
            )

        persisted_ids: List[str] = []
        for block in blocks:
            validate_memoryblock(block)
            try:
                memory_store.write(block)
            except Exception as exc:
                raise RuntimeError(f"memory backend unavailable: {exc}") from exc
            persisted_ids.append(block.id)

        state.state_snapshot["persisted_memory_ids"] = persisted_ids
        return persisted_ids

    def run(self, task: str, run_dir: Path) -> EventRecord:
        run_dir = Path(run_dir)
        run_dir.mkdir(parents=True, exist_ok=True)

        state = RunState(task=task, status="running", current_step=1)
        state.state_snapshot["active_backend"] = self.active_backend
        state.state_snapshot["run_id"] = run_dir.name
        self._ensure_span_root(state)
        state.save(run_dir)
        return self._execute_run(run_dir, state)

    def resume_run(self, run_dir: Path) -> EventRecord:
        state = RunState.load(Path(run_dir))
        if state.status == "completed":
            raise RuntimeError("Cannot resume a completed run.")
        if state.status == "pending":
            state.status = "running"
        return self._execute_run(Path(run_dir), state)

    def _execute_run(self, run_dir: Path, state: RunState) -> EventRecord:
        run_id = run_dir.name
        self._configure_backend(state.state_snapshot.get("active_backend", self.active_backend))

        meta = {
            "run_id": run_id,
            "engine_version": self.config.engine_version,
            "config_hash": self.config.config_hash,
            "cognition_backend": self.active_backend,
            "configured_cognition_backend": self.config.cognition_backend,
        }
        write_meta(run_dir, meta)

        memory_store = self._initialize_memory_store(run_dir, state)
        trace_log = TraceLog(run_dir / "trace.jsonl")
        event_log = EventLog(run_dir / "eventlog.jsonl")
        final_failure_class = None

        while state.attempt <= self.config.retry_max_attempts and state.status == "running":
            try:
                if state.current_step == 1:
                    tags = self.tagger.extract(state.task)
                    validate_tagset(tags)
                    state.state_snapshot["tags"] = tags.to_dict()
                    state.state_snapshot["role_models"] = self._select_role_models([])
                    dp = DecisionPoint("tag_extraction", {"task": state.task[:50]}, {"tags": tags.to_dict()})
                    self._record_span(state, "ai.llm.invoke", "success", {"phase": "tag_extraction", "backend": self.active_backend})
                    state.state_snapshot["dp_1"] = dp.to_dict()
                    state.current_step = 2
                    state.save(run_dir)

                if state.current_step == 2:
                    tags = TagSet.from_dict(state.state_snapshot["tags"])
                    query_plan = self.planner.plan(tags)
                    validate_queryplan(query_plan)
                    state.state_snapshot["query_plan"] = query_plan.to_dict()
                    dp = DecisionPoint("query_planning", {"tags": tags.to_dict()}, {"query_plan": query_plan.to_dict()})
                    self._record_span(state, "ai.llm.invoke", "success", {"phase": "query_planning", "backend": self.active_backend})
                    state.state_snapshot["dp_2"] = dp.to_dict()
                    state.current_step = 3
                    state.save(run_dir)

                if state.current_step == 3:
                    tags = TagSet.from_dict(state.state_snapshot["tags"])
                    query_plan = QueryPlan.from_dict(state.state_snapshot["query_plan"])
                    try:
                        candidates = memory_store.read(tags, query_plan)
                    except Exception as exc:
                        raise RuntimeError(f"memory backend unavailable: {exc}") from exc

                    retriever = Retriever(candidates, config_enabled=self.config.rust_acceleration_toggles.get("retrieval_ranking", False))
                    retrieved, ret_exp = retriever.retrieve(tags, query_plan)
                    r_stats = RetrievalStats(
                        k_requested=ret_exp["k_requested"],
                        k_returned=ret_exp["k_returned"],
                        scores=ret_exp["scores"],
                        diversity_hits=ret_exp["diversity_hits"],
                        expansion_applied=ret_exp["expansion_applied"],
                    )
                    state.state_snapshot["retrieval_stats"] = r_stats.__dict__
                    state.state_snapshot["retrieved"] = [b.to_dict() for b in retrieved]
                    dp = DecisionPoint("retrieval", {"candidates": len(candidates)}, {"retrieved_count": len(retrieved)})
                    state.state_snapshot["dp_3"] = dp.to_dict()
                    state.current_step = 4
                    state.save(run_dir)

                if state.current_step == 4:
                    tags = TagSet.from_dict(state.state_snapshot["tags"])
                    query_plan = QueryPlan.from_dict(state.state_snapshot["query_plan"])
                    retrieved = [MemoryBlock.from_dict(b) for b in state.state_snapshot["retrieved"]]
                    agents, routing_reason, decomp, router_conf = self.router.route(state.task, tags, query_plan, retrieved)

                    plugin_context = PluginContext(task=state.task, tags=tags.tags, selected_agents=agents)
                    plugins = self.plugin_registry.select(plugin_context)
                    role_models = self._select_role_models([plugin.role for plugin in plugins])
                    merged_agents = self._merge_agent_preferences(agents, [plugin.to_dict() for plugin in plugins])
                    enrichment = select_enrichment(state.task, tags.tags, plugins, merged_agents, role_models)

                    state.state_snapshot["selected_agents"] = merged_agents
                    state.state_snapshot["plugins"] = [plugin.to_dict() for plugin in plugins]
                    state.state_snapshot["role_models"] = role_models
                    state.state_snapshot["enrichment"] = enrichment.to_dict()
                    dp = DecisionPoint(
                        "routing",
                        {"task": state.task[:50]},
                        {
                            "agents": merged_agents,
                            "reason": routing_reason,
                            "confidence": router_conf,
                            "decomposition": decomp,
                            "plugins": [plugin.name for plugin in plugins],
                        },
                    )
                    self._record_span(state, "ai.llm.invoke", "success", {"phase": "routing", "backend": self.active_backend, "plugins": [plugin.name for plugin in plugins]})
                    self._record_span(state, "ai.agent.invoke", "success", {"phase": "agent_selection", "selected_agents": merged_agents, "plugins": [plugin.name for plugin in plugins]})
                    state.state_snapshot["dp_4"] = dp.to_dict()
                    state.current_step = 5
                    state.state_snapshot.setdefault("tool_calls", [])
                    state.save(run_dir)

                if state.current_step == 5:
                    agents = state.state_snapshot.get("selected_agents", [])
                    tool_calls = state.state_snapshot.get("tool_calls", [])
                    disable_tools = state.state_snapshot.get("disable_tools", False)

                    if not disable_tools and "interpreter" in agents and len(tool_calls) == 0:
                        sandbox_root = self.config.path_allowlists[0] if self.config.path_allowlists else str(run_dir)
                        command = self._build_interpreter_command(state.task)
                        req = ToolRequest(
                            "open_interpreter",
                            {
                                "command": command,
                                "approval_token": f"APPROVE: {command}",
                                "timeout": 2.0,
                                "sandbox_root": sandbox_root,
                                "working_directory": sandbox_root,
                            },
                        )
                        res, dp = self.gateway.execute(req, ApprovalContext(approved_by="engine_policy", reason="default_interpreter_phase"))
                        if res.status == "denied":
                            raise PermissionError(f"permission denied: {res.error_class}")
                        if res.status == "error":
                            raise RuntimeError(f"tool execution error: {res.error_class or res.output}")
                        state.state_snapshot["dp_5"] = dp.to_dict()
                        self._record_span(state, "ai.tool.invoke", res.status, {"tool": req.name, "sandbox_root": sandbox_root, "duration_ms": res.duration_ms})
                        state.state_snapshot["tool_calls"].append(
                            {
                                "tool_call_id": res.tool_call_id,
                                "name": req.name,
                                "status": res.status,
                                "duration_ms": res.duration_ms,
                                "error_class": res.error_class,
                                "output_summary": str(res.output)[:160] if res.output else None,
                            }
                        )
                        tool_calls = state.state_snapshot.get("tool_calls", [])

                    if not disable_tools and "researcher" in agents and len(tool_calls) == 0:
                        tool_path = self.config.path_allowlists[0] if self.config.path_allowlists else "."
                        req = ToolRequest("list_directory", {"path": tool_path})
                        res, dp = self.gateway.execute(req, ApprovalContext(approved_by="engine_policy", reason="default_research_phase"))
                        if res.status == "denied":
                            raise PermissionError(f"permission denied: {res.error_class}")
                        if res.status == "error":
                            raise RuntimeError(f"tool execution error: {res.error_class or res.output}")
                        state.state_snapshot["dp_5"] = dp.to_dict()
                        self._record_span(state, "ai.tool.invoke", res.status, {"tool": req.name, "path": tool_path, "duration_ms": res.duration_ms})
                        state.state_snapshot["tool_calls"].append(
                            {
                                "tool_call_id": res.tool_call_id,
                                "name": req.name,
                                "status": res.status,
                                "duration_ms": res.duration_ms,
                                "error_class": res.error_class,
                                "output_summary": str(res.output)[:160] if res.output else None,
                            }
                        )

                    state.current_step = 6
                    state.save(run_dir)

                if state.current_step == 6:
                    tags = TagSet.from_dict(state.state_snapshot["tags"])
                    retrieved = [MemoryBlock.from_dict(b) for b in state.state_snapshot["retrieved"]]
                    tool_calls = state.state_snapshot.get("tool_calls", [])
                    synthesis = self.synthesizer.synthesize(state.task, tags, retrieved, tool_calls)
                    state.state_snapshot["synthesis"] = synthesis
                    dp = DecisionPoint("synthesis", {"context_len": len(retrieved)}, {"result_preview": synthesis[:100]})
                    self._record_span(state, "ai.llm.invoke", "success", {"phase": "synthesis", "backend": self.active_backend, "tool_call_count": len(tool_calls)})
                    state.state_snapshot["dp_6"] = dp.to_dict()
                    state.current_step = 7
                    state.save(run_dir)

                if state.current_step == 7:
                    tags = TagSet.from_dict(state.state_snapshot["tags"])
                    synthesis = state.state_snapshot["synthesis"]
                    writeback = self.evaluator.evaluate(state.task, synthesis, tags)
                    writeback.version_info = self._version_info(state)
                    validate_writeback(writeback)
                    self._record_span(state, "ai.llm.invoke", "success", {"phase": "evaluation", "backend": self.active_backend, "evaluation_outcome": writeback.evaluation_outcome})
                    state.state_snapshot["writeback"] = writeback.to_dict()
                    self._write_json_artifact(run_dir / "writeback.json", writeback.to_dict())
                    promotion = self._build_promotion_artifact(state.task, tags, writeback, state)
                    self._write_json_artifact(run_dir / "promotion.json", promotion)
                    state.state_snapshot["promotion"] = promotion
                    writeback.version_info = self._version_info(state)
                    state.state_snapshot["writeback"] = writeback.to_dict()
                    self._write_json_artifact(run_dir / "writeback.json", writeback.to_dict())
                    dp = DecisionPoint("writeback", {"synthesis_preview": synthesis[:10]}, {"evaluation": writeback.evaluation_outcome, "procedural": bool(writeback.procedural_snippet)})
                    state.state_snapshot["dp_7"] = dp.to_dict()
                    state.current_step = 8
                    state.save(run_dir)

                if state.current_step == 8:
                    synthesis = state.state_snapshot["synthesis"]
                    tags = TagSet.from_dict(state.state_snapshot["tags"])
                    writeback_payload = state.state_snapshot["writeback"]
                    writeback = WritebackPackage.from_dict(writeback_payload)
                    persisted_ids = self._persist_memory_blocks(memory_store, writeback, tags, synthesis, run_dir, state)
                    state.state_snapshot["persisted_memory_ids"] = persisted_ids
                    state.status = "completed"
                    manifest = self._build_run_manifest(run_dir, state)
                    self._write_json_artifact(run_dir / "run_manifest.json", manifest)
                    state.state_snapshot["run_manifest"] = manifest
                    state.save(run_dir)
                    break

            except Exception as e:
                final_failure_class, ctx = self.classifier.classify(e)
                decision, retry_dp = self.retry_engine.evaluate(final_failure_class, state.attempt)
                state.state_snapshot[f"error_dp_{state.attempt}"] = retry_dp.to_dict()
                state.state_snapshot[f"error_ctx_{state.attempt}"] = ctx
                self._apply_retry_decision(decision, run_dir, state, ctx)
                memory_store = self._initialize_memory_store(run_dir, state)
                if state.status != "running":
                    break

        version_info = self._version_info(state)
        provenance = ProvenanceInfo(
            git_commit="",
            engine_version=self.config.engine_version,
            cognition_backend=self.active_backend,
            config_hash=self.config.config_hash,
            version_info=version_info,
        )
        safe_tags = TagSet.from_dict(state.state_snapshot["tags"]) if "tags" in state.state_snapshot else TagSet(tags={})
        query_plan = QueryPlan.from_dict(state.state_snapshot["query_plan"]) if "query_plan" in state.state_snapshot else QueryPlan(filters={"tags": {}}, limits=0, recency_bias=0.0)

        dps = []
        for i in range(1, 8):
            if f"dp_{i}" in state.state_snapshot:
                raw_dp = state.state_snapshot[f"dp_{i}"]
                dps.append(DecisionPoint(raw_dp["name"], raw_dp["inputs_summary"], raw_dp["choice"], rationale=raw_dp.get("rationale"), latency_ms=raw_dp.get("latency_ms")))

        eval_outcome = state.state_snapshot.get("writeback", {}).get("evaluation_outcome", "error")
        retrieval_stats = RetrievalStats(**state.state_snapshot["retrieval_stats"]) if "retrieval_stats" in state.state_snapshot else None
        outcome_word = state.status if state.status in ["success", "completed", "failed", "degraded"] else "failure"
        if outcome_word == "completed":
            outcome_word = "success"
        if outcome_word == "failed":
            outcome_word = "failure"
        if outcome_word == "success" and state.state_snapshot.get("degraded_mode"):
            outcome_word = "degraded"

        execution_spans = self._finalize_spans(state, outcome_word)
        trace = PerformanceTrace(
            run_id=run_id,
            task=state.task,
            tags=safe_tags,
            decision_points=dps,
            outcome=outcome_word,
            evaluation_outcome=eval_outcome,
            validators=["contracts_v1_strict"],
            provenance=provenance,
            failure_class=final_failure_class.value if final_failure_class else None,
            retrieval_stats=retrieval_stats,
            execution_spans=execution_spans,
        )
        trace_log.append(trace)

        event = EventRecord(
            task=state.task,
            tags=safe_tags,
            query_plan=query_plan,
            retrieved_ids=[b["id"] for b in state.state_snapshot.get("retrieved", [])],
            actions=state.state_snapshot.get("selected_agents", []),
            tool_calls=state.state_snapshot.get("tool_calls", []),
            validations=["contracts_v1_strict"],
            outcome=outcome_word,
            version_info=version_info,
            failure_class=final_failure_class.value if final_failure_class else None,
            retries=state.attempt - 1,
            provenance={
                "trace_id": trace.trace_id,
                "backend": self.active_backend,
                "run_artifact_dir": str(run_dir),
                "degraded_mode": bool(state.state_snapshot.get("degraded_mode")),
                "version_info": version_info,
                "plugins": [plugin.get("name") for plugin in state.state_snapshot.get("plugins", [])],
                "role_models": state.state_snapshot.get("role_models", {}),
                "enrichment": state.state_snapshot.get("enrichment", {}),
                "persisted_memory_ids": state.state_snapshot.get("persisted_memory_ids", []),
                "promotion_artifact": state.state_snapshot.get("promotion", {}),
                "run_manifest": state.state_snapshot.get("run_manifest", {}),
            },
        )
        validate_eventrecord(event)
        event_log.append(event)
        return event

























