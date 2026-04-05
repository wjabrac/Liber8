"""Python wrapper for the Rust retrieval_ranker boundary substitution."""

import logging
from typing import List
from src.contracts import MemoryBlock

try:
    import retrieval_ranker
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False


class PythonRanker:
    """Pure-Python fallback ranker using basic term matching."""
    def rank(self, blocks: List[MemoryBlock], query: str) -> List[MemoryBlock]:
        query_terms = set(query.lower().split())
        if not query_terms:
            return blocks
            
        def score(content: str) -> int:
            content_lower = content.lower()
            return sum(1 for term in query_terms if term in content_lower)
            
        # Sort by term match count, descending
        return sorted(blocks, key=lambda b: score(b.content), reverse=True)


class RustRankerWrapper:
    def __init__(self, config_enabled: bool = False):
        self.rust_enabled = config_enabled and RUST_AVAILABLE
        self.python_fallback = PythonRanker()
        if config_enabled and not RUST_AVAILABLE:
            logging.warning("Rust retrieval_ranker requested but not installed. Falling back to Python.")

    def rank(self, blocks: List[MemoryBlock], query: str) -> List[MemoryBlock]:
        if not self.rust_enabled:
            return self.python_fallback.rank(blocks, query)
            
        contents = [b.content for b in blocks]
        try:
            ranked_contents = retrieval_ranker.rank_blocks(contents, query)
            # Reconstruct MemoryBlock list from ranked contents
            # (Note: this simple implementation assumes unique contents for reconstruction)
            content_to_block = {b.content: b for b in blocks}
            ranked_blocks = []
            for rc in ranked_contents:
                if rc in content_to_block:
                    ranked_blocks.append(content_to_block[rc])
            
            # Add back any blocks that might have been filtered or missed
            missed = [b for b in blocks if b.content not in ranked_contents]
            return ranked_blocks + missed
        except Exception as e:
            logging.error(f"Rust rank_blocks failed: {e}. Falling back to Python.")
            return self.python_fallback.rank(blocks, query)
