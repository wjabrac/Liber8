# CX-008 Run sessions + meta.json

Objective
Create a consistent per-run directory and metadata file used by replay/export and by future optimization.

Scope
- Add src/runs/session.py with create_run_dir(base_dir)->Path and write_meta(run_dir, meta)
- meta.json includes: run_id, created_at, git_commit, engine_version, config_hash, cognition_backend

Acceptance criteria
- CLI and CognitionEngine always create and populate meta.json
- git commit is captured when available (empty string acceptable if not)

Tests
- Unit test meta.json schema presence and required keys.
