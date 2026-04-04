# CX-012 ExecutionGateway v1 (allowlist + audited tool calls)

Objective
Implement an ExecutionGateway and ToolRegistry per spec/execution_gateway_policy_v0.md. Default tools are non-destructive.

Scope
- Add src/execution/gateway.py, src/execution/tools.py, src/execution/policy.py
- Provide NullTool, FileReadTool (read-only within allowlisted paths)
- Capture all tool calls into EventRecord.tool_calls and PerformanceTrace decision_points

Acceptance criteria
- Unknown tools are rejected by default
- Tool calls include inputs/outputs summaries and durations
- No Docker required

Tests
- Unit test tool allowlist and policy enforcement.
