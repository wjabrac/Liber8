"""Application service wrapper for LIBR8."""

from __future__ import annotations

import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional

from src.cognition.engine import CognitionEngine
from src.export import export_run_report
from src.ops.logging import JsonLogger
from src.ops.retention import RunRetentionPolicy, plan_run_prune
from src.runs.session import list_run_dirs
from src.service.artifacts import index_run_artifacts
from src.service.config import ServiceConfig
from src.service.models import RunRecord
from src.service.state import ServiceStateStore, build_state_store
from src.service.migrations import MigrationRunner
from src.service.workflows.approvals import ApprovalRequest, InMemoryApprovalQueue, FileBackedApprovalQueue
from src.service.workflows.exports import ExportJob, InMemoryExportJobQueue, FileBackedExportJobQueue


class Libr8Service:
    def __init__(
        self,
        config: ServiceConfig,
        *,
        state_store: ServiceStateStore | None = None,
        logger: JsonLogger | None = None,
        approval_queue: InMemoryApprovalQueue | FileBackedApprovalQueue | None = None,
        export_queue: InMemoryExportJobQueue | FileBackedExportJobQueue | None = None,
    ) -> None:
        self.config = config
        self.state_store = state_store or build_state_store(config.state_store_backend, config.postgres_dsn)
        self.state = self.state_store
        self.logger = logger or JsonLogger()
        self.storage_dir = Path(config.storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._service_state_dir = self.storage_dir / ".service_state"
        self._service_state_dir.mkdir(parents=True, exist_ok=True)
        self.approval_queue = approval_queue or FileBackedApprovalQueue(self._service_state_dir / "approvals.json")
        self.export_queue = export_queue or FileBackedExportJobQueue(self._service_state_dir / "exports.json")
        self._async_executor: ThreadPoolExecutor | None = None
        self._async_futures: Dict[str, Future[Dict[str, Any]]] = {}
        self._async_lock = Lock()

        if config.auto_migrate and config.postgres_dsn:
            try:
                runner = MigrationRunner(config.postgres_dsn)
                applied = runner.apply_migrations()
                if applied:
                    self.logger.emit("auto_migration_complete", applied_count=len(applied))
            except Exception as e:
                self.logger.emit("auto_migration_failed", error=str(e))

    def _build_engine(self) -> CognitionEngine:
        return CognitionEngine(self.config.to_engine_config())

    def _new_record(self, task: str, status: str) -> tuple[str, Path, RunRecord]:
        task_id = str(uuid.uuid4())
        run_dir = self.storage_dir / ".runs" / task_id
        record = RunRecord(task_id=task_id, run_id=run_dir.name, task=task, status=status, artifact_dir=str(run_dir))
        self.state_store.record_submission(record)
        return task_id, run_dir, record

    def _execute_task(self, task_id: str, task: str, run_dir: Path) -> Dict[str, Any]:
        self.logger.emit("task_submitted", task_id=task_id, task=task, run_id=run_dir.name)

        engine = self._build_engine()
        event = engine.run(task, run_dir)
        updated = self.state_store.update_record(
            task_id,
            status="completed" if event.outcome in {"success", "degraded"} else "failed",
            outcome=event.outcome,
            failure_class=event.failure_class,
            artifact_dir=str(run_dir),
        )
        artifact_records = [record.to_dict() for record in index_run_artifacts(run_dir)]
        self.logger.emit("task_completed", task_id=task_id, run_id=run_dir.name, outcome=event.outcome)
        return {
            "task_id": task_id,
            "run_id": run_dir.name,
            "status": updated.status if updated else record.status,
            "outcome": event.outcome,
            "artifact_dir": str(run_dir),
            "failure_class": event.failure_class,
            "artifacts": artifact_records,
        }

    def submit_task(self, task: str) -> Dict[str, Any]:
        task_id, run_dir, _ = self._new_record(task, "running")
        return self._execute_task(task_id, task, run_dir)

    def _ensure_async_executor(self) -> ThreadPoolExecutor:
        if self._async_executor is None:
            self._async_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="libr8-task")
        return self._async_executor

    def _run_async_task(self, task_id: str, task: str, run_dir: Path) -> Dict[str, Any]:
        self.state_store.update_record(task_id, status="running")
        try:
            return self._execute_task(task_id, task, run_dir)
        finally:
            with self._async_lock:
                self._async_futures.pop(task_id, None)

    def submit_task_async(self, task: str) -> Dict[str, Any]:
        task_id, run_dir, _ = self._new_record(task, "queued")
        future = self._ensure_async_executor().submit(self._run_async_task, task_id, task, run_dir)
        with self._async_lock:
            self._async_futures[task_id] = future
        self.logger.emit("task_queued", task_id=task_id, task=task, run_id=run_dir.name)
        return {
            "task_id": task_id,
            "run_id": run_dir.name,
            "status": "queued",
            "artifact_dir": str(run_dir),
            "outcome": None,
            "failure_class": None,
            "artifacts": [],
        }

    def get_task(self, task_id: str) -> Dict[str, Any] | None:
        record = self.state_store.get_record(task_id)
        return record.to_dict() if record else None

    def submit_approval(self, task_id: str, scope: str, reason: str) -> Dict[str, Any]:
        request = ApprovalRequest(request_id=str(uuid.uuid4()), task_id=task_id, scope=scope, reason=reason)
        self.approval_queue.submit(request)
        self.logger.emit("approval_submitted", task_id=task_id, request_id=request.request_id, scope=scope)
        return request.to_dict()

    def resolve_approval(self, request_id: str, status: str) -> Dict[str, Any] | None:
        request = self.approval_queue.resolve(request_id, status)
        if request is None:
            return None
        self.logger.emit("approval_resolved", request_id=request.request_id, status=status)
        return request.to_dict()

    def list_pending_approvals(self) -> Dict[str, Any]:
        return {"pending": [request.to_dict() for request in self.approval_queue.pending()]}

    def submit_export_job(self, run_id: str, job_kind: str = "markdown_report") -> Dict[str, Any]:
        job = ExportJob(job_id=str(uuid.uuid4()), run_id=run_id, job_kind=job_kind)
        self.export_queue.submit(job)
        self.logger.emit("export_job_submitted", job_id=job.job_id, run_id=run_id, job_kind=job_kind)
        return job.to_dict()

    def process_export_job(self, job_id: str) -> Dict[str, Any] | None:
        job = self.export_queue.get(job_id)
        if job is None:
            return None
        run_dir = self.storage_dir / ".runs" / job.run_id
        report_path = export_run_report(run_dir)
        updated = self.export_queue.update(job_id, status="completed", output_path=str(report_path))
        self.logger.emit("export_job_completed", job_id=job_id, run_id=job.run_id, output_path=str(report_path))
        return updated.to_dict() if updated else None

    def list_export_jobs(self) -> Dict[str, Any]:
        return {"jobs": [job.to_dict() for job in self.export_queue.list_all()]}

    def admin_snapshot(self) -> Dict[str, Any]:
        return {
            "config": self.config.public_snapshot(),
            "state_store": self.state_store.summary(),
            "approval_queue": self.list_pending_approvals(),
            "export_jobs": self.list_export_jobs(),
        }

    def health(self) -> Dict[str, Any]:
        engine_config = self.config.to_engine_config()
        
        # Check storage writability
        storage_writable = False
        try:
            test_file = self.storage_dir / ".healthcheck"
            test_file.write_text("ok")
            test_file.unlink()
            storage_writable = True
        except Exception:
            storage_writable = False

        state_store_reachable = self.state_store.test_connection()
        isolation_required = self.config.require_isolation_for_writes
        isolation_ready = not (isolation_required and self.config.execution_isolation_backend in {"", "none"})
        default_allowlist = engine_config.path_allowlists[0] if engine_config.path_allowlists else ""
        default_allowlist_exists = bool(default_allowlist) and Path(default_allowlist).exists()

        readiness_reasons: list[str] = []
        if not storage_writable:
            readiness_reasons.append("storage_unwritable")
        if not state_store_reachable:
            readiness_reasons.append("state_store_unreachable")
        if not isolation_ready:
            readiness_reasons.append("isolation_required_but_unconfigured")
        if not default_allowlist_exists:
            readiness_reasons.append("default_allowlist_missing")

        ready = storage_writable and state_store_reachable and isolation_ready
        return {
            "status": "ok" if ready else "degraded",
            "service_type": "api",
            "storage_dir": str(self.storage_dir.resolve()),
            "storage_writable": storage_writable,
            "state_store_reachable": state_store_reachable,
            "backend": self.config.cognition_backend,
            "run_count": len(list_run_dirs(self.storage_dir)),
            "state_store": self.state_store.summary(),
            "approval_queue_depth": len(self.approval_queue.pending()),
            "export_job_count": len(self.export_queue.list_all()),
            "require_isolation_for_writes": self.config.require_isolation_for_writes,
            "execution_isolation_backend": self.config.execution_isolation_backend,
            "default_allowlist": default_allowlist,
            "default_allowlist_exists": default_allowlist_exists,
            "readiness_reasons": readiness_reasons,
        }

    def retention_preview(self, policy: Optional[RunRetentionPolicy] = None) -> Dict[str, Any]:
        active_policy = policy or self.config.retention_policy
        decisions = plan_run_prune(self.storage_dir, active_policy)
        return {
            "policy": {
                "max_age_days": active_policy.max_age_days,
                "max_total_bytes": active_policy.max_total_bytes,
                "keep_minimum": active_policy.keep_minimum,
            },
            "removable": [
                {
                    "run_dir": str(item.run_dir),
                    "reason": item.reason,
                    "size_bytes": item.size_bytes,
                }
                for item in decisions
            ],
        }
