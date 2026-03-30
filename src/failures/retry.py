"""Retry Policy Engine."""

from typing import Tuple
from .contracts import FailureClass
from src.trace import DecisionPoint
from src.cognition.config import EngineConfig

class RetryPolicyEngine:
    """Evaluates categorized failures against the decision matrix."""
    
    def __init__(self, config: EngineConfig):
        self.config = config

    def evaluate(self, failure: FailureClass, attempt: int) -> Tuple[str, DecisionPoint]:
        decision = "stop"
        
        if failure in (FailureClass.transient_io, FailureClass.transient_model, FailureClass.transient_rate_limit):
            limit = self.config.retry_max_attempts
            if failure == FailureClass.transient_rate_limit:
                limit = 5  # As per spec scenario 1
                
            if attempt <= limit:
                decision = "exponential_backoff"
            else:
                decision = "switch_tier" if failure != FailureClass.transient_io else "stop"
                
        elif failure == FailureClass.tool_execution_error:
            if attempt <= 1:
                decision = "retry_fixed"
            else:
                decision = "switch_tool"
                
        elif failure == FailureClass.memory_backend_unavailable:
            decision = "enter_degraded_mode"
            
        elif failure in (FailureClass.deterministic_validation_failure, FailureClass.tool_permission_denied):
            decision = "ask_for_approval"
            
        elif failure in (FailureClass.deterministic_contract_violation, FailureClass.planner_inconsistent, FailureClass.unknown):
            decision = "stop"
            
        dp = DecisionPoint(
            name="retry_decision" if decision != "enter_degraded_mode" else "degraded_transition",
            inputs_summary={
                "failure_class": failure.value, 
                "attempt": attempt, 
                "max_retries": self.config.retry_max_attempts
            },
            choice={"decision": decision},
            rationale="Evaluated failure according to v0.1 retry policy matrix."
        )
        return decision, dp
