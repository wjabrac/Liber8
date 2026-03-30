"""Trace Replayer tool for LIBR8 run debugging."""

import json
from pathlib import Path
from src.trace import PerformanceTrace, DecisionPoint

class TraceReplayer:
    """Reads execution artifacts from a run directory and reconstructs the decision trace."""
    
    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.trace_file = run_dir / "trace.jsonl"
        self.event_file = run_dir / "eventlog.jsonl"
        
    def analyze(self, verbosity: str = "summary") -> None:
        if not self.trace_file.exists():
            print(f"Trace file not found at {self.trace_file}")
            return
            
        with open(self.trace_file, "r") as f:
            lines = f.readlines()
            
        if not lines:
            print("Trace file is empty.")
            return
            
        # Parse the latest trace in the file
        raw_data = json.loads(lines[-1])
        from src.contracts.migration import upcast_trace
        trace_data = upcast_trace(raw_data)
        
        print("\n" + "="*50)
        print(f"REPLAY TRACE: {trace_data.get('trace_id')}")
        print(f"Task: {trace_data.get('task')}")
        print(f"Outcome: {trace_data.get('outcome')}")
        print("="*50)
        
        if verbosity == "summary":
            print(f"Total Decision Points: {len(trace_data.get('decision_points', []))}")
            if trace_data.get("failure_class"):
                 print(f"Failure Classification: {trace_data.get('failure_class')}")
            return
            
        print("\n--- Decision Point Timeline ---")
        for idx, dp_raw in enumerate(trace_data.get("decision_points", [])):
            name = dp_raw.get("name", "unknown")
            latency = dp_raw.get("latency_ms", 0.0)
            print(f"[{idx+1}] {name.upper()} ({latency}ms)")
            
            if verbosity in ("debug", "full"):
                choice = dp_raw.get("choice", {})
                print(f"    Decision: {json.dumps(choice)}")
                
                if verbosity == "full":
                    inputs = dp_raw.get("inputs_summary", {})
                    rationale = dp_raw.get("rationale", "")
                    print(f"    Inputs: {json.dumps(inputs)}")
                    print(f"    Rationale: {rationale}")
            print()
            
        if "retrieval_stats" in trace_data and trace_data["retrieval_stats"]:
            print("--- Retrieval Metrics ---")
            print(json.dumps(trace_data["retrieval_stats"], indent=2))
        
        print("\nEnd of Replay.\n")

    def aggregate(self, use_rust: bool = False) -> None:
        if not self.trace_file.exists():
            print(f"Trace file not found at {self.trace_file}")
            return
            
        with open(self.trace_file, "r") as f:
            lines = f.readlines()
            
        traces = [json.loads(line) for line in lines if line.strip()]
        
        print(f"Aggregating {len(traces)} traces...")
        from src.rust_wrappers.aggregator import RustReplayAggregatorWrapper
        aggregator = RustReplayAggregatorWrapper(config_enabled=use_rust)
        result = aggregator.aggregate(traces)
        print("Aggregation Result:")
        print(json.dumps(result, indent=2))
