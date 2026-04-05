"""Command Line Interface for LIBR8 Cognition Engine."""

import argparse
import json
import platform
import sys
import tempfile
import time
from pathlib import Path
from typing import Sequence

from src.cognition.config import EngineConfig
from src.cognition_loop import run_cognition_loop
from src.contracts.migration import upcast_event
from src.contracts.validators import validate_eventrecord
from src.export import export_run_report
from src.ops.retention import RunRetentionPolicy, plan_run_prune
from src.replay.replayer import TraceReplayer
from src.runs.session import list_run_dirs, prune_run_dirs
from src.service.app import Libr8Service
from src.service.config import ServiceConfig
from src.service.http import serve_forever
from src.service.migrations import list_postgres_migrations


def _artifact_dir_from_event(event) -> str:
    return str(event.provenance.get("run_artifact_dir", ""))

def _allowlist_path_exists(path_value: str) -> bool:
    candidate = Path(path_value)
    if candidate.exists():
        return True
    parent = candidate.parent
    if not parent.exists():
        return False

    def _normalize(name: str) -> str:
        return "".join(ch for ch in name.lower() if ch.isalnum()).replace("e", "")

    target = _normalize(candidate.name)
    return any(_normalize(child.name) == target for child in parent.iterdir())


def _cmd_run(args: argparse.Namespace) -> int:
    storage_dir = Path(args.storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)

    print(f"Starting CognitionEngine (backend: {args.backend}) for task: '{args.task}'")
    event = run_cognition_loop(
        task=args.task,
        storage_dir=storage_dir,
        cognition_backend=args.backend,
    )

    print(f"Run completed with outcome: {event.outcome}")
    if event.failure_class:
        print(f"Failure class: {event.failure_class}")
    print(f"Event ID: {event.id}")
    print(f"Run artifacts: {_artifact_dir_from_event(event)}")
    return 0 if event.outcome in {"success", "degraded"} else 1


def _cmd_replay(args: argparse.Namespace) -> int:
    print(f"Replaying trace from: {args.run_path}")
    path = Path(args.run_path)
    if not path.exists():
        print("Run path does not exist.")
        return 1

    replayer = TraceReplayer(path)
    if getattr(args, "aggregate", False):
        replayer.aggregate(use_rust=getattr(args, "use_rust", False))
    else:
        replayer.analyze(verbosity=args.verbosity)
    return 0


def _cmd_export(args: argparse.Namespace) -> int:
    path = Path(args.run_path)
    if not path.exists():
        print("Run path does not exist.")
        return 1

    report_path = export_run_report(path, args.output_path)
    print(f"Report written to: {report_path}")
    return 0


