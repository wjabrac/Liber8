"""Operational service state storage contracts."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Protocol

from src.service.models import RunRecord
from src.service.postgres_store import PostgresServiceStateStore


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ServiceStateStore(Protocol):
    def record_submission(self, record: RunRecord) -> None: ...
    def update_record(self, task_id: str, **updates: str | None) -> RunRecord | None: ...
    def get_record(self, task_id: str) -> RunRecord | None: ...
    def summary(self) -> Dict[str, object]: ...


class InMemoryServiceStateStore:
    def __init__(self) -> None:
        self._records: Dict[str, RunRecord] = {}

    def record_submission(self, record: RunRecord) -> None:
        self._records[record.task_id] = record

    def update_record(self, task_id: str, **updates: str | None) -> RunRecord | None:
        record = self._records.get(task_id)
        if record is None:
            return None
        for key, value in updates.items():
            if hasattr(record, key):
                setattr(record, key, value)
        record.updated_at = _now_iso()
        return record

    def get_record(self, task_id: str) -> RunRecord | None:
        return self._records.get(task_id)

    def summary(self) -> Dict[str, object]:
        statuses: Dict[str, int] = {}
        for record in self._records.values():
            statuses[record.status] = statuses.get(record.status, 0) + 1
        return {
            "backend": "memory",
            "records": len(self._records),
            "statuses": statuses,
        }


class PlannedPostgresStateStore:
    def __init__(self, dsn: str | None) -> None:
        self.dsn = dsn or ""
        self._fallback = InMemoryServiceStateStore()

    def record_submission(self, record: RunRecord) -> None:
        self._fallback.record_submission(record)

    def update_record(self, task_id: str, **updates: str | None) -> RunRecord | None:
        return self._fallback.update_record(task_id, **updates)

    def get_record(self, task_id: str) -> RunRecord | None:
        return self._fallback.get_record(task_id)

    def summary(self) -> Dict[str, object]:
        fallback_summary = self._fallback.summary()
        return {
            "backend": "postgres",
            "configured": bool(self.dsn),
            "implemented": False,
            "database_available": False,
            "schema_ready": False,
            "fallback_backend": fallback_summary["backend"],
            "fallback_records": fallback_summary["records"],
            "schema_path": str(postgres_schema_path()),
        }


def build_state_store(backend: str, postgres_dsn: str | None = None) -> ServiceStateStore:
    if backend == "postgres":
        if postgres_dsn:
            try:
                return PostgresServiceStateStore(postgres_dsn)
            except RuntimeError:
                return PlannedPostgresStateStore(postgres_dsn)
        return PlannedPostgresStateStore(postgres_dsn)
    return InMemoryServiceStateStore()


def postgres_schema_path() -> Path:
    return Path(__file__).resolve().parents[2] / "sql" / "postgres" / "001_service_schema.sql"
