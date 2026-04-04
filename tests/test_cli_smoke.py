import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from main import main as app_main
from src.cli import main as cli_main


class TestCliSmoke(unittest.TestCase):
    def test_cli_and_main_share_run_interface(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "run"
            argv = ["run", "cli task", "--storage-dir", str(storage_dir), "--backend", "fallback"]

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                cli_exit_code = cli_main(argv)
                app_exit_code = app_main(argv)

            output = stdout.getvalue()
            run_dirs = list((storage_dir / ".runs").glob("*"))

            self.assertEqual(cli_exit_code, 0)
            self.assertEqual(app_exit_code, 0)
            self.assertEqual(len(run_dirs), 2)
            for run_dir in run_dirs:
                self.assertTrue((run_dir / "eventlog.jsonl").exists())
                self.assertTrue((run_dir / "memory.jsonl").exists())
                self.assertIn(str(run_dir), output)


if __name__ == "__main__":
    unittest.main()
