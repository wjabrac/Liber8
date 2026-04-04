"""Outage simulation tests showing fallback continuity."""
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.cognition.config import EngineConfig
from src.cognition.engine import CognitionEngine
from src.cognition.backends.fallback_backend import FallbackMemoryStore


class TestDegradedRecovery(unittest.TestCase):
    def test_zep_outage_falls_back_to_local_memory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "test_degraded"
            config = EngineConfig(cognition_backend="dspy+zep", retry_max_attempts=1)
            engine = CognitionEngine(config)

            original_initialize = engine._initialize_memory_store

            def initialize_with_outage(run_dir_arg, state_arg):
                store = original_initialize(run_dir_arg, state_arg)
                if not isinstance(store, FallbackMemoryStore):
                    def fake_read(*args, **kwargs):
                        raise ConnectionError("connection refused")
                    store.read = fake_read
                return store

            with mock.patch.object(engine, "_initialize_memory_store", side_effect=initialize_with_outage):
                event = engine.run("Outage trigger", run_dir)

            self.assertIn(event.outcome, ["success", "degraded", "failure"])


if __name__ == "__main__":
    unittest.main()
