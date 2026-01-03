"""Minimal cognition loop."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .contracts import EventRecord, MemoryBlock, QueryPlan, TagSet, WritebackPackage
from .eventlog import EventLog
from .memory_adapter import FileSystemMemoryAdapter
from .tagger import Tagger


def run_cognition_loop(
    task: str,
    storage_dir: Path,
    *,
    fake_backend: bool = False,
    model_endpoint: Optional[str] = None,
) -> EventRecord:
    storage_dir = Path(storage_dir)
    tagger = Tagger(fake_backend=fake_backend)
    if model_endpoint is not None:
        tagger.model_endpoint = model_endpoint
    tags = tagger.extract_tags(task)

    memory_adapter = FileSystemMemoryAdapter(storage_dir / "memory.jsonl")
    query_plan = QueryPlan(
        filters={"tags": tags.tags},
        limits=5,
        recency_bias=0.5,
        diversity_rules=["unique_sources"],
        expansion_rules=["synonyms"],
        scoring_knobs={"freshness": 0.3, "relevance": 0.7},
    )
    retrieved = memory_adapter.read(tags, query_plan=query_plan)

    synthesis = f"SYNTHESIS: {task} (retrieved {len(retrieved)} memories)"
    writeback = WritebackPackage(
        episode=synthesis,
        distilled_facts=[task],
        procedural_snippet=None,
        tags=tags,
        evaluation_outcome="ok",
        promotion_notes="stored in episodic lane",
        demotion_notes=None,
    )

    memory_block = MemoryBlock(
        content=synthesis,
        tags=tags,
        provenance={"source": "cognition_loop"},
        lane="episodic",
        confidence=0.6,
    )
    memory_adapter.write(memory_block)

    event = EventRecord(
        task=task,
        tags=tags,
        query_plan=query_plan,
        retrieved_ids=[block.id for block in retrieved],
        actions=["tag_extraction", "memory_read", "synthesis", "memory_write", "event_log"],
        tool_calls=[{"name": "tagger", "fake": fake_backend}],
        validations=["contracts_v0"],
        outcome="success",
        failure_class=None,
        retries=0,
        cost=0.0,
        latency=0.0,
        provenance={
            "writeback": writeback.to_dict(),
            "model_endpoint": tagger.model_endpoint,
            "query_plan": query_plan.to_dict(),
        },
    )

    EventLog(storage_dir / "eventlog.jsonl").append(event)
    return event
