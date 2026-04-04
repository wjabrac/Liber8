"""Execution gateway applying policy, contexts, and boundaries."""

import time
from typing import Optional, Tuple
from src.execution.isolation import ExecutionIsolationBoundary, IsolationRequest
from src.tools.contracts import ToolRequest, ToolResultEnvelope, ApprovalContext
from src.tools.registry import ToolRegistry
from src.tools.policy import ToolPolicy
from src.tools.paths import is_within_allowed_roots, resolve_boundary_path
from src.trace import DecisionPoint


class ExecutionGateway:
    def __init__(self, registry: ToolRegistry, policy: ToolPolicy, isolation_boundary: ExecutionIsolationBoundary | None = None):
        self.registry = registry
        self.policy = policy
        self.isolation_boundary = isolation_boundary

    def execute(self, request: ToolRequest, approval: Optional[ApprovalContext] = None) -> Tuple[ToolResultEnvelope, DecisionPoint]:
        start = time.time()

        tool_data = self.registry.get_tool(request.name)
        if not tool_data:
            duration = (time.time() - start) * 1000
            env = ToolResultEnvelope(request.tool_call_id, "error", duration, None, "tool_not_found")
            dp = DecisionPoint("tool_execution", {"tool": request.name}, {"policy_decision": "error", "reason": "unregistered_tool"}, latency_ms=duration)
            return env, dp

        is_write = tool_data.get("is_write", False)
        requires_isolation = tool_data.get("requires_isolation", False)

        args = request.arguments.copy()
        if "path" in args:
            norm_path = resolve_boundary_path(str(args["path"]))
            if self.policy.path_allowlists and not is_within_allowed_roots(norm_path, self.policy.path_allowlists):
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
            if requires_isolation and self.policy.enforce_isolation_for_writes and self.isolation_boundary is None:
                duration = (time.time() - start) * 1000
                env = ToolResultEnvelope(request.tool_call_id, "denied", duration, None, "policy_violation_isolation_required")
                dp = DecisionPoint("tool_execution", {"tool": request.name}, {"policy_decision": "denied", "reason": "isolation_required"}, latency_ms=duration)
                return env, dp

        try:
            if requires_isolation and self.isolation_boundary is not None:
                result = self.isolation_boundary.execute(
                    IsolationRequest(
                        tool_name=request.name,
                        arguments=args,
                        approved_by=approval.approved_by if approval else None,
                        reason=approval.reason if approval else None,
                    ),
                    tool_data["func"],
                )
                duration = (time.time() - start) * 1000
                env = ToolResultEnvelope(request.tool_call_id, result.status, duration, result.output, result.error_class)
                dp = DecisionPoint(
                    "tool_execution",
                    {"tool": request.name, "args": repr(args)[:100]},
                    {"policy_decision": "approved", "status": result.status, "isolation_backend": result.backend},
                    latency_ms=duration,
                )
                return env, dp

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
