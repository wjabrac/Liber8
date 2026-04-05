import tempfile
import unittest
import os

from src.service.app import Libr8Service
from src.service.config import ServiceConfig
from src.service.migrations import MigrationRunner

class TestLivePostgres(unittest.TestCase):
    def setUp(self):
        self.dsn = os.environ.get("TEST_POSTGRES_DSN", "postgres://postgres:mysecretpassword@127.0.0.1:5432/libr8_test")
        
    @unittest.skipUnless(os.environ.get("LIVE_POSTGRES"), "Requires active PostgreSQL to test live store")
    def test_postgres_store_records_and_updates_run(self) -> None:
        MigrationRunner(self.dsn).apply_migrations()
        with tempfile.TemporaryDirectory() as tmpdir:
            service = Libr8Service(ServiceConfig(
                storage_dir=tmpdir, 
                cognition_backend="fallback",
                state_store_backend="postgres",
                postgres_dsn=self.dsn
            ))
            
            # submit task
            result = service.submit_task("live postgres test task")
            self.assertEqual(result["status"], "completed")
            
            # verify record saved in DB
            record = service.state.get_record(result["task_id"])
            self.assertIsNotNone(record)
            self.assertEqual(record.task, "live postgres test task")
            self.assertEqual(record.outcome, result["outcome"])
            health = service.health()
            self.assertEqual(health["status"], "ok")
            self.assertTrue(health["state_store"]["database_available"])
            self.assertTrue(health["state_store"]["schema_ready"])

if __name__ == "__main__":
    unittest.main()
