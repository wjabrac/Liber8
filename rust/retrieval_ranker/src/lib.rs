use pyo3::prelude::*;
use std::collections::HashSet;

#[pyfunction]
fn rank_blocks(blocks: Vec<String>, query: String) -> PyResult<Vec<String>> {
    let query_terms: HashSet<&str> = query.split_whitespace().collect();
    
    let mut scored_blocks: Vec<(f64, String)> = blocks.into_iter().map(|block| {
        let block_terms: HashSet<&str> = block.split_whitespace().collect();
        let overlap = query_terms.intersection(&block_terms).count() as f64;
        let score = if query_terms.is_empty() { 0.0 } else { overlap / query_terms.len() as f64 };
        (score, block)
    }).collect();
    
    // Sort descending by score
    scored_blocks.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));
    
    let ranked = scored_blocks.into_iter().map(|(_, b)| b).collect();
    Ok(ranked)
}

#[pymodule]
fn retrieval_ranker(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(rank_blocks, m)?)?;
    Ok(())
}