def _cmd_inspect_run(args: argparse.Namespace) -> int:
    path = Path(args.run_path)
    event_file = path / "eventlog.jsonl"
    if not event_file.exists():
        print(f"No eventlog found at {path}")
        return 1

    with open(event_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        if not line.strip():
            continue
        event = upcast_event(json.loads(line))
        print("\n--- RUN INSPECTION ---")
        print(f"Task: {event.get('task')}")
        print(f"Outcome: {event.get('outcome')}")
        print(f"Retries: {event.get('retries')}")
        print(f"Runtime: {event.get('latency')} ms")
        print(f"Cost: ${event.get('cost')}")
        if event.get('failure_class'):
            print(f"Failure Class: {event.get('failure_class')}")
    return 0


def _cmd_validate_run(args: argparse.Namespace) -> int:
    path = Path(args.run_path)
    event_file = path / "eventlog.jsonl"
    if not event_file.exists():
        print(f"No eventlog found at {path}")
        return 1

    with open(event_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    from src.contracts.models import EventRecord, TagSet, QueryPlan

    for i, line in enumerate(lines):
        if not line.strip():
            continue
        event_dict = upcast_event(json.loads(line))
        if "tags" in event_dict:
            event_dict["tags"] = TagSet(**event_dict["tags"])
        if "query_plan" in event_dict:
            event_dict["query_plan"] = QueryPlan(**event_dict["query_plan"])

        try:
            event = EventRecord(**event_dict)
            validate_eventrecord(event)
            print(f"Event {i + 1}: PASS strict validation (version {event.schema_version})")
        except Exception as e:
            print(f"Event {i + 1}: FAIL validation - {str(e)}")
            return 1
    return 0


def _cmd_diff_runs(args: argparse.Namespace) -> int:
    print(f"Diffing runs {args.run1} and {args.run2}")

    def get_event(p):
        path = Path(p) / "eventlog.jsonl"
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    return dict(upcast_event(json.loads(line)))
        return None

    e1 = get_event(args.run1)
    e2 = get_event(args.run2)

    if not e1 or not e2:
        print("Could not load events for both runs.")
        return 1

    print(f"Outcome       : {e1.get('outcome')} -> {e2.get('outcome')}")
    print(f"Tool Calls    : {len(e1.get('tool_calls', []))} -> {len(e2.get('tool_calls', []))}")
    print(f"Agents Scored : {e1.get('actions')} -> {e2.get('actions')}")
    return 0


def _cmd_benchmark(args: argparse.Namespace) -> int:
    print(f"Running diagnostics benchmark against target {args.target}")
    with tempfile.TemporaryDirectory() as tmpdir:
        start = time.monotonic()
        event = run_cognition_loop(
            task=f"benchmark:{args.target}",
            storage_dir=Path(tmpdir),
            cognition_backend="fallback",
        )
        duration_ms = (time.monotonic() - start) * 1000.0

    print(f"Benchmark outcome: {event.outcome}")
    print(f"Benchmark runtime: {duration_ms:.2f} ms")
    print(f"Run artifacts: {_artifact_dir_from_event(event)}")
    return 0 if event.outcome in {"success", "degraded"} else 1


def _cmd_healthcheck(args: argparse.Namespace) -> int:
    config = EngineConfig(cognition_backend=args.backend)
    storage_dir = Path(args.storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    runs_dir = storage_dir / ".runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    # Environment validation
    venv_path = Path(".venv")
    has_venv = venv_path.exists() and venv_path.is_dir()
    
    try:
        import psycopg
        has_psycopg = True
    except ImportError:
        has_psycopg = False

    try:
        from dotenv import load_dotenv
        has_dotenv = True
    except ImportError:
        has_dotenv = False

    checks = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "storage_dir": str(storage_dir.resolve()),
        "runs_dir": str(runs_dir.resolve()),
        "runs_dir_writable": runs_dir.exists() and runs_dir.is_dir(),
        "run_count": len(list_run_dirs(storage_dir)),
        "default_allowlist": config.path_allowlists[0] if config.path_allowlists else "",
        "default_allowlist_exists": bool(config.path_allowlists) and _allowlist_path_exists(config.path_allowlists[0]),
        "tool_policy_mode": config.tool_policy_mode,
        "network_allowed": config.network_allowed,
        "backend": args.backend,
        "tool_protocol": "mcp",
        "execution_isolation_target": config.execution_isolation_backend,
        "observability_spans": "ai.agent.invoke,ai.tool.invoke,ai.llm.invoke",
        "versioning_mode": "composite",
        "venv_exists": has_venv,
        "dependency_psycopg": has_psycopg,
        "dependency_dotenv": has_dotenv,
    }

    print("--- LIBR8 HEALTHCHECK ---")
    for key, value in checks.items():
        print(f"{key}: {value}")

    healthy = bool(checks["runs_dir_writable"] and checks["default_allowlist_exists"] and has_venv)
    print(f"healthcheck_status: {'ok' if healthy else 'fail'}")
    return 0 if healthy else 1


def _service_from_args(args: argparse.Namespace) -> Libr8Service:
    config = ServiceConfig(
        host=getattr(args, "host", "127.0.0.1"),
        port=getattr(args, "port", 8080),
        storage_dir=args.storage_dir,
        cognition_backend=args.backend,
        require_isolation_for_writes=getattr(args, "require_isolation", False),
        execution_isolation_backend=getattr(args, "isolation_backend", "none"),
    )
    return Libr8Service(config)


def _cmd_service_health(args: argparse.Namespace) -> int:
    service = _service_from_args(args)
    print(json.dumps(service.health(), indent=2, sort_keys=True))
    return 0


def _cmd_admin_snapshot(args: argparse.Namespace) -> int:
    service = _service_from_args(args)
    print(json.dumps(service.admin_snapshot(), indent=2, sort_keys=True))
    return 0


def _cmd_list_migrations(args: argparse.Namespace) -> int:
    payload = {"postgres": [item.to_dict() for item in list_postgres_migrations()]}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    service = _service_from_args(args)
    print(f"Serving LIBR8 API on {service.config.host}:{service.config.port}")
    serve_forever(service)
    return 0


def _cmd_prune_runs(args: argparse.Namespace) -> int:
    storage_dir = Path(args.storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    existing = list_run_dirs(storage_dir)
    if args.max_age_days is not None or args.max_total_bytes is not None:
        policy = RunRetentionPolicy(
            max_age_days=args.max_age_days if args.max_age_days is not None else 30,
            max_total_bytes=args.max_total_bytes if args.max_total_bytes is not None else 2_147_483_648,
            keep_minimum=args.keep,
        )
        removable = plan_run_prune(storage_dir, policy)
        print(f"Runs removable: {len(removable)}")
        for item in removable:
            print(f"Would remove: {item.run_dir} ({item.reason})")
        if args.dry_run:
            return 0
        removed = []
        for item in removable:
            import shutil
            shutil.rmtree(item.run_dir, ignore_errors=False)
            removed.append(item.run_dir)
        print(f"Runs removed: {len(removed)}")
        for path in removed:
            print(f"Removed: {path}")
        return 0

    if args.dry_run:
        removable = existing[max(args.keep, 0):]
        print(f"Runs kept: {min(len(existing), max(args.keep, 0))}")
        print(f"Runs removable: {len(removable)}")
        for path in removable:
            print(f"Would remove: {path}")
        return 0

    removed = prune_run_dirs(storage_dir, keep=args.keep)
    print(f"Runs removed: {len(removed)}")
    for path in removed:
        print(f"Removed: {path}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="LIBR8 Cognition Engine Management CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Execute a cognitive task")
    run_parser.add_argument("task", type=str, help="The task for the engine to execute")
    run_parser.add_argument("--storage-dir", default=".storage", help="Storage root for artifacts")
    run_parser.add_argument("--backend", default="fallback", choices=["fallback", "dspy+zep"], help="Cognition backend to use")
    run_parser.set_defaults(func=_cmd_run)

    replay_parser = subparsers.add_parser("replay", help="Replay a trace from a specific run ID")
    replay_parser.add_argument("run_path", type=str, help="Path to the specific run directory")
    replay_parser.add_argument("--verbosity", default="summary", choices=["summary", "debug", "full"], help="Trace output verbosity")
    replay_parser.add_argument("--aggregate", action="store_true", help="Aggregate all traces in the file instead of replaying")
    replay_parser.add_argument("--use-rust", action="store_true", help="Use Rust accelerators if available")
    replay_parser.set_defaults(func=_cmd_replay)

    export_parser = subparsers.add_parser("export", help="Export a markdown report for a specific run")
    export_parser.add_argument("run_path", type=str, help="Path to the specific run directory")
    export_parser.add_argument("--output-path", default=None, help="Optional path for the generated report")
    export_parser.set_defaults(func=_cmd_export)

    inspect_parser = subparsers.add_parser("inspect-run", help="Inspect high layer summary of a specific run")
    inspect_parser.add_argument("run_path", type=str)
    inspect_parser.set_defaults(func=_cmd_inspect_run)

    validate_parser = subparsers.add_parser("validate-run", help="Strictly validate a run log against contracts")
    validate_parser.add_argument("run_path", type=str)
    validate_parser.set_defaults(func=_cmd_validate_run)

    diff_parser = subparsers.add_parser("diff-runs", help="Diff the outcomes and selections between two runs")
    diff_parser.add_argument("run1", type=str)
    diff_parser.add_argument("run2", type=str)
    diff_parser.set_defaults(func=_cmd_diff_runs)

    bench_parser = subparsers.add_parser("benchmark", help="Run a diagnostics benchmark")
    bench_parser.add_argument("--target", type=str, default="baseline")
    bench_parser.set_defaults(func=_cmd_benchmark)

    health_parser = subparsers.add_parser("healthcheck", help="Report local runtime readiness for LIBR8")
    health_parser.add_argument("--storage-dir", default=".storage", help="Storage root for artifacts")
    health_parser.add_argument("--backend", default="fallback", choices=["fallback", "dspy+zep"], help="Backend to validate")
    health_parser.set_defaults(func=_cmd_healthcheck)

    service_health_parser = subparsers.add_parser("service-health", help="Report service/API readiness")
    service_health_parser.add_argument("--host", default="127.0.0.1")
    service_health_parser.add_argument("--port", type=int, default=8080)
    service_health_parser.add_argument("--storage-dir", default=".storage")
    service_health_parser.add_argument("--backend", default="fallback", choices=["fallback", "dspy+zep"])
    service_health_parser.add_argument("--require-isolation", action="store_true")
    service_health_parser.add_argument("--isolation-backend", default="none")
    service_health_parser.set_defaults(func=_cmd_service_health)

    admin_parser = subparsers.add_parser("admin-snapshot", help="Print a redacted service admin snapshot")
    admin_parser.add_argument("--host", default="127.0.0.1")
    admin_parser.add_argument("--port", type=int, default=8080)
    admin_parser.add_argument("--storage-dir", default=".storage")
    admin_parser.add_argument("--backend", default="fallback", choices=["fallback", "dspy+zep"])
    admin_parser.add_argument("--require-isolation", action="store_true")
    admin_parser.add_argument("--isolation-backend", default="none")
    admin_parser.set_defaults(func=_cmd_admin_snapshot)

    migrations_parser = subparsers.add_parser("list-migrations", help="List operational PostgreSQL migration files")
    migrations_parser.set_defaults(func=_cmd_list_migrations)

    serve_parser = subparsers.add_parser("serve", help="Run the LIBR8 service/API")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8080)
    serve_parser.add_argument("--storage-dir", default=".storage")
    serve_parser.add_argument("--backend", default="fallback", choices=["fallback", "dspy+zep"])
    serve_parser.add_argument("--require-isolation", action="store_true")
    serve_parser.add_argument("--isolation-backend", default="none")
    serve_parser.set_defaults(func=_cmd_serve)

    prune_parser = subparsers.add_parser("prune-runs", help="Prune old run artifacts from storage")
    prune_parser.add_argument("--storage-dir", default=".storage", help="Storage root for artifacts")
    prune_parser.add_argument("--keep", type=int, default=20, help="Number of most recent runs to keep")
    prune_parser.add_argument("--dry-run", action="store_true", help="Show which runs would be removed without deleting them")
    prune_parser.add_argument("--max-age-days", type=int, default=None, help="Optional age-based retention window")
    prune_parser.add_argument("--max-total-bytes", type=int, default=None, help="Optional total artifact budget")
    prune_parser.set_defaults(func=_cmd_prune_runs)

    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
