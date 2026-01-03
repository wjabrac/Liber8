"""Contracts v0 for Liber8."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import uuid
from typing import Any, Dict, List, Optional


class ValidationError(ValueError):
    """Raised when contract validation fails."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def _ensure_jsonable(value: Any, path: str) -> None:
    try:
        json.dumps(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"Value at {path} is not JSON-serializable") from exc


def _ensure_list_of_str(values: List[Any], path: str) -> None:
    _require(isinstance(values, list), f"{path} must be a list")
    for idx, value in enumerate(values):
        _require(isinstance(value, str), f"{path}[{idx}] must be a string")


def _ensure_dict_str_keys(values: Dict[Any, Any], path: str) -> None:
    _require(isinstance(values, dict), f"{path} must be a dict")
    for key in values.keys():
        _require(isinstance(key, str), f"{path} keys must be strings")


@dataclass
class TagSet:
    schema_version: str
    tags: Dict[str, Any]
    uncertainty: Optional[Dict[str, float]] = None

    def __post_init__(self) -> None:
        _require(isinstance(self.schema_version, str) and self.schema_version.strip(), "schema_version required")
        _ensure_dict_str_keys(self.tags, "tags")
        for key, value in self.tags.items():
            _ensure_jsonable(value, f"tags.{key}")
        if self.uncertainty is not None:
            _ensure_dict_str_keys(self.uncertainty, "uncertainty")
            for key, value in self.uncertainty.items():
                _require(isinstance(value, (int, float)), f"uncertainty.{key} must be a number")
                _require(0.0 <= float(value) <= 1.0, f"uncertainty.{key} must be between 0 and 1")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "tags": self.tags,
            "uncertainty": self.uncertainty,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TagSet":
        return cls(
            schema_version=payload["schema_version"],
            tags=payload["tags"],
            uncertainty=payload.get("uncertainty"),
        )


@dataclass
class QueryPlan:
    filters: Dict[str, Any]
    limits: int
    recency_bias: float
    diversity_rules: List[str] = field(default_factory=list)
    expansion_rules: List[str] = field(default_factory=list)
    scoring_knobs: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _ensure_dict_str_keys(self.filters, "filters")
        _require(isinstance(self.limits, int) and self.limits >= 0, "limits must be a non-negative int")
        _require(isinstance(self.recency_bias, (int, float)), "recency_bias must be a number")
        _require(0.0 <= float(self.recency_bias) <= 1.0, "recency_bias must be between 0 and 1")
        _ensure_list_of_str(self.diversity_rules, "diversity_rules")
        _ensure_list_of_str(self.expansion_rules, "expansion_rules")
        _ensure_dict_str_keys(self.scoring_knobs, "scoring_knobs")
        _ensure_jsonable(self.scoring_knobs, "scoring_knobs")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "filters": self.filters,
            "limits": self.limits,
            "recency_bias": self.recency_bias,
            "diversity_rules": self.diversity_rules,
            "expansion_rules": self.expansion_rules,
            "scoring_knobs": self.scoring_knobs,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "QueryPlan":
        return cls(
            filters=payload["filters"],
            limits=payload["limits"],
            recency_bias=payload["recency_bias"],
            diversity_rules=payload.get("diversity_rules", []),
            expansion_rules=payload.get("expansion_rules", []),
            scoring_knobs=payload.get("scoring_knobs", {}),
        )


@dataclass
class MemoryBlock:
    content: str
    tags: TagSet
    provenance: Dict[str, Any]
    lane: str
    confidence: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    valid_until: Optional[str] = None

    def __post_init__(self) -> None:
        _require(isinstance(self.content, str) and self.content.strip(), "content required")
        _require(isinstance(self.tags, TagSet), "tags must be a TagSet")
        _ensure_dict_str_keys(self.provenance, "provenance")
        _require(self.lane in {"episodic", "semantic", "procedural"}, "lane must be episodic, semantic, or procedural")
        _require(isinstance(self.confidence, (int, float)), "confidence must be a number")
        _require(0.0 <= float(self.confidence) <= 1.0, "confidence must be between 0 and 1")
        _require(isinstance(self.id, str) and self.id.strip(), "id required")
        _require(isinstance(self.created_at, str) and self.created_at.strip(), "created_at required")
        _require(isinstance(self.updated_at, str) and self.updated_at.strip(), "updated_at required")
        if self.valid_until is not None:
            _require(isinstance(self.valid_until, str) and self.valid_until.strip(), "valid_until must be a string")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "tags": self.tags.to_dict(),
            "provenance": self.provenance,
            "lane": self.lane,
            "confidence": self.confidence,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "valid_until": self.valid_until,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "MemoryBlock":
        return cls(
            id=payload.get("id", str(uuid.uuid4())),
            content=payload["content"],
            tags=TagSet.from_dict(payload["tags"]),
            provenance=payload.get("provenance", {}),
            lane=payload["lane"],
            confidence=payload["confidence"],
            created_at=payload.get("created_at", _now_iso()),
            updated_at=payload.get("updated_at", _now_iso()),
            valid_until=payload.get("valid_until"),
        )


