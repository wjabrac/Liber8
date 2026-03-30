"""Execution gateway applying policy, contexts, and boundaries."""

import time
import os
from typing import Optional, Tuple
from src.tools.contracts import ToolRequest, ToolResultEnvelope, ApprovalContext
from src.tools.registry import ToolRegistry
from src.tools.policy import ToolPolicy
from src.trace import DecisionPoint

class ExecutionGateway:
    def __init__(self, registry: ToolRegistry, policy: ToolPolicy):
        self.registry = registry
        self.policy = policy

    def execute(self, request: ToolRequest, approval: Optional[ApprovalContext] = None) -> Tuple[ToolResultEnvelope, DecisionPoint]:
        start = time.time()
        
        tool_data = self.registry.get_tool(request.name)
        if not tool_data:
            duration = (time.time() - start) * 1000
            env = ToolResultEnvelope(request.tool_call_id, "error", duration, None, "tool_not_found")
            dp = DecisionPoint("tool_execution", {"tool": request.name}, {"policy_decision": "error", "reason": "unregistered_tool"}, latency_ms=duration)
            return env, dp
            
        is_write = tool_data.get("is_write", False)
        
        args = request.arguments.copy()
        if "path" in args:
            raw_path = str(args["path"])
            norm_path = os.path.realpath(os.path.abspath(raw_path))
            # Optional allowlist boundary enforcement
            if self.policy.path_allowlists:
                allowed = False
                for w in self.policy.path_allowlists:
                    if norm_path.startswith(os.path.realpath(os.path.abspath(w))):
                        allowed = True
                        break
                if not allowed:
                    duration = (time.time() - start) * 1000
                    env = ToolResultEnvelope(request.tool_call_id, "denied", duration, None, "policy_violation_path_escape")
                    dp = DecisionPoint("tool_execution", {"tool": request.name, "path": norm_path}, {"policy_decision": "denied", "reason": "path_not_allowed"}, latency_ms=duration)
                    return env, dp
            args["path"] = norm_path
            
        if is_write:
            if self.policy.mode == "read_only":
                duration = (time.time() - start) * 1000
                env = ToolResultEnvelope(request.tool_call_id, "denied", duration, None, "policy_violation_write_in_read_only")
                dp = DecisionPoint("tool_execution", {"tool": request.name}, {"policy_decision": "denied", "reason": "write_in_read_only"}, latency_ms=duration)
                return env, dp
            if not approval:
                duration = (time.time() - start) * 1000
                env = ToolResultEnvelope(request.tool_call_id, "denied", duration, None, "policy_violation_missing_approval")
                dp = DecisionPoint("tool_execution", {"tool": request.name}, {"policy_decision": "denied", "reason": "missing_approval_context"}, latency_ms=duration)
                return env, dp
                
        try:
            result = tool_data["func"](**args)
            duration = (time.time() - start) * 1000
            env = ToolResultEnvelope(request.tool_call_id, "success", duration, result)
            dp = DecisionPoint("tool_execution", {"tool": request.name, "args": repr(args)[:100]}, {"policy_decision": "approved", "status": "success"}, latency_ms=duration)
            return env, dp
        except Exception as e:
            duration = (time.time() - start) * 1000
            env = ToolResultEnvelope(request.tool_call_id, "error", duration, str(e), "execution_error")
            dp = DecisionPoint("tool_execution", {"tool": request.name}, {"policy_decision": "approved", "status": "error", "message": str(e)}, latency_ms=duration)
            return env, dp
