"""Router that composes small agents."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from ..agents import retrieval_agent, synthesis_agent, tagger_agent, writeback_agent
from ..contracts import EventRecord, QueryPlan, TagSet, ValidationError
from ..eventlog import EventLog
from ..memory_adapter import FileSystemMemoryAdapter


def _fallback_tags() -> TagSet:
    return TagSet(schema_version="v0", tags={})


def _fallback_query_plan() -> QueryPlan:
    return QueryPlan(filters={}, limits=0, recency_bias=0.0)


def run_router(
    task: str,
    storage_dir: Path,
    *,
    fake_backend: bool = False,
    model_endpoint: Optional[str] = None,
) -> EventRecord:
    storage_dir = Path(storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    memory_adapter = FileSystemMemoryAdapter(storage_dir / "memory.jsonl")
    actions: List[str] = []
    tool_calls: List[dict] = []
    retrieved_ids: List[str] = []
    tags: TagSet = _fallback_tags()
    query_plan: QueryPlan = _fallback_query_plan()
    failure_class: Optional[str] = None
    outcome = "success"
    provenance = {}

    try:
        tags = tagger_agent.extract_tags(task, fake_backend=fake_backend, model_endpoint=model_endpoint)
        actions.append("tag_extraction")
        tool_calls.append({"name": "tagger", "fake": fake_backend})

        retrieved, query_plan = retrieval_agent.retrieve(tags, memory_adapter)
        actions.append("memory_read")
        retrieved_ids = [block.id for block in retrieved]

        synthesis, writeback = synthesis_agent.synthesize(task, tags, retrieved)
        actions.append("synthesis")

        writeback_id = writeback_agent.write_memory(synthesis, tags, memory_adapter)
        actions.append("memory_write")

        provenance = {
            "writeback": writeback.to_dict(),
            "writeback_id": writeback_id,
            "query_plan": query_plan.to_dict(),
        }
    except ValidationError as exc:
        outcome = "failure"
        failure_class = "validation_error"
        provenance = {"error": str(exc)}
    except Exception as exc:  # pragma: no cover - defensive guard
        outcome = "failure"
        failure_class = "unknown"
        provenance = {"error": str(exc)}

    actions.append("event_log")
    event = EventRecord(
        task=task,
        tags=tags,
        query_plan=query_plan,
        retrieved_ids=retrieved_ids,
        actions=actions,
        tool_calls=tool_calls,
        validations=["contracts_v0"],
        outcome=outcome,
        failure_class=failure_class,
        retries=0,
        cost=0.0,
        latency=0.0,
        provenance=provenance,
    )
    EventLog(storage_dir / "eventlog.jsonl").append(event)
    return event
