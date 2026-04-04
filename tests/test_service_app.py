import tempfile
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
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir, state_store_backend="postgres", postgres_dsn="postgres://example"))
            health = service.health()

            self.assertEqual(health["state_store"]["backend"], "postgres")
            self.assertFalse(health["state_store"]["implemented"])

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


if __name__ == "__main__":
    unittest.main()
