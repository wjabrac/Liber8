import tempfile
import time
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

    def test_async_run_submission_route(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir))
            status, payload = dispatch_http_request(service, "POST", "/v1/runs/async", {"task": "summarize architecture"})
            self.assertEqual(status, 202)
            self.assertEqual(payload["status"], "queued")

            deadline = time.time() + 3
            record = None
            while time.time() < deadline:
                lookup_status, record = dispatch_http_request(service, "GET", f"/v1/runs/{payload['task_id']}")
                self.assertEqual(lookup_status, 200)
                if record["status"] in {"completed", "failed"}:
                    break
                time.sleep(0.05)

            self.assertIsNotNone(record)
            self.assertIn(record["status"], {"completed", "failed"})

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

    def test_api_key_auth(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir, api_key="secret-123"))
            
            # 1. Blocked without key
            status, payload = dispatch_http_request(service, "POST", "/v1/runs", {"task": "test"})
            self.assertEqual(status, 401)
            self.assertEqual(payload["error"], "unauthorized")
            
            # 2. Allowed with correct key
            status, payload = dispatch_http_request(
                service, "POST", "/v1/runs", {"task": "test"}, 
                headers={"X-API-Key": "secret-123"}
            )
            self.assertEqual(status, 202)
            
            # 3. Healthz is public
            status, _ = dispatch_http_request(service, "GET", "/healthz")
            self.assertEqual(status, 200)

    def test_local_first_auth_policy(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            # 1. Loopback with no key -> Allowed
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir, host="127.0.0.1", api_key=None))
            status, _ = dispatch_http_request(service, "POST", "/v1/runs", {"task": "test"})
            self.assertEqual(status, 202)

            # 2. Non-loopback with no key -> Denied (403)
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir, host="0.0.0.0", api_key=None))
            status, _ = dispatch_http_request(service, "POST", "/v1/runs", {"task": "test"})
            self.assertEqual(status, 403)

            # 3. Non-loopback with no key + override -> Allowed
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir, host="0.0.0.0", api_key=None, allow_unauthenticated_non_loopback=True))
            status, _ = dispatch_http_request(service, "POST", "/v1/runs", {"task": "test"})
            self.assertEqual(status, 202)

            # 4. Health checks are ALWAYS public even on non-loopback with no key
            service = Libr8Service(ServiceConfig(storage_dir=tmpdir, host="0.0.0.0", api_key=None))
            status, _ = dispatch_http_request(service, "GET", "/healthz")
            self.assertEqual(status, 200)
            status, _ = dispatch_http_request(service, "GET", "/readyz")
            self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main()
