"""Data contracts for tool payloads."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import uuid

@dataclass
class ApprovalContext:
    approved_by: str
    reason: str

@dataclass
class ToolRequest:
    name: str
    arguments: Dict[str, Any]
    tool_call_id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class ToolResultEnvelope:
    tool_call_id: str
    status: str
    duration_ms: float
    output: Any
    error_class: Optional[str] = None
