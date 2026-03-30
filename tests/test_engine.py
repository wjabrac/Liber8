import unittest
import tempfile
import json
from pathlib import Path
from src.cognition.engine import CognitionEngine
from src.cognition.config import EngineConfig

class TestCognitionEngine(unittest.TestCase):
    def test_engine_run_produces_artifacts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "test_run"
            config = EngineConfig(cognition_backend="fallback")
            engine = CognitionEngine(config)
            
            event = engine.run("Test the engine", run_dir)
            
            self.assertEqual(event.outcome, "success")
            self.assertTrue((run_dir / "meta.json").exists())
            self.assertTrue((run_dir / "eventlog.jsonl").exists())
            self.assertTrue((run_dir / "trace.jsonl").exists())
            self.assertTrue((run_dir / "memory.jsonl").exists())
            
            # Verify parsing
            with (run_dir / "meta.json").open() as f:
                meta = json.load(f)
                self.assertEqual(meta["run_id"], "test_run")
            
            # Verify trace parsing
            with (run_dir / "trace.jsonl").open() as f:
                trace_lines = f.readlines()
                self.assertEqual(len(trace_lines), 1)
                trace_data = json.loads(trace_lines[0])
                self.assertIn("trace_id", trace_data)
                self.assertEqual(trace_data["outcome"], "success")

if __name__ == "__main__":
    unittest.main()
