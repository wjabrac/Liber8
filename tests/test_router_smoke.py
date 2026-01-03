import tempfile
import unittest
from pathlib import Path

from src.orchestration.router import run_router


class TestRouterSmoke(unittest.TestCase):
    def test_router_runs_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "run"
            event = run_router("hello router", storage_dir, fake_backend=True)

            self.assertEqual(event.actions[-1], "event_log")
            self.assertEqual(event.actions[:4], ["tag_extraction", "memory_read", "synthesis", "memory_write"])
            self.assertTrue((storage_dir / "eventlog.jsonl").exists())
            self.assertTrue((storage_dir / "memory.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
