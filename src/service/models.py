"""Shared service-layer models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Dict


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class RunRecord:
    task_id: str
    run_id: str
    task: str
    status: str
    outcome: str | None = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    artifact_dir: str | None = None
    failure_class: str | None = None

    def to_dict(self) -> Dict[str, str | None]:
        return asdict(self)
