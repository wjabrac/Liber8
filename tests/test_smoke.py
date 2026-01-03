import tempfile
import unittest
from pathlib import Path

from src.cognition_loop import run_cognition_loop
from src.eventlog import EventLog
from src.memory_adapter import FileSystemMemoryAdapter


class SmokeTest(unittest.TestCase):
    def test_cognition_loop_fake_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir)
            record = run_cognition_loop("summarize last task", storage_dir, fake_backend=True)

            log_records = EventLog(storage_dir / "eventlog.jsonl").read_all()
            memory_blocks = FileSystemMemoryAdapter(storage_dir / "memory.jsonl").read(record.tags)

        self.assertEqual(record.outcome, "success")
        self.assertGreaterEqual(len(log_records), 1)
        self.assertGreaterEqual(len(memory_blocks), 1)


if __name__ == "__main__":
    unittest.main()
