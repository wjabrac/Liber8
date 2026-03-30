"""Contracts for the LIBR8 Router."""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from src.contracts import TagSet, QueryPlan, MemoryBlock


@dataclass
class RouterInput:
    task: str
    tags: TagSet
    query_plan: QueryPlan
    retrieved_blocks: List[MemoryBlock]
    prior_context: Optional[Dict[str, Any]] = None


@dataclass
class RouterOutput:
    agents: List[str]
    routing_reason: str
    decomposition: List[Dict[str, Any]]
    confidence: float
    fallback_used: bool
