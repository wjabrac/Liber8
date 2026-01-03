# AG-004 — Failure classes and retry policy v0

Goal
Define a failure taxonomy and retry decision matrix that can be implemented directly using EventRecord fields.

Inputs
- src/contracts.py (EventRecord, ValidationError)
- AG_EXTRACT/analysis/resilience_primitives.md and evaluation_primitives.md (if present)
- work_orders/codeex/002_cognition_loop.md (context for loop steps)

Deliverable
- spec/failure_retry_policy_v0.md

Required taxonomy (minimum)
- parse_error
- validation_error
- retrieval_error
- tool_error
- environment_error
- rate_limit
- timeout
- user_approval_required
- unknown_error

Required decision matrix
For each failure_class define:
- retry_allowed: yes/no
- max_retries default
- backoff strategy (none, fixed, exponential)
- escalation target (stop, ask for approval, switch tier, switch tool)
- required event provenance fields to record

Required "stop rules"
- repeated identical failure signature
- cost ceiling exceeded
- safety gate hit without approval token
- missing required environment variable for non-fake mode

Acceptance criteria
- Another developer can implement a classify_failure(exc, context) -> failure_class and etry_decision(event) -> action from this doc.
- Contains at least 10 example scenarios mapping error text and context to failure_class and decision.
- No code changes.

Do-not-do
- Do not introduce broad philosophical content. This is an operational policy spec.
