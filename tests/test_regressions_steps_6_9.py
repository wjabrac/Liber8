import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from src.cli import main as cli_main
from src.cognition.config import EngineConfig
from src.orchestration.router import run_router


class TestRegressionsSteps6To9(unittest.TestCase):
    def test_router_wrapper_uses_canonical_engine(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "router-run"
            event = run_router("compat route", run_dir, fake_backend=True)
        self.assertEqual(Path(event.provenance["run_artifact_dir"]), run_dir)
        self.assertIn(event.outcome, {"success", "degraded"})

    def test_path_allowlists_are_project_root_derived_or_env_driven(self) -> None:
        default_config = EngineConfig()
        self.assertTrue(default_config.path_allowlists)
        self.assertTrue(default_config.path_allowlists[0].endswith("LIBR8"))

        with mock.patch.dict(os.environ, {"LIBR8_PATH_ALLOWLIST": os.pathsep.join(["/tmp/alpha", "/tmp/beta"])}):
            env_config = EngineConfig()
        self.assertEqual(env_config.path_allowlists, ["/tmp/alpha", "/tmp/beta"])

    def test_run_command_prints_exact_artifact_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "storage"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                rc = cli_main(["run", "artifact path", "--storage-dir", str(storage_dir), "--backend", "fallback"])
            self.assertEqual(rc, 0)
            run_dirs = list((storage_dir / ".runs").glob("*"))
            self.assertEqual(len(run_dirs), 1)
            self.assertIn(str(run_dirs[0]), stdout.getvalue())

    def test_benchmark_command_performs_real_work(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            rc = cli_main(["benchmark", "--target", "smoke"])
        output = stdout.getvalue()
        self.assertEqual(rc, 0)
        self.assertIn("Benchmark outcome", output)
        self.assertIn("Run artifacts", output)


if __name__ == "__main__":
    unittest.main()
