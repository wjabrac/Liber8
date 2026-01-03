import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from src.cli import main


class TestCliSmoke(unittest.TestCase):
    def test_run_creates_output_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "run"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(
                    [
                        "run",
                        "cli task",
                        "--storage",
                        str(storage_dir),
                        "--fake",
                        "--print-json",
                    ]
                )
            self.assertEqual(exit_code, 0)
            self.assertTrue((storage_dir / "eventlog.jsonl").exists())
            self.assertTrue((storage_dir / "memory.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
