"""Approval and review queue primitives for service-side control flows."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Dict, List


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ApprovalRequest:
    request_id: str
    task_id: str
    scope: str
    reason: str
    status: str = "pending"
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


class InMemoryApprovalQueue:
    def __init__(self) -> None:
        self._requests: Dict[str, ApprovalRequest] = {}

    def submit(self, request: ApprovalRequest) -> None:
        self._requests[request.request_id] = request

    def resolve(self, request_id: str, status: str) -> ApprovalRequest | None:
        request = self._requests.get(request_id)
        if request is None:
            return None
        request.status = status
        request.updated_at = _now_iso()
        return request

    def get(self, request_id: str) -> ApprovalRequest | None:
        return self._requests.get(request_id)

    def pending(self) -> List[ApprovalRequest]:
        return [request for request in self._requests.values() if request.status == "pending"]
