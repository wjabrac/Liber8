# CX-017: Rust Candidates Boundary

This document outlines the architectural boundary where Python components within the Liber8 Cognition Engine will be substituted with Rust implementations to reduce latency and overhead, primarily targeting loops identified by the Trimming Playbook (`AG-011`).

## 1. Candidate Modules

Currently, two hot-paths have been identified for Phase 4 architectural substitution.

### A. Retrieval Ranking Core
**Current Location**: `src/retrieval/scoring.py` (`score_block`, `rank_and_explain`)
**Why**: Tag-first mathematical overlapping against thousands of memory blocks is computationally expensive in pure Python.
**Input Boundary (FFI)**:
- `query_tags`: JSON serialized representation of the query `TagSet`.
- `candidate_blocks`: JSON records containing `id`, `tags`, `confidence`, `created_at`, `lane`, `provenance`.
**Output Boundary (FFI)**:
- Ranked list of block IDs and stringified explanation payload objects.
**Fallback**: If the Python `ctypes` or PyO3 wrapper fails to load the compiled Rust `.so`, the system will gracefully fall back to the existing pure Python loops in `scoring.py`.

### B. Trace Log Aggregation
**Current Location**: `src/runs/replay.py` (`ReplayEngine.load_run`)
**Why**: As event logs grow, iterating over thousands of JSON lines in Python becomes an IO bottleneck.
**Input Boundary (FFI)**:
- `run_dir_path`: Absolute path to a `.runs/{run_id}` directory containing `trace.jsonl` and `eventlog.jsonl`.
**Output Boundary (FFI)**:
- Aggregated JSON dictionary (Python object) with unified `meta`, `traces`, and `events` arrays.
**Fallback**: The `json.loads` procedural loop maintained in `replay.py`.

## 2. Foreign Function Interface (FFI) Approach
For these boundaries, **PyO3/Maturin** will be preferred over native `ctypes` due to its idiomatic conversion of Rust memory structures into native Python dictionaries and lists. It provides the most zero-cost bridging available.
