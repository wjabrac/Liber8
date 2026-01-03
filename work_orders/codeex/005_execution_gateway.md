# CX-005 — Execution gateway with approval gating (Docker-free)

Goal
Implement a local execution gateway that runs shell commands safely with a strict approval gate for any destructive operation.

Inputs
- Existing approval-token rule: destructive actions require explicit token string "APPROVE: <exact command block>"
- src/contracts.py (EventRecord provenance should record executions)
- Existing tests and structure

Deliverables (code)
- src/execution/gateway.py
- src/execution/classifier.py
- tests/test_exec_classifier.py
- tests/test_exec_gateway.py

Command classification requirements
Classify a command into one of:
- read_only
- write_non_destructive
- destructive
- network
- unknown

Minimum rules (must be implemented)
- destructive includes: rm, del, rmdir, Remove-Item without -WhatIf, format, diskpart, shutdown, reboot, Stop-Service, uninstall, overwrite redirects like ">" to existing files (unless writing to new temp paths), git reset --hard, git clean -fdx
- read_only includes: ls, dir, cat, type, git status, git diff, python -m unittest (read-only execution)
- network includes: curl, wget, Invoke-WebRequest, pip install, npm install
- unknown defaults to destructive unless explicitly allowed (fail closed)

Gateway behavior
- Execute only read_only and write_non_destructive without approval token.
- Require approval token for destructive and for network by default (network should be blocked unless token provided).
- Capture stdout, stderr, exit code, duration.
- Return a structured result dict and ensure it is JSON-serializable.

Testing requirements
- Tests must not execute destructive commands.
- Tests must verify that destructive commands are refused without approval token.
- Tests must verify allowlisted read_only commands run (use harmless commands like python -c "print(1)").

Acceptance criteria
- All tests pass.
- Gateway fails closed by default.
- Clear, deterministic refusal messages are returned for blocked commands.

Do-not-do
- No Open Interpreter dependency.
- No Docker sandbox.
