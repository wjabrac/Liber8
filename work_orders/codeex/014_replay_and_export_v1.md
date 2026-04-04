# CX-014 Replay + export v1

Objective
Enable deterministic replay for fake mode and produce a readable run report for debugging and optimization.

Scope
- Implement src/replay.py to rerun from .runs/<run_id>/meta.json
- Implement src/export.py to export a markdown report summarizing:
  - tags, routing decisions, retrieval stats, failures, writeback summary
- Keep artifacts referenced by path; do not duplicate large payloads

Acceptance criteria
- libr8 replay <run_dir> works in fake mode deterministically
- libr8 export <run_dir> writes eport.md

Tests
- Smoke test ensures report.md is produced and contains key sections.
