"""Validators for LIBR8 contracts running at ingress/egress boundaries."""

import json
from typing import Any, Dict, List
from .errors import ValidationError
from .models import SCHEMA_VERSION, TagSet, QueryPlan, MemoryBlock, WritebackPackage, EventRecord


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


def _ensure_version_info(values: Dict[Any, Any], path: str) -> None:
    _ensure_dict_str_keys(values, path)
    for key, value in values.items():
        _require(isinstance(value, str), f"{path}.{key} must be a string")


def validate_tagset(ts: TagSet) -> None:
    _require(isinstance(ts.schema_version, str) and ts.schema_version.strip(), "schema_version required")
    _require(ts.schema_version == SCHEMA_VERSION, f"schema_version must be {SCHEMA_VERSION}")
    _ensure_dict_str_keys(ts.tags, "tags")
    for key, value in ts.tags.items():
        _ensure_jsonable(value, f"tags.{key}")
    if ts.uncertainty is not None:
        _ensure_dict_str_keys(ts.uncertainty, "uncertainty")
        for key, value in ts.uncertainty.items():
            _require(isinstance(value, (int, float)), f"uncertainty.{key} must be a number")
            _require(0.0 <= float(value) <= 1.0, f"uncertainty.{key} must be between 0 and 1")


def validate_queryplan(qp: QueryPlan) -> None:
    _require(qp.schema_version == SCHEMA_VERSION, f"schema_version must be {SCHEMA_VERSION}")
    _ensure_dict_str_keys(qp.filters, "filters")
    _require(isinstance(qp.limits, int) and qp.limits >= 0, "limits must be a non-negative int")
    _require(isinstance(qp.recency_bias, (int, float)), "recency_bias must be a number")
    _require(0.0 <= float(qp.recency_bias) <= 1.0, "recency_bias must be between 0 and 1")
    _ensure_list_of_str(qp.diversity_rules, "diversity_rules")
    _ensure_list_of_str(qp.expansion_rules, "expansion_rules")
    _ensure_dict_str_keys(qp.scoring_knobs, "scoring_knobs")
    _ensure_jsonable(qp.scoring_knobs, "scoring_knobs")


def validate_memoryblock(mb: MemoryBlock) -> None:
    _require(mb.schema_version == SCHEMA_VERSION, f"schema_version must be {SCHEMA_VERSION}")
    _require(isinstance(mb.content, str) and mb.content.strip(), "content required")
    validate_tagset(mb.tags)
    _ensure_dict_str_keys(mb.provenance, "provenance")
    _require(mb.lane in {"episodic", "semantic", "procedural"}, "lane must be episodic, semantic, or procedural")
    _require(isinstance(mb.confidence, (int, float)), "confidence must be a number")
    _require(0.0 <= float(mb.confidence) <= 1.0, "confidence must be between 0 and 1")
    _ensure_version_info(mb.version_info, "version_info")
    _require(isinstance(mb.id, str) and mb.id.strip(), "id required")
    _require(isinstance(mb.created_at, str) and mb.created_at.strip(), "created_at required")
    _require(isinstance(mb.updated_at, str) and mb.updated_at.strip(), "updated_at required")
    if mb.valid_until is not None:
        _require(isinstance(mb.valid_until, str) and mb.valid_until.strip(), "valid_until must be a string")


def validate_writeback(wb: WritebackPackage) -> None:
    _require(wb.schema_version == SCHEMA_VERSION, f"schema_version must be {SCHEMA_VERSION}")
    _require(isinstance(wb.episode, str) and wb.episode.strip(), "episode required")
    _ensure_list_of_str(wb.distilled_facts, "distilled_facts")
    validate_tagset(wb.tags)
    _require(isinstance(wb.evaluation_outcome, str) and wb.evaluation_outcome.strip(), "evaluation_outcome required")
    _ensure_version_info(wb.version_info, "version_info")
    if wb.procedural_snippet is not None:
        _require(isinstance(wb.procedural_snippet, str), "procedural_snippet must be a string")
    if wb.promotion_notes is not None:
        _require(isinstance(wb.promotion_notes, str), "promotion_notes must be a string")
    if wb.demotion_notes is not None:
        _require(isinstance(wb.demotion_notes, str), "demotion_notes must be a string")


def validate_eventrecord(er: EventRecord) -> None:
    _require(er.schema_version == SCHEMA_VERSION, f"schema_version must be {SCHEMA_VERSION}")
    _require(isinstance(er.task, str) and er.task.strip(), "task required")
    validate_tagset(er.tags)
    validate_queryplan(er.query_plan)
    _ensure_list_of_str(er.retrieved_ids, "retrieved_ids")
    _ensure_list_of_str(er.actions, "actions")
    _require(isinstance(er.tool_calls, list), "tool_calls must be a list")
    for idx, call in enumerate(er.tool_calls):
        _require(isinstance(call, dict), f"tool_calls[{idx}] must be a dict")
        _ensure_jsonable(call, f"tool_calls[{idx}]")
    _ensure_list_of_str(er.validations, "validations")
    _require(isinstance(er.outcome, str) and er.outcome.strip(), "outcome required")
    _require(er.outcome in {"success", "failure", "degraded"}, f"outcome must be success, failure, or degraded, got {er.outcome}")
    _ensure_version_info(er.version_info, "version_info")
    if er.failure_class is not None:
        _require(isinstance(er.failure_class, str), "failure_class must be a string")
    _require(isinstance(er.retries, int) and er.retries >= 0, "retries must be a non-negative int")
    _require(isinstance(er.cost, (int, float)) and er.cost >= 0, "cost must be a non-negative number")
    _require(isinstance(er.latency, (int, float)) and er.latency >= 0, "latency must be a non-negative number")
    _require(isinstance(er.id, str) and er.id.strip(), "id required")
    _require(isinstance(er.timestamp, str) and er.timestamp.strip(), "timestamp required")
    _ensure_dict_str_keys(er.provenance, "provenance")
    _ensure_jsonable(er.provenance, "provenance")
