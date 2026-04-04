# CX-017 Rust candidates boundary (design-only)

Objective
Define the boundary where Rust can later replace hot-path components without rewriting the engine.

Scope
- Add docs/rust_boundary.md describing:
  - candidate modules (retrieval ranking, index build, jsonl parsing, trace aggregation)
  - required surface (inputs/outputs)
  - fallback behavior if Rust module absent
- Do not introduce Rust build tooling yet.

Acceptance criteria
- Document exists and references concrete Python module entry points intended to be swapped later.
