"""Markdown run-report export for LIBR8 artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from src.contracts.migration import upcast_event, upcast_trace


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _load_jsonl_last(path: Path, upcaster) -> Dict[str, Any]:
    if not path.exists():
        return {}
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return {}
    return upcaster(json.loads(lines[-1]))


def _bullet_list(values: Iterable[str]) -> List[str]:
    items = [value for value in values if value]
    return items if items else ["none"]


def export_run_report(run_dir: Path | str, output_path: Path | str | None = None) -> Path:
    run_path = Path(run_dir)
    if not run_path.exists():
        raise FileNotFoundError(f"Run path does not exist: {run_path}")

    report_path = Path(output_path) if output_path is not None else run_path / "report.md"

    meta = _load_json(run_path / "meta.json")
    manifest = _load_json(run_path / "run_manifest.json")
    writeback = _load_json(run_path / "writeback.json")
    event = _load_jsonl_last(run_path / "eventlog.jsonl", upcast_event)
    trace = _load_jsonl_last(run_path / "trace.jsonl", upcast_trace)

    tags = ((event.get("tags") or {}).get("tags") or {})
    routing = next((dp for dp in trace.get("decision_points", []) if dp.get("name") == "routing"), {})
    retrieval_stats = trace.get("retrieval_stats") or {}
    failures = [trace.get("failure_class"), event.get("failure_class")]
    writeback_payload = writeback or event.get("provenance", {}).get("writeback", {}) or {}
    persisted_ids = event.get("provenance", {}).get("persisted_memory_ids", [])
    artifact_paths = (manifest.get("artifacts") or {}) if manifest else {}

    lines = [
        "# LIBR8 Run Report",
        "",
        "## Summary",
        f"- Run ID: {meta.get('run_id', run_path.name)}",
        f"- Task: {event.get('task') or trace.get('task') or 'unknown'}",
        f"- Outcome: {event.get('outcome') or trace.get('outcome') or manifest.get('status') or 'unknown'}",
        f"- Evaluation outcome: {writeback_payload.get('evaluation_outcome') or trace.get('evaluation_outcome') or 'unknown'}",
        f"- Backend: {meta.get('cognition_backend') or manifest.get('backend') or event.get('provenance', {}).get('backend') or 'unknown'}",
        f"- Created at: {meta.get('created_at', 'unknown')}",
        "",
        "## Tags",
    ]
    lines.extend(f"- {key}: {value}" for key, value in sorted(tags.items()))
    if not tags:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Routing Decisions",
            f"- Agents: {', '.join(_bullet_list(routing.get('choice', {}).get('agents', [])))}",
            f"- Reason: {routing.get('choice', {}).get('reason', 'none')}",
            f"- Confidence: {routing.get('choice', {}).get('confidence', 'unknown')}",
            "",
            "## Retrieval Stats",
            f"- Requested: {retrieval_stats.get('k_requested', 0)}",
            f"- Returned: {retrieval_stats.get('k_returned', 0)}",
            f"- Diversity hits: {retrieval_stats.get('diversity_hits', 0)}",
            f"- Expansion applied: {retrieval_stats.get('expansion_applied', False)}",
            "",
            "## Failures",
        ]
    )
    failure_items = [value for value in failures if value]
    if failure_items:
        lines.extend(f"- {value}" for value in failure_items)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Writeback Summary",
            f"- Distilled facts: {len(writeback_payload.get('distilled_facts', []))}",
            f"- Procedural snippet: {'present' if writeback_payload.get('procedural_snippet') else 'none'}",
            f"- Persisted memory ids: {', '.join(_bullet_list(persisted_ids))}",
            "",
            "## Artifact Paths",
        ]
    )
    if artifact_paths:
        lines.extend(f"- {name}: {path}" for name, path in sorted(artifact_paths.items()))
    else:
        lines.append("- none")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path
