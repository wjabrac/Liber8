"""Export job queue primitives for service-side control flows."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Dict, List


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ExportJob:
    job_id: str
    run_id: str
    job_kind: str
    status: str = "pending"
    output_path: str | None = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, str | None]:
        return asdict(self)


class InMemoryExportJobQueue:
    def __init__(self) -> None:
        self._jobs: Dict[str, ExportJob] = {}

    def submit(self, job: ExportJob) -> None:
        self._jobs[job.job_id] = job

    def get(self, job_id: str) -> ExportJob | None:
        return self._jobs.get(job_id)

    def update(self, job_id: str, *, status: str, output_path: str | None = None) -> ExportJob | None:
        job = self._jobs.get(job_id)
        if job is None:
            return None
        job.status = status
        if output_path is not None:
            job.output_path = output_path
        job.updated_at = _now_iso()
        return job

    def list_all(self) -> List[ExportJob]:
        return list(self._jobs.values())
