"""Python wrapper for the Rust retrieval_ranker boundary substitution."""

import logging
from typing import List
from src.contracts import MemoryBlock

try:
    import retrieval_ranker
    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False


class RustRankerWrapper:
    def __init__(self, config_enabled: bool = False):
        self.enabled = config_enabled and RUST_AVAILABLE
        if config_enabled and not RUST_AVAILABLE:
            logging.warning("Rust retrieval_ranker requested but not installed. Falling back to Python.")

    def rank(self, blocks: List[MemoryBlock], query: str) -> List[MemoryBlock]:
        if not self.enabled:
            return blocks
            
        contents = [b.content for b in blocks]
        try:
            ranked_contents = retrieval_ranker.rank_blocks(contents, query)
            ranked_blocks = []
            for rc in ranked_contents:
                for b in blocks:
                    if b.content == rc:
                        ranked_blocks.append(b)
                        break
            return ranked_blocks
        except Exception as e:
            logging.error(f"Rust rank_blocks failed: {e}. Falling back to Python.")
            return blocks
