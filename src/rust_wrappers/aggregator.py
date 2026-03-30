"""Python wrapper for the Rust replay_aggregator boundary substitution."""

import logging
import json

try:
    import replay_aggregator
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False


class RustReplayAggregatorWrapper:
    def __init__(self, config_enabled: bool = False):
        self.enabled = config_enabled and RUST_AVAILABLE
        if config_enabled and not RUST_AVAILABLE:
            logging.warning("Rust replay_aggregator requested but not installed. Falling back to Python.")

    def aggregate(self, traces: list[dict]) -> dict:
        if not self.enabled:
            return {"status": "fallback", "count": len(traces)}
            
        try:
            raw_json = json.dumps(traces)
            result = replay_aggregator.aggregate_traces(raw_json)
            return json.loads(result)
        except Exception as e:
            logging.error(f"Rust aggregate_traces failed: {e}. Falling back to Python.")
            return {"status": "fallback_on_error", "count": len(traces)}
