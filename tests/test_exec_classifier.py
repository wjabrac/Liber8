import unittest

from src.execution.classifier import classify_command


class TestExecClassifier(unittest.TestCase):
    def test_read_only_commands(self) -> None:
        self.assertEqual(classify_command("ls"), "read_only")
        self.assertEqual(classify_command("git status"), "read_only")
        self.assertEqual(classify_command("python -m unittest"), "read_only")

    def test_network_commands(self) -> None:
        self.assertEqual(classify_command("curl https://example.com"), "network")
        self.assertEqual(classify_command("pip install requests"), "network")

    def test_destructive_commands(self) -> None:
        self.assertEqual(classify_command("rm -rf /tmp/test"), "destructive")
        self.assertEqual(classify_command("git reset --hard"), "destructive")
        self.assertEqual(classify_command("ls && rm -rf /tmp/test"), "destructive")


if __name__ == "__main__":
    unittest.main()
