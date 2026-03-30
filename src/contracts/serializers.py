"""Serializers for LIBR8 contracts."""

import json
from typing import Any, Dict
from .models import TagSet, QueryPlan, MemoryBlock, WritebackPackage, EventRecord

def tagset_to_dict(obj: TagSet) -> Dict[str, Any]:
    return {"schema_version": obj.schema_version, "tags": obj.tags, "uncertainty": obj.uncertainty}

def tagset_from_dict(payload: Dict[str, Any]) -> TagSet:
    return TagSet(
        schema_version=payload["schema_version"],
        tags=payload["tags"],
        uncertainty=payload.get("uncertainty")
    )

def queryplan_to_dict(obj: QueryPlan) -> Dict[str, Any]:
    return {
        "filters": obj.filters,
        "limits": obj.limits,
        "recency_bias": obj.recency_bias,
        "diversity_rules": obj.diversity_rules,
        "expansion_rules": obj.expansion_rules,
        "scoring_knobs": obj.scoring_knobs,
    }

def queryplan_from_dict(payload: Dict[str, Any]) -> QueryPlan:
    return QueryPlan(
        filters=payload["filters"],
        limits=payload["limits"],
        recency_bias=payload["recency_bias"],
        diversity_rules=payload.get("diversity_rules", []),
        expansion_rules=payload.get("expansion_rules", []),
        scoring_knobs=payload.get("scoring_knobs", {}),
    )

def memoryblock_to_dict(obj: MemoryBlock) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "content": obj.content,
        "tags": tagset_to_dict(obj.tags),
        "provenance": obj.provenance,
        "lane": obj.lane,
        "confidence": obj.confidence,
        "created_at": obj.created_at,
        "updated_at": obj.updated_at,
        "valid_until": obj.valid_until,
    }

def memoryblock_from_dict(payload: Dict[str, Any]) -> MemoryBlock:
    from .models import _now_iso
    import uuid
    return MemoryBlock(
        id=payload.get("id", str(uuid.uuid4())),
        content=payload["content"],
        tags=tagset_from_dict(payload["tags"]),
        provenance=payload.get("provenance", {}),
        lane=payload["lane"],
        confidence=payload["confidence"],
        created_at=payload.get("created_at", _now_iso()),
        updated_at=payload.get("updated_at", _now_iso()),
        valid_until=payload.get("valid_until"),
    )

def writeback_to_dict(obj: WritebackPackage) -> Dict[str, Any]:
    return {
        "episode": obj.episode,
        "distilled_facts": obj.distilled_facts,
        "procedural_snippet": obj.procedural_snippet,
        "tags": tagset_to_dict(obj.tags),
        "evaluation_outcome": obj.evaluation_outcome,
        "promotion_notes": obj.promotion_notes,
        "demotion_notes": obj.demotion_notes,
    }

def writeback_from_dict(payload: Dict[str, Any]) -> WritebackPackage:
    return WritebackPackage(
        episode=payload["episode"],
        distilled_facts=payload.get("distilled_facts", []),
        procedural_snippet=payload.get("procedural_snippet"),
        tags=tagset_from_dict(payload["tags"]),
        evaluation_outcome=payload["evaluation_outcome"],
        promotion_notes=payload.get("promotion_notes"),
        demotion_notes=payload.get("demotion_notes"),
    )

def eventrecord_to_dict(obj: EventRecord) -> Dict[str, Any]:
    return {
        "id": obj.id,
        "timestamp": obj.timestamp,
        "task": obj.task,
        "tags": tagset_to_dict(obj.tags),
        "query_plan": queryplan_to_dict(obj.query_plan),
        "retrieved_ids": obj.retrieved_ids,
        "actions": obj.actions,
        "tool_calls": obj.tool_calls,
        "validations": obj.validations,
        "outcome": obj.outcome,
        "failure_class": obj.failure_class,
        "retries": obj.retries,
        "cost": obj.cost,
        "latency": obj.latency,
        "provenance": obj.provenance,
    }

def eventrecord_from_dict(payload: Dict[str, Any]) -> EventRecord:
    from .models import _now_iso
    import uuid
    return EventRecord(
        id=payload.get("id", str(uuid.uuid4())),
        timestamp=payload.get("timestamp", _now_iso()),
        task=payload["task"],
        tags=tagset_from_dict(payload["tags"]),
        query_plan=queryplan_from_dict(payload["query_plan"]),
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
