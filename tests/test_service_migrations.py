import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from src.service.migrations import MigrationFile, MigrationHashMismatchError, MigrationRunner


class TestServiceMigrations(unittest.TestCase):
    def test_apply_migrations_raises_on_hash_mismatch(self) -> None:
        runner = object.__new__(MigrationRunner)
        runner.dsn = "postgres://unit-test"
        runner._migrations_root = None

        migration = MigrationFile(name="001_schema.sql", path="/tmp/001_schema.sql", sha256="new-hash")

        with mock.patch.object(runner, "get_applied_migrations", return_value={"001_schema.sql": "old-hash"}):
            with mock.patch.object(runner, "_available_migrations", return_value=[migration]):
                with self.assertRaises(MigrationHashMismatchError):
                    runner.apply_migrations()

    def test_custom_migration_root_discovers_sql_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            file_path = root / "001_test.sql"
            file_path.write_text("SELECT 1;", encoding="utf-8")

            runner = object.__new__(MigrationRunner)
            runner.dsn = "postgres://unit-test"
            runner._migrations_root = root

            migrations = runner._available_migrations()
            self.assertEqual(len(migrations), 1)
            self.assertEqual(migrations[0].name, "001_test.sql")
            self.assertEqual(migrations[0].sha256, hashlib.sha256(b"SELECT 1;").hexdigest())


if __name__ == "__main__":
    unittest.main()
