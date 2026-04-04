use pyo3::prelude::*;
use serde_json::{Value, json};

#[pyfunction]
fn aggregate_traces(traces_json: String) -> PyResult<String> {
    let traces: Vec<Value> = serde_json::from_str(&traces_json).unwrap_or(vec![]);
    
    let total_traces = traces.len();
    let mut success_count = 0;
    let mut total_latency = 0.0;
    
    for trace in &traces {
        if trace["outcome"] == "success" {
            success_count += 1;
        }
        if let Some(lat) = trace.get("latency").and_then(|l| l.as_f64()) {
            total_latency += lat;
        }
    }
    
    let avg_latency = if total_traces > 0 { total_latency / total_traces as f64 } else { 0.0 };
    
    let result = json!({
        "status": "rust_aggregated",
        "total": total_traces,
        "success": success_count,
        "avg_latency": avg_latency
    });
    
    Ok(result.to_string())
}

#[pymodule]
fn replay_aggregator(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(aggregate_traces, m)?)?;
    Ok(())
}
