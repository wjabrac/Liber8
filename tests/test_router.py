"""Tests for the routing module."""

import unittest
from src.routing.contracts import RouterInput
from src.routing.router import Router
from src.contracts import TagSet, QueryPlan

class TestRouter(unittest.TestCase):
    def setUp(self):
        self.qp = QueryPlan(filters={}, limits=5, recency_bias=0.5)
    
    def _make_input(self, intent: str) -> RouterInput:
        tags = TagSet(schema_version="v0", tags={"intent": intent})
        return RouterInput(
            task="Test task",
            tags=tags,
            query_plan=self.qp,
            retrieved_blocks=[]
        )

    def test_fake_backend_route(self):
        router = Router(fake_backend=True)
        ri = self._make_input("anything")
        output, dp = router.route(ri)
        
        self.assertTrue(output.fallback_used)
        self.assertEqual(output.agents, ["synthesizer"])
        self.assertEqual(dp.name, "routing")
        self.assertEqual(dp.choice["routing_reason"], "fake_backend_deterministic")

    def test_multi_agent_route(self):
        router = Router(fake_backend=False)
        ri = self._make_input("multi_agent")
        output, dp = router.route(ri)
        
        self.assertFalse(output.fallback_used)
        self.assertEqual(output.agents, ["researcher", "synthesizer"])
        self.assertEqual(output.routing_reason, "multi_agent_route")
        
    def test_no_agent_route(self):
        router = Router(fake_backend=False)
        ri = self._make_input("no_agent")
        output, dp = router.route(ri)
        
        self.assertEqual(output.agents, [])
        self.assertEqual(output.routing_reason, "direct_synthesis_route")

if __name__ == "__main__":
    unittest.main()
