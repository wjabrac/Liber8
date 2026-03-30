"""Tests for verifying mid-process interruptions are safely resumable."""
import unittest
import tempfile
import sys
from unittest import mock
from pathlib import Path
from src.cognition.config import EngineConfig
from src.cognition.engine import CognitionEngine
from src.runs.state import RunState

class TestCrashDurability(unittest.TestCase):
    def test_resume_from_interruption(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "durability_run"
            config = EngineConfig(cognition_backend="fallback")
            engine = CognitionEngine(config)
            
            # Monkey patch router to simulate a catastrophic crush midway through step 4
            def crash_route(*args, **kwargs):
                raise KeyboardInterrupt("simulated unhandled process crash")
            
            with mock.patch.object(engine.router, "route", side_effect=crash_route):
                with self.assertRaises(KeyboardInterrupt):
                    engine.run("Test resumption", run_dir)
                    
            state = RunState.load(run_dir)
            self.assertEqual(state.current_step, 4)
            self.assertEqual(state.status, "running")
            
            event = engine.resume_run(run_dir)
            self.assertEqual(event.outcome, "success")
            self.assertTrue(event.provenance.get("backend") == "fallback")

if __name__ == "__main__":
    unittest.main()
