import tempfile
import unittest
from pathlib import Path

from src.cognition.config import EngineConfig
from src.cognition.engine import CognitionEngine


class TestEngineE2E(unittest.TestCase):
    def test_end_to_end_run_writes_core_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "e2e-run"
            event = CognitionEngine(EngineConfig(cognition_backend="fallback")).run("summarize architecture", run_dir)

            self.assertIn(event.outcome, {"success", "degraded"})
            self.assertTrue((run_dir / "meta.json").exists())
            self.assertTrue((run_dir / "eventlog.jsonl").exists())
            self.assertTrue((run_dir / "trace.jsonl").exists())
            self.assertTrue((run_dir / "memory.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
