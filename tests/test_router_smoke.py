import tempfile
import unittest
from pathlib import Path

from src.orchestration.router import run_router


class TestRouterSmoke(unittest.TestCase):
    def test_router_runs_via_canonical_engine(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run"
            event = run_router("hello router", run_dir, fake_backend=True)

            self.assertIn(event.outcome, ["success", "degraded"])
            self.assertEqual(Path(event.provenance["run_artifact_dir"]), run_dir)
            self.assertTrue((run_dir / "eventlog.jsonl").exists())
            self.assertTrue((run_dir / "memory.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
