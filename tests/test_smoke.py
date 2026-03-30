import tempfile
import unittest
from pathlib import Path

from src.cognition_loop import run_cognition_loop
from src.eventlog import EventLog
from src.memory_adapter import FileSystemMemoryAdapter


class SmokeTest(unittest.TestCase):
    def test_cognition_loop_fallback_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)
            record = run_cognition_loop("summarize last task", storage_dir, cognition_backend="fallback")

            # Find the generated run_dir
            run_dirs = list((storage_dir / ".runs").glob("*"))
            self.assertEqual(len(run_dirs), 1)
            run_dir = run_dirs[0]

            log_records = EventLog(run_dir / "eventlog.jsonl").read_all()
            memory_blocks = FileSystemMemoryAdapter(run_dir / "memory.jsonl").read(record.tags)

        self.assertEqual(record.outcome, "success")
        self.assertGreaterEqual(len(log_records), 1)
        self.assertGreaterEqual(len(memory_blocks), 1)


if __name__ == "__main__":
    unittest.main()
