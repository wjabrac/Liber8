# Execution Gateway Policy v0 (spec anchor)

Goal: safe, auditable tool execution with an allowlist and per-tool policies.

Requirements:
- ToolRegistry with explicit enablement
- ToolPolicy: read_only vs write, network_allowed flag, path allowlists
- Every tool call logs: inputs summary, outputs summary, duration, errors, and policy decision
- Default tooling should be non-destructive; destructive tools require explicit user approval in the client environment

Acceptance criteria:
- ExecutionGateway rejects unknown tools by default.
- Tool calls are recorded in EventRecord.tool_calls and PerformanceTrace.
