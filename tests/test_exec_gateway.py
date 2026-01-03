import unittest

from src.execution.gateway import execute_command


class TestExecGateway(unittest.TestCase):
    def test_blocks_destructive_without_approval(self) -> None:
        result = execute_command("rm -rf /tmp/should-not-run")
        self.assertFalse(result["allowed"])
        self.assertEqual(result["status"], "blocked")

    def test_allows_read_only_command(self) -> None:
        result = execute_command('python -c "print(1)"')
        self.assertTrue(result["allowed"])
        self.assertEqual(result["exit_code"], 0)

    def test_approval_token_allows_command(self) -> None:
        command = 'echo "approved"'
        result = execute_command(command, approval_token=f"APPROVE: {command}")
        self.assertTrue(result["allowed"])
        self.assertEqual(result["exit_code"], 0)


if __name__ == "__main__":
    unittest.main()
