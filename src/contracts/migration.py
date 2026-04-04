"""Migration layer for upcasting persisted artifacts to current schema versions."""

from typing import Dict, Any
from .models import SCHEMA_VERSION


def _normalize_version_info(payload: Dict[str, Any]) -> Dict[str, str]:
    raw = payload.get("version_info", {})
    if not isinstance(raw, dict):
        return {}
    return {str(key): str(value) for key, value in raw.items()}


def upcast_event(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Upcasts an unversioned or v0 EventRecord payload to strict v1.0."""
    out = raw.copy()

    if "schema_version" not in out:
        out["schema_version"] = SCHEMA_VERSION
    if "tool_calls" not in out:
        out["tool_calls"] = []
    out["version_info"] = _normalize_version_info(out)

    if "outcome" in out and out["outcome"] not in {"success", "failure", "degraded"}:
        out["outcome"] = "success" if out["outcome"] == "completed" else "failure"

    if "tags" in out and isinstance(out["tags"], dict) and "schema_version" not in out["tags"]:
        out["tags"]["schema_version"] = SCHEMA_VERSION
    if "query_plan" in out and isinstance(out["query_plan"], dict) and "schema_version" not in out["query_plan"]:
        out["query_plan"]["schema_version"] = SCHEMA_VERSION

    return out


def upcast_trace(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Upcasts a PerformanceTrace to v1.0 strict."""
    out = raw.copy()
    if "schema_version" not in out:
        out["schema_version"] = SCHEMA_VERSION

    if "outcome" in out and out["outcome"] not in {"success", "failure", "degraded"}:
        out["outcome"] = "success" if out["outcome"] == "completed" else "failure"

    if "tags" in out and isinstance(out["tags"], dict) and "schema_version" not in out["tags"]:
        out["tags"]["schema_version"] = SCHEMA_VERSION

    provenance = out.get("provenance") if isinstance(out.get("provenance"), dict) else {}
    provenance["version_info"] = _normalize_version_info(provenance)
    out["provenance"] = provenance

    spans = out.get("execution_spans", [])
    if not isinstance(spans, list):
        spans = []
    normalized_spans = []
    for span in spans:
        if not isinstance(span, dict):
            continue
        span_copy = span.copy()
        attributes = span_copy.get("attributes", {})
        span_copy["attributes"] = attributes if isinstance(attributes, dict) else {}
        normalized_spans.append(span_copy)
    out["execution_spans"] = normalized_spans

    return out
