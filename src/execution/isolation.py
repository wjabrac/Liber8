"""Execution isolation contracts for mutation-capable tool paths."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Protocol


@dataclass
class IsolationRequest:
    tool_name: str
    arguments: Dict[str, Any]
    approved_by: str | None = None
    reason: str | None = None


@dataclass
class IsolationResult:
    status: str
    output: Any = None
    error_class: str | None = None
    backend: str = "none"


class ExecutionIsolationBoundary(Protocol):
    backend_name: str

    def execute(self, request: IsolationRequest, func: Callable[..., Any]) -> IsolationResult: ...


class LocalPassthroughIsolationBoundary:
    backend_name = "local_passthrough"

    def execute(self, request: IsolationRequest, func: Callable[..., Any]) -> IsolationResult:
        try:
            return IsolationResult(status="success", output=func(**request.arguments), backend=self.backend_name)
        except Exception as exc:
            return IsolationResult(status="error", output=str(exc), error_class="execution_error", backend=self.backend_name)


class DenyIsolationBoundary:
    backend_name = "deny"

    def execute(self, request: IsolationRequest, func: Callable[..., Any]) -> IsolationResult:
        return IsolationResult(
            status="denied",
            output=None,
            error_class="isolation_backend_unavailable",
            backend=self.backend_name,
        )


def build_isolation_boundary(name: str | None) -> Optional[ExecutionIsolationBoundary]:
    if name in {None, "", "none"}:
        return None
    if name == "local_passthrough":
        return LocalPassthroughIsolationBoundary()
    if name == "deny":
        return DenyIsolationBoundary()
    return DenyIsolationBoundary()
