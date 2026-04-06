import tempfile
import time
import unittest
from pathlib import Path

from src.service.app import Libr8Service
from src.service.config import ServiceConfig


class TestServiceApp(unittest.TestCase):
    def test_health_reports_api_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir, cognition_backend="fallback"))
            health = service.health()

            self.assertEqual(health["service_type"], "api")
            self.assertEqual(health["backend"], "fallback")
            self.assertEqual(health["status"], "ok")

    def test_health_reports_planned_postgres_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Unreachable postgres should result in degraded status
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir, state_store_backend="postgres", postgres_dsn="postgres://example"))
            health = service.health()

            self.assertEqual(health["state_store"]["backend"], "postgres")
            self.assertEqual(health["status"], "degraded")
            self.assertFalse(health["state_store_reachable"])

    def test_health_reports_unreachable_postgres(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Invalid DSN/port to force a timeout/failure
            service = Libr8Service(ServiceConfig(
                storage_dir=tmpdir, 
                state_store_backend="postgres", 
                postgres_dsn="postgres://postgres:password@127.0.0.1:54321/nonexistent"
            ))
            health = service.health()
            self.assertEqual(health["status"], "degraded")
            self.assertFalse(health["state_store_reachable"])
            self.assertFalse(health["state_store"]["reachable"])

    def test_submit_task_records_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir, cognition_backend="fallback"))
            result = service.submit_task("summarize architecture")
            record = service.get_task(result["task_id"])

            self.assertEqual(result["status"], "completed")
            self.assertIn(result["outcome"], {"success", "degraded"})
            self.assertIsNotNone(record)
            self.assertTrue(Path(result["artifact_dir"]).exists())
            self.assertTrue(result["artifacts"])

    def test_export_job_processes_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir, cognition_backend="fallback"))
            result = service.submit_task("summarize architecture")
            job = service.submit_export_job(result["run_id"])
            processed = service.process_export_job(job["job_id"])

            self.assertIsNotNone(processed)
            self.assertEqual(processed["status"], "completed")
            self.assertTrue(Path(processed["output_path"]).exists())

    def test_admin_snapshot_includes_public_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir, postgres_dsn="postgres://example"))
            snapshot = service.admin_snapshot()

            self.assertIn("config", snapshot)
            self.assertTrue(snapshot["config"]["postgres_dsn_configured"])

    def test_approval_and_export_queues_persist_on_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir, cognition_backend="fallback"))
            approval = service.submit_approval("task-1", "tool.write", "needs approval")
            run = service.submit_task("summarize architecture")
            job = service.submit_export_job(run["run_id"])

            restarted = Libr8Service(ServiceConfig(storage_dir=tmpdir, cognition_backend="fallback"))
            pending = restarted.list_pending_approvals()
            jobs = restarted.list_export_jobs()

            self.assertEqual(len(pending["pending"]), 1)
            self.assertEqual(pending["pending"][0]["request_id"], approval["request_id"])
            self.assertEqual(len(jobs["jobs"]), 1)
            self.assertEqual(jobs["jobs"][0]["job_id"], job["job_id"])

    def test_submit_task_async_records_and_completes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir, cognition_backend="fallback"))
            queued = service.submit_task_async("summarize architecture")
            self.assertEqual(queued["status"], "queued")

            deadline = time.time() + 3
            record = None
            while time.time() < deadline:
                record = service.get_task(queued["task_id"])
                if record and record["status"] in {"completed", "failed"}:
                    break
                time.sleep(0.05)

            self.assertIsNotNone(record)
            self.assertIn(record["status"], {"completed", "failed"})


if __name__ == "__main__":
    unittest.main()
