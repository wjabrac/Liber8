"""Contracts for Failure Classification."""

from enum import Enum

class FailureClass(str, Enum):
    validation_error = "validation_error"  # generic
    backend_unavailable = "backend_unavailable"
    timeout = "timeout"
    unknown = "unknown"
    transient_io = "transient_io"
    transient_model = "transient_model"
    transient_rate_limit = "transient_rate_limit"
    deterministic_contract_violation = "deterministic_contract_violation"
    deterministic_validation_failure = "deterministic_validation_failure"
    tool_permission_denied = "tool_permission_denied"
    tool_execution_error = "tool_execution_error"
    memory_backend_unavailable = "memory_backend_unavailable"
    planner_inconsistent = "planner_inconsistent"
