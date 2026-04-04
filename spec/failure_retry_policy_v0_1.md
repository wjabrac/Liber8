# Failure Taxonomy and Retry Policy v0.1

**Purpose**: Define the failure classes, retry decision matrix, stop rules, and degraded mode transitions to govern LIBR8's behavior upon encountering errors during the cognition loop.

## 1. Failure Taxonomy & Decision Matrix

Each exception encountered during execution maps deterministically to one of the following `failure_class` categories.

| `failure_class` | `retry_allowed` | `max_retries` | `backoff_strategy` | `escalation_target` | Provenance Fields to Record |
| --- | --- | --- | --- | --- | --- |
| **`transient_io`** | yes | 3 | exponential | stop | `endpoint_url`, `error_code` |
| **`transient_model`** | yes | 3 | exponential | switch tier | `model_name`, `provider` |
| **`transient_rate_limit`** | yes | 5 | exponential | switch tier | `retry_after`, `tier` |
| **`deterministic_contract_violation`** | no | 0 | none | stop | `contract_version`, `violation_details` |
| **`deterministic_validation_failure`** | no | 0 | none | ask for approval | `failing_validator`, `validation_errors` |
| **`tool_permission_denied`** | no | 0 | none | ask for approval | `tool_name`, `required_perms` |
| **`tool_execution_error`** | yes | 1 | fixed | switch tool | `tool_name`, `stderr_snippet` |
| **`memory_backend_unavailable`** | yes | 3 | fixed | degraded mode | `backend_uri`, `connection_error` |
| **`planner_inconsistent`** | yes | 1 | none | stop | `planner_state`, `inconsistency_type` |
| **`unknown`** | no | 0 | none | stop | `stack_trace`, `exception_type` |

## 2. Stop Rules

Execution immediately halts (superseding the retry policy) if any of the following rules are triggered:
1. **Repeated Identical Failure Signature**: If the exact same failure class and context occurs twice in a row despite retries (indicating a stuck loop).
2. **Cost Ceiling Exceeded**: If the accumulated cost of the run exceeds the user-defined budget threshold.
3. **Safety Gate Hit**: If a safety or ethics validator is triggered and no overriding user approval token is present.
4. **Missing Environment Constraints**: If required environment variables (e.g., `LIBR8_MODEL_ENDPOINT`) are missing while attempting non-fake mode.

## 3. Degraded Mode & Recovery

If the memory or database backend fails (`memory_backend_unavailable`):
1. **Transition**: The system falls back to `degraded` mode immediately (bypassing exponential backoff on primary operations).
2. **Behavior**: In degraded mode, memory reads return empty results, and memory writes are buffered to a local temporary JSONL file.
3. **Recovery Attempt**: Every subsequent loop iteration will perform a health check to the original backend before running. If successful, buffered writes are flushed, and normal operation resumes.

## 4. Scenarios & Trace Entries

### Scenario 1: Model Rate Limit
* **Context**: `LIBR8` makes a call to the LLM but receives a 429 Too Many Requests response.
* **Classification**: `transient_rate_limit`
* **Decision**: Wait with exponential backoff (retry allowed), attempt up to 5 times.
* **Trace Entry**:
  ```json
  {"action": "retry_decision", "failure_class": "transient_rate_limit", "decision": "exponential_backoff", "attempt": 1}
  ```

### Scenario 2: Schema Validation Failure
* **Context**: The LLM outputs JSON that fails to parse against the `QueryPlan` pydantic schema.
* **Classification**: `deterministic_validation_failure`
* **Decision**: Do not retry immediately. Escalate to the user (ask for approval/manual fix).
* **Trace Entry**:
  ```json
  {"action": "retry_decision", "failure_class": "deterministic_validation_failure", "decision": "ask_for_approval", "failing_validator": "QueryPlan"}
  ```

### Scenario 3: Database Connection Refused
* **Context**: The MemoryAdapter or vector DB cannot be accessed.
* **Classification**: `memory_backend_unavailable`
* **Decision**: Transition to degraded mode; start recovery polling.
* **Trace Entry**:
  ```json
  {"action": "degraded_transition", "failure_class": "memory_backend_unavailable", "decision": "enter_degraded_mode"}
  ```

### Scenario 4: Command Execution Fails
* **Context**: A generated Bash command fails with a non-zero exit code (syntax error).
* **Classification**: `tool_execution_error`
* **Decision**: Retry once (fixed 0s backoff) or switch tool.
* **Trace Entry**:
  ```json
  {"action": "retry_decision", "failure_class": "tool_execution_error", "decision": "retry_fixed", "tool_name": "bash"}
  ```

### Scenario 5: Missing Endpoint Config
* **Context**: User runs `main.py` without `fake_backend`, but `LIBR8_MODEL_ENDPOINT` is unset.
* **Classification**: Stop Rule Hit (Missing Environment Constraints).
* **Decision**: System halts immediately without retry.
* **Trace Entry**:
  ```json
  {"action": "engine_halt", "reason": "missing_required_environment_variable", "variable": "LIBR8_MODEL_ENDPOINT"}
  ```

### Scenario 6: Tool Permission Denied
* **Context**: Agent tries to write to a protected system directory outside the `.runs` or workspace folder.
* **Classification**: `tool_permission_denied`
* **Decision**: Stop and escalate (ask for approval). No automatic retries.
* **Trace Entry**:
  ```json
  {"action": "retry_decision", "failure_class": "tool_permission_denied", "decision": "ask_for_approval", "tool_name": "write_file"}
  ```
