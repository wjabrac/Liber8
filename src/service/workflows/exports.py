"""Export job queue primitives for service-side control flows."""

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


class FileBackedExportJobQueue:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()
        self._jobs: Dict[str, ExportJob] = {}
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
                job = ExportJob(**item)
            except TypeError:
                continue
            self._jobs[job.job_id] = job

    def _flush(self) -> None:
        snapshot = [job.to_dict() for job in self._jobs.values()]
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
        tmp_path.replace(self.path)

    def submit(self, job: ExportJob) -> None:
        with self._lock:
            self._jobs[job.job_id] = job
            self._flush()

    def get(self, job_id: str) -> ExportJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, *, status: str, output_path: str | None = None) -> ExportJob | None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            job.status = status
            if output_path is not None:
                job.output_path = output_path
            job.updated_at = _now_iso()
            self._flush()
            return job

    def list_all(self) -> List[ExportJob]:
        with self._lock:
            return list(self._jobs.values())
