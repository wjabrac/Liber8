"""Migration layer for upcasting persisted artifacts to current schema versions."""

from typing import Dict, Any

def upcast_event(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Upcasts an unversioned or v0 EventRecord payload to strict v1.0."""
    out = raw.copy()
    
    # Missing schema version
    if "schema_version" not in out:
        out["schema_version"] = "1.0"
        
    # v0 to v1 structural shifts
    if "tool_calls" not in out:
        out["tool_calls"] = []
    
    # Normalizing outcomes mapped in Phase 1
    if "outcome" in out:
        if out["outcome"] not in {"success", "failure", "degraded"}:
            if out["outcome"] == "completed":
                out["outcome"] = "success"
            else:
                out["outcome"] = "failure"
                
    # Normalize nested TagSet schema version
    if "tags" in out and isinstance(out["tags"], dict):
        if "schema_version" not in out["tags"]:
            out["tags"]["schema_version"] = "1.0"
            
    # Normalize nested QueryPlan
    if "query_plan" in out and isinstance(out["query_plan"], dict):
        if "schema_version" not in out["query_plan"]:
            out["query_plan"]["schema_version"] = "1.0"
            
    return out

def upcast_trace(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Upcasts a PerformanceTrace to v1.0 strict."""
    out = raw.copy()
    if "schema_version" not in out:
        out["schema_version"] = "1.0"
        
    if "outcome" in out:
        if out["outcome"] not in {"success", "failure", "degraded"}:
            if out["outcome"] == "completed":
                out["outcome"] = "success"
            else:
                out["outcome"] = "failure"
                
    if "tags" in out and isinstance(out["tags"], dict):
        if "schema_version" not in out["tags"]:
            out["tags"]["schema_version"] = "1.0"
            
    return out
