import unittest
import time
from src.rust_wrappers.ranker import RustRankerWrapper, PythonRanker, RUST_AVAILABLE
from src.contracts.models import TagSet, MemoryBlock

class TestRustParity(unittest.TestCase):
    def setUp(self):
        self.blocks = []
        for i in range(100):
            content = f"document {i} about artificial intelligence and space" if i % 2 == 0 else f"document {i} completely irrelevant"
            self.blocks.append(MemoryBlock(
                content=content, 
                tags=TagSet("1.0", {}), 
                provenance={}, 
                lane="episodic", 
                confidence=1.0,
                updated_at="2026-04-04T12:00:00Z"
            ))

    def test_python_ranker_logic(self):
        ranker = PythonRanker()
        results = ranker.rank(self.blocks, "artificial intelligence space")
        self.assertEqual(len(results), 100)
        # First item should be one of the AI documents
        self.assertIn("artificial intelligence", results[0].content.lower())

    @unittest.skipIf(not RUST_AVAILABLE, "Rust extension not built")
    def test_ranker_parity(self):
        # Test Rust path
        rust_ranker = RustRankerWrapper(config_enabled=True)
        py_ranker = PythonRanker()
        
        query = "artificial intelligence space"
        
        rust_results = rust_ranker.rank(self.blocks, query)
        py_results = py_ranker.rank(self.blocks, query)
        
        self.assertEqual(len(rust_results), len(py_results))
        # Top results should match in term-match count
        self.assertIn("artificial intelligence", rust_results[0].content.lower())
        
        # Performance check for 1000 items
        large_blocks = self.blocks * 10
        start = time.time()
        rust_ranker.rank(large_blocks, query)
        rust_dur = time.time() - start
        
        start = time.time()
        py_ranker.rank(large_blocks, query)
        py_dur = time.time() - start
        
        print(f"Rust scored 1k items in {rust_dur*1000:.2f}ms")
        print(f"Python scored 1k items in {py_dur*1000:.2f}ms")

if __name__ == "__main__":
    unittest.main()
