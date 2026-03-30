"""Performance Trace v0 models and writers."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .contracts import TagSet, _now_iso, _ensure_jsonable, _require


@dataclass
class DecisionPoint:
    name: str
    inputs_summary: Dict[str, Any]
    choice: Dict[str, Any]
    rationale: Optional[str] = None
    latency_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "inputs_summary": self.inputs_summary,
            "choice": self.choice,
            "rationale": self.rationale,
            "latency_ms": self.latency_ms,
        }


@dataclass
class RetrievalStats:
    k_requested: int
    k_returned: int
    scores: List[Dict[str, Any]]
    diversity_hits: List[str]
    expansion_applied: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "k_requested": self.k_requested,
            "k_returned": self.k_returned,
            "scores": self.scores,
            "diversity_hits": self.diversity_hits,
            "expansion_applied": self.expansion_applied,
        }


@dataclass
class CostInfo:
    model_calls: int = 0
    tokens_in: float = 0.0
    tokens_out: float = 0.0
    cost_usd: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_calls": self.model_calls,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "cost_usd": self.cost_usd,
        }


@dataclass
class ProvenanceInfo:
    git_commit: str
    engine_version: str
    cognition_backend: str
    config_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "git_commit": self.git_commit,
            "engine_version": self.engine_version,
            "cognition_backend": self.cognition_backend,
            "config_hash": self.config_hash,
        }


@dataclass
class PerformanceTrace:
    run_id: str
    task: str
    tags: TagSet
    decision_points: List[DecisionPoint]
    outcome: str
    evaluation_outcome: str
    validators: List[str]
    provenance: ProvenanceInfo
    created_at: str = field(default_factory=_now_iso)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    schema_version: str = "1.0"
    failure_class: Optional[str] = None
    retrieval_stats: Optional[RetrievalStats] = None
    costs: Optional[CostInfo] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "trace_id": self.trace_id,
            "run_id": self.run_id,
            "created_at": self.created_at,
            "task": self.task,
            "tags": self.tags.to_dict(),
            "decision_points": [dp.to_dict() for dp in self.decision_points],
            "outcome": self.outcome,
            "failure_class": self.failure_class,
            "evaluation_outcome": self.evaluation_outcome,
            "validators": self.validators,
            "retrieval_stats": self.retrieval_stats.to_dict() if self.retrieval_stats else None,
            "costs": self.costs.to_dict() if self.costs else None,
            "provenance": self.provenance.to_dict(),
        }


class TraceLog:
    def __init__(self, file_path: Path | str):
        self.file_path = Path(file_path)
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, trace: PerformanceTrace) -> None:
        payload = trace.to_dict()
        _ensure_jsonable(payload, "trace payload")
        with self.file_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
