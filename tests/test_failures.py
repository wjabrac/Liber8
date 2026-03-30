"""Tests for failures module."""

import unittest
from src.failures.contracts import FailureClass
from src.failures.classifier import FailureClassifier
from src.failures.retry import RetryPolicyEngine
from src.contracts.errors import ValidationError
from src.cognition.config import EngineConfig

class TestFailures(unittest.TestCase):
    def setUp(self):
        self.classifier = FailureClassifier()
        self.config = EngineConfig(retry_max_attempts=3)
        self.retry_engine = RetryPolicyEngine(self.config)

    def test_classifier_validation_error(self):
        exc = ValidationError("TagSet is invalid")
        fc, context = self.classifier.classify(exc)
        self.assertEqual(fc, FailureClass.deterministic_validation_failure)

    def test_classifier_rate_limit(self):
        exc = Exception("HTTP 429 Too Many Requests")
        fc, context = self.classifier.classify(exc)
        self.assertEqual(fc, FailureClass.transient_rate_limit)

    def test_retry_policy_rate_limit(self):
        decision, dp = self.retry_engine.evaluate(FailureClass.transient_rate_limit, attempt=2)
        self.assertEqual(decision, "exponential_backoff")
        
        # Max retries exceeded
        decision, dp = self.retry_engine.evaluate(FailureClass.transient_rate_limit, attempt=6)
        self.assertEqual(decision, "switch_tier")

    def validation_error_escalates(self):
        decision, dp = self.retry_engine.evaluate(FailureClass.deterministic_validation_failure, attempt=1)
        self.assertEqual(decision, "ask_for_approval")

if __name__ == "__main__":
    unittest.main()
