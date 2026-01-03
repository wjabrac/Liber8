# CX-006 — Minimal CLI and run directory conventions

Goal
Provide a minimal CLI that runs the router loop, stores outputs under a run directory, and prints stable, parseable output for tooling.

Inputs
- src/orchestration/router.py (from CX-004)
- src/eventlog.py
- src/memory_adapter.py

Deliverables (code)
- src/cli.py
- tests/test_cli_smoke.py
- Update README or add docs/cli.md (optional but preferred)

CLI requirements
1) Commands
- run: run a task
  - args: task string
  - flags: --storage <path>, --fake, --model-endpoint <url>, --print-json
- show-runs:
  - list latest N runs by reading eventlog.jsonl from a directory

2) Run directory layout
When --storage is not provided, default to:
- .runs/<utc_timestamp>/
  - eventlog.jsonl
  - memory.jsonl
  - meta.json (optional)

3) Output format
- Default: print event id, outcome, and storage path on one line
- If --print-json: print full EventRecord JSON to stdout

Testing requirements
- CLI smoke test runs with --fake and ensures it creates expected files.

Acceptance criteria
- Works in Codex environment with no additional configuration when --fake is used.
- No network usage in tests.
- All tests pass.
