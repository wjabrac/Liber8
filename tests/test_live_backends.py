"""Live integration tests for real backends."""
import os
import unittest
from pathlib import Path
import tempfile
from src.cognition.config import EngineConfig
from src.cognition.engine import CognitionEngine

class TestLiveBackends(unittest.TestCase):
    @unittest.skipUnless(os.environ.get("RESTRICT_LIVE_TESTS") == "1", "Live tests require RESTRICT_LIVE_TESTS=1")
    def test_live_dspy_zep_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "live_run"
            config = EngineConfig(cognition_backend="dspy+zep")
            engine = CognitionEngine(config)
            event = engine.run("Live architecture summary test", run_dir)
            self.assertEqual(event.outcome, "success")
            self.assertIn("trace_id", event.provenance)
