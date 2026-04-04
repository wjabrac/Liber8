"""Deterministically classifies exceptions into standardized FailureClasses."""

from typing import Any, Dict, Tuple
from .contracts import FailureClass
from src.contracts.errors import ValidationError


class FailureClassifier:
    """Maps runtime anomalies into known failure classes."""

    def classify(self, exc: Exception, context: Dict[str, Any] = None) -> Tuple[FailureClass, Dict[str, Any]]:
        err_msg = str(exc).lower()

        if isinstance(exc, ValidationError):
            return FailureClass.deterministic_validation_failure, {
                "failing_validator": "unknown",
                "validation_errors": str(exc),
            }

        if "memory backend unavailable" in err_msg or "zep_python is not installed" in err_msg:
            return FailureClass.memory_backend_unavailable, {"exception": str(exc)}

        if "tool execution error" in err_msg:
            return FailureClass.tool_execution_error, {"exception": str(exc)}

        if "timeout" in err_msg:
            return FailureClass.timeout, {"exception": str(exc)}

        if "rate limit" in err_msg or "429" in err_msg:
            return FailureClass.transient_rate_limit, {"exception": str(exc)}

        if "connection refused" in err_msg or "no route to host" in err_msg:
            return FailureClass.transient_io, {"exception": str(exc)}

        if "permission denied" in err_msg:
            return FailureClass.tool_permission_denied, {"exception": str(exc)}

        return FailureClass.unknown, {
            "exception_type": type(exc).__name__,
            "stack_trace": str(exc)[:200],
        }