@dataclass
class WritebackPackage:
    episode: str
    distilled_facts: List[str]
    tags: TagSet
    evaluation_outcome: str
    procedural_snippet: Optional[str] = None
    promotion_notes: Optional[str] = None
    demotion_notes: Optional[str] = None

    def __post_init__(self) -> None:
        _require(isinstance(self.episode, str) and self.episode.strip(), "episode required")
        _ensure_list_of_str(self.distilled_facts, "distilled_facts")
        _require(isinstance(self.tags, TagSet), "tags must be a TagSet")
        _require(isinstance(self.evaluation_outcome, str) and self.evaluation_outcome.strip(), "evaluation_outcome required")
        if self.procedural_snippet is not None:
            _require(isinstance(self.procedural_snippet, str), "procedural_snippet must be a string")
        if self.promotion_notes is not None:
            _require(isinstance(self.promotion_notes, str), "promotion_notes must be a string")
        if self.demotion_notes is not None:
            _require(isinstance(self.demotion_notes, str), "demotion_notes must be a string")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode": self.episode,
            "distilled_facts": self.distilled_facts,
            "procedural_snippet": self.procedural_snippet,
            "tags": self.tags.to_dict(),
            "evaluation_outcome": self.evaluation_outcome,
            "promotion_notes": self.promotion_notes,
            "demotion_notes": self.demotion_notes,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "WritebackPackage":
        return cls(
            episode=payload["episode"],
            distilled_facts=payload.get("distilled_facts", []),
            procedural_snippet=payload.get("procedural_snippet"),
            tags=TagSet.from_dict(payload["tags"]),
            evaluation_outcome=payload["evaluation_outcome"],
            promotion_notes=payload.get("promotion_notes"),
            demotion_notes=payload.get("demotion_notes"),
        )


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
    failure_class: Optional[str] = None
    retries: int = 0
    cost: float = 0.0
    latency: float = 0.0
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=_now_iso)

    def __post_init__(self) -> None:
        _require(isinstance(self.task, str) and self.task.strip(), "task required")
        _require(isinstance(self.tags, TagSet), "tags must be a TagSet")
        _require(isinstance(self.query_plan, QueryPlan), "query_plan must be a QueryPlan")
        _ensure_list_of_str(self.retrieved_ids, "retrieved_ids")
        _ensure_list_of_str(self.actions, "actions")
        _require(isinstance(self.tool_calls, list), "tool_calls must be a list")
        for idx, call in enumerate(self.tool_calls):
            _require(isinstance(call, dict), f"tool_calls[{idx}] must be a dict")
            _ensure_jsonable(call, f"tool_calls[{idx}]")
        _ensure_list_of_str(self.validations, "validations")
        _require(isinstance(self.outcome, str) and self.outcome.strip(), "outcome required")
        if self.failure_class is not None:
            _require(isinstance(self.failure_class, str), "failure_class must be a string")
        _require(isinstance(self.retries, int) and self.retries >= 0, "retries must be a non-negative int")
        _require(isinstance(self.cost, (int, float)) and self.cost >= 0, "cost must be a non-negative number")
        _require(isinstance(self.latency, (int, float)) and self.latency >= 0, "latency must be a non-negative number")
        _require(isinstance(self.id, str) and self.id.strip(), "id required")
        _require(isinstance(self.timestamp, str) and self.timestamp.strip(), "timestamp required")
        _ensure_dict_str_keys(self.provenance, "provenance")
        _ensure_jsonable(self.provenance, "provenance")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "task": self.task,
            "tags": self.tags.to_dict(),
            "query_plan": self.query_plan.to_dict(),
            "retrieved_ids": self.retrieved_ids,
            "actions": self.actions,
            "tool_calls": self.tool_calls,
            "validations": self.validations,
            "outcome": self.outcome,
            "failure_class": self.failure_class,
            "retries": self.retries,
            "cost": self.cost,
            "latency": self.latency,
            "provenance": self.provenance,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "EventRecord":
        return cls(
            id=payload.get("id", str(uuid.uuid4())),
            timestamp=payload.get("timestamp", _now_iso()),
            task=payload["task"],
            tags=TagSet.from_dict(payload["tags"]),
            query_plan=QueryPlan.from_dict(payload["query_plan"]),
            retrieved_ids=payload.get("retrieved_ids", []),
            actions=payload.get("actions", []),
            tool_calls=payload.get("tool_calls", []),
            validations=payload.get("validations", []),
            outcome=payload["outcome"],
            failure_class=payload.get("failure_class"),
            retries=payload.get("retries", 0),
            cost=payload.get("cost", 0.0),
            latency=payload.get("latency", 0.0),
            provenance=payload.get("provenance", {}),
        )
