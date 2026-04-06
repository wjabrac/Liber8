"""Approval and review queue primitives for service-side control flows."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from threading import Lock
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


class FileBackedApprovalQueue:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._requests: Dict[str, ApprovalRequest] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(payload, list):
            return
        for item in payload:
            if not isinstance(item, dict):
                continue
            try:
                request = ApprovalRequest(**item)
            except TypeError:
                continue
            self._requests[request.request_id] = request

    def _flush(self) -> None:
        snapshot = [request.to_dict() for request in self._requests.values()]
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
        tmp_path.replace(self.path)

    def submit(self, request: ApprovalRequest) -> None:
        with self._lock:
            self._requests[request.request_id] = request
            self._flush()

    def resolve(self, request_id: str, status: str) -> ApprovalRequest | None:
        with self._lock:
            request = self._requests.get(request_id)
            if request is None:
                return None
            request.status = status
            request.updated_at = _now_iso()
            self._flush()
            return request

    def get(self, request_id: str) -> ApprovalRequest | None:
        with self._lock:
            return self._requests.get(request_id)

    def pending(self) -> List[ApprovalRequest]:
        with self._lock:
            return [request for request in self._requests.values() if request.status == "pending"]
