import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.cli import main as cli_main
from src.cognition.config import EngineConfig
from src.cognition.engine import CognitionEngine
from src.runs.session import create_run_dir, list_run_dirs


class TestCliOps(unittest.TestCase):
    def test_healthcheck_reports_ready_local_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                rc = cli_main(["healthcheck", "--storage-dir", tmpdir, "--backend", "fallback"])

            output = stdout.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn("healthcheck_status: ok", output)
            self.assertIn("tool_policy_mode: write", output)
            self.assertIn("tool_protocol: mcp", output)
            self.assertIn("versioning_mode: composite", output)
            self.assertIn("service_readyz_status_code: 200", output)
            self.assertIn("service_readyz_status: ok", output)

    def test_service_health_reports_api_shape(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                rc = cli_main(["service-health", "--storage-dir", tmpdir, "--backend", "fallback"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(rc, 0)
            self.assertEqual(payload["service_type"], "api")
            self.assertEqual(payload["backend"], "fallback")

    def test_admin_snapshot_reports_redacted_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                rc = cli_main(["admin-snapshot", "--storage-dir", tmpdir, "--backend", "fallback"])

            payload = json.loads(stdout.getvalue())
            self.assertEqual(rc, 0)
            self.assertIn("config", payload)
            self.assertIn("postgres_dsn_configured", payload["config"])

    def test_list_migrations_reports_sql_assets(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            rc = cli_main(["list-migrations"])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(rc, 0)
        self.assertTrue(payload["postgres"])
        self.assertTrue(any(item["name"] == "001_service_schema.sql" for item in payload["postgres"]))

    def test_run_emits_run_manifest_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "manifest-run"
            event = CognitionEngine(EngineConfig(cognition_backend="fallback")).run("summarize architecture", run_dir)

            manifest_path = run_dir / "run_manifest.json"
            trace_path = run_dir / "trace.jsonl"
            self.assertTrue(manifest_path.exists())
            self.assertTrue(trace_path.exists())

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            trace_lines = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            trace = trace_lines[-1]

            self.assertEqual(manifest["run_id"], run_dir.name)
            self.assertEqual(manifest["status"], "completed")
            self.assertEqual(manifest["backend"], event.provenance["backend"])
            self.assertIn("eventlog", manifest["artifacts"])
            self.assertIn("run_manifest", manifest["artifacts"])
            self.assertEqual(manifest["summary"]["evaluation_outcome"], "ok")
            self.assertGreaterEqual(manifest["summary"]["persisted_memory_count"], 1)
            self.assertIn("core_engine", manifest["version_info"])
            self.assertTrue(trace["execution_spans"])
            self.assertIn("version_info", trace["provenance"])

    def test_prune_runs_dry_run_preserves_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)
            for _ in range(3):
                create_run_dir(storage_dir)

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                rc = cli_main(["prune-runs", "--storage-dir", str(storage_dir), "--keep", "1", "--dry-run"])

            self.assertEqual(rc, 0)
            self.assertEqual(len(list_run_dirs(storage_dir)), 3)
            self.assertIn("Runs removable: 2", stdout.getvalue())

    def test_prune_runs_removes_older_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)
            for _ in range(4):
                create_run_dir(storage_dir)

            rc = cli_main(["prune-runs", "--storage-dir", str(storage_dir), "--keep", "2"])

            self.assertEqual(rc, 0)
            self.assertEqual(len(list_run_dirs(storage_dir)), 2)

    def test_export_writes_report_with_key_sections(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "report-run"
            CognitionEngine(EngineConfig(cognition_backend="fallback")).run("summarize architecture", run_dir)

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                rc = cli_main(["export", str(run_dir)])

            report_path = run_dir / "report.md"
            report = report_path.read_text(encoding="utf-8")

            self.assertEqual(rc, 0)
            self.assertTrue(report_path.exists())
            self.assertIn("## Tags", report)
            self.assertIn("## Routing Decisions", report)
            self.assertIn("## Retrieval Stats", report)
            self.assertIn("## Failures", report)
            self.assertIn("## Writeback Summary", report)
            self.assertIn("## Artifact Paths", report)
            self.assertIn("Report written to:", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
