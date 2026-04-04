"""Data models for LIBR8 contracts. Validation is decoupled from instantiation."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid
import datetime

SCHEMA_VERSION = "1.0"


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


@dataclass
class TagSet:
    schema_version: str = SCHEMA_VERSION
    tags: Dict[str, Any] = field(default_factory=dict)
    uncertainty: Optional[Dict[str, float]] = None


@dataclass
class QueryPlan:
    filters: Dict[str, Any]
    limits: int
    recency_bias: float
    schema_version: str = SCHEMA_VERSION
    diversity_rules: List[str] = field(default_factory=list)
    expansion_rules: List[str] = field(default_factory=list)
    scoring_knobs: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryBlock:
    content: str
    tags: TagSet
    provenance: Dict[str, Any]
    lane: str
    confidence: float
    schema_version: str = SCHEMA_VERSION
    version_info: Dict[str, str] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    valid_until: Optional[str] = None


@dataclass
class WritebackPackage:
    episode: str
    distilled_facts: List[str]
    tags: TagSet
    evaluation_outcome: str
    schema_version: str = SCHEMA_VERSION
    version_info: Dict[str, str] = field(default_factory=dict)
    procedural_snippet: Optional[str] = None
    promotion_notes: Optional[str] = None
    demotion_notes: Optional[str] = None


@dataclass
class EventRecord:
    task: str
    tags: TagSet
    query_plan: QueryPlan
    retrieved_ids: List[str]
    actions: List[str]
    tool_calls: List[Dict[str, Any]]
    validations: List[str]
    outcome: str
    provenance: Dict[str, Any]
    schema_version: str = SCHEMA_VERSION
    version_info: Dict[str, str] = field(default_factory=dict)
    failure_class: Optional[str] = None
    retries: int = 0
    cost: float = 0.0
    latency: float = 0.0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=_now_iso)
