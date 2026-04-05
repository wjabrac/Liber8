import tempfile
import unittest

from src.service.app import Libr8Service
from src.service.config import ServiceConfig
from src.service.http import dispatch_http_request


class TestServiceHttp(unittest.TestCase):
    def test_health_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir))
            status, payload = dispatch_http_request(service, "GET", "/healthz")

            self.assertEqual(status, 200)
            self.assertEqual(payload["service_type"], "api")

    def test_ready_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir))
            status, payload = dispatch_http_request(service, "GET", "/readyz")

            self.assertEqual(status, 200)
            self.assertEqual(payload["status"], "ok")

    def test_run_submission_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir))
            status, payload = dispatch_http_request(service, "POST", "/v1/runs", {"task": "summarize architecture"})
            lookup_status, record = dispatch_http_request(service, "GET", f"/v1/runs/{payload['task_id']}")

            self.assertEqual(status, 202)
            self.assertEqual(lookup_status, 200)
            self.assertEqual(record["task_id"], payload["task_id"])
            self.assertTrue(payload["artifacts"])

    def test_approval_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir))
            create_status, created = dispatch_http_request(service, "POST", "/v1/approvals", {"task_id": "task-1", "scope": "tool.write", "reason": "needs approval"})
            list_status, pending = dispatch_http_request(service, "GET", "/v1/approvals")
            resolve_status, resolved = dispatch_http_request(service, "POST", f"/v1/approvals/{created['request_id']}/resolve", {"status": "approved"})

            self.assertEqual(create_status, 201)
            self.assertEqual(list_status, 200)
            self.assertEqual(resolve_status, 200)
            self.assertEqual(len(pending["pending"]), 1)
            self.assertEqual(resolved["status"], "approved")

    def test_export_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir))
            _, run_payload = dispatch_http_request(service, "POST", "/v1/runs", {"task": "summarize architecture"})
            create_status, created = dispatch_http_request(service, "POST", "/v1/exports", {"run_id": run_payload["run_id"]})
            list_status, jobs = dispatch_http_request(service, "GET", "/v1/exports")
            process_status, processed = dispatch_http_request(service, "POST", f"/v1/exports/{created['job_id']}/process", {})

            self.assertEqual(create_status, 201)
            self.assertEqual(list_status, 200)
            self.assertEqual(process_status, 200)
            self.assertEqual(len(jobs["jobs"]), 1)
            self.assertEqual(processed["status"], "completed")

    def test_admin_routes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir, postgres_dsn="postgres://example"))
            migrations_status, migrations = dispatch_http_request(service, "GET", "/admin/migrations")
            snapshot_status, snapshot = dispatch_http_request(service, "GET", "/admin/snapshot")
            schema_status, schema = dispatch_http_request(service, "GET", "/admin/schema")

            self.assertEqual(migrations_status, 200)
            self.assertEqual(snapshot_status, 200)
            self.assertEqual(schema_status, 200)
            self.assertTrue(migrations["postgres"])
            self.assertIn("config", snapshot)
            self.assertTrue(schema["endpoints"])


if __name__ == "__main__":
    unittest.main()
