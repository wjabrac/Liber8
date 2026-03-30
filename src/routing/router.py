"""Small-agents router v1 with decision logging."""

from typing import Tuple
from src.trace import DecisionPoint
from .contracts import RouterInput, RouterOutput


class Router:
    """Determines downstream bounded worker execution based on Task and context."""
    
    def __init__(self, fake_backend: bool = False):
        self.fake_backend = fake_backend

    def route(self, router_input: RouterInput) -> Tuple[RouterOutput, DecisionPoint]:
        """
        Executes routing rules and returns the decision alongside a DecisionPoint for tracing.
        Currently implements deterministic rules to preserve fake_backend operations, 
        plus dummy real pathways for CX-010 validation until DSPy is integrated.
        """
        if self.fake_backend:
            output = RouterOutput(
                agents=["synthesizer"],
                routing_reason="fake_backend_deterministic",
                decomposition=[{"step": "synthesize_only", "agent": "synthesizer"}],
                confidence=1.0,
                fallback_used=True
            )
        else:
            intent = router_input.tags.tags.get("intent", "default")
            
            if intent == "no_agent":
                output = RouterOutput(
                    agents=[],
                    routing_reason="direct_synthesis_route",
                    decomposition=[],
                    confidence=0.9,
                    fallback_used=False
                )
            elif intent == "multi_agent":
                output = RouterOutput(
                    agents=["researcher", "synthesizer"],
                    routing_reason="multi_agent_route",
                    decomposition=[
                        {"step": "research", "agent": "researcher"},
                        {"step": "synthesize", "agent": "synthesizer"}
                    ],
                    confidence=0.85,
                    fallback_used=False
                )
            else:
                output = RouterOutput(
                    agents=["synthesizer"],
                    routing_reason="single_agent_route",
                    decomposition=[{"step": "process_task", "agent": "synthesizer"}],
                    confidence=0.95,
                    fallback_used=False
                )
                
        dp = DecisionPoint(
            name="routing",
            inputs_summary={
                "task_preview": router_input.task[:20],
                "retrieved_count": len(router_input.retrieved_blocks)
            },
            choice={
                "agents": output.agents,
                "routing_reason": output.routing_reason,
                "fallback_used": output.fallback_used
            },
            rationale="Routed based on backend mode and TagSet intent."
        )
        
        return output, dp
