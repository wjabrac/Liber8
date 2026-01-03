"""Retrieval agent for memory blocks."""

from __future__ import annotations

from typing import List, Tuple

from ..contracts import MemoryBlock, QueryPlan, TagSet
from ..memory_adapter import FileSystemMemoryAdapter


def build_query_plan(tags: TagSet) -> QueryPlan:
    return QueryPlan(
        filters={"tags": tags.tags},
        limits=5,
        recency_bias=0.5,
        diversity_rules=["unique_sources"],
        expansion_rules=["synonyms"],
        scoring_knobs={"freshness": 0.3, "relevance": 0.7},
    )


def retrieve(
    tags: TagSet,
    memory_adapter: FileSystemMemoryAdapter,
    *,
    query_plan: QueryPlan | None = None,
) -> Tuple[List[MemoryBlock], QueryPlan]:
    plan = query_plan or build_query_plan(tags)
    blocks = memory_adapter.read(tags, query_plan=plan)
    return blocks, plan
