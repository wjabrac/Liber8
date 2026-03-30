"""Import-time verification tests."""
import unittest

class TestImportVerification(unittest.TestCase):
    def test_interfaces_import(self):
        from src.cognition.interfaces import TagExtractor, QueryPlanner, RouterPolicyProvider, Synthesizer, Evaluator, MemoryStore
        self.assertTrue(True)

    def test_dspy_backend_import(self):
        from src.cognition.backends.dspy_backend import DSPY_AVAILABLE
        if DSPY_AVAILABLE:
            from src.cognition.backends.dspy_backend import DSPyTagExtractor

    def test_zep_backend_import(self):
        from src.memory.backends.zep_backend import ZEP_AVAILABLE
        if ZEP_AVAILABLE:
            from src.memory.backends.zep_backend import ZepMemoryStore

    def test_fallback_backend_import(self):
        from src.cognition.backends.fallback_backend import FallbackTagExtractor
        self.assertTrue(True)
