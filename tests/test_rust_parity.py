import unittest
import time
from src.rust_wrappers.ranker import RustRankerWrapper, RUST_AVAILABLE
from src.contracts.models import TagSet, MemoryBlock

class TestRustParity(unittest.TestCase):
    @unittest.skipIf(not RUST_AVAILABLE, "Rust extension not built")
    def test_ranker_parity(self):
        blocks = []
        for i in range(10000):
            content = f"document {i} about artificial intelligence and space" if i % 2 == 0 else f"document {i} completely irrelevant"
            blocks.append(MemoryBlock(content=content, tags=TagSet("1.0", {}), provenance={}, lane="episodic", confidence=1.0))
            
        ranker = RustRankerWrapper(config_enabled=True)
        
        start = time.time()
        results = ranker.rank(blocks, "artificial intelligence space")
        dur = time.time() - start
        
        self.assertEqual(len(results), 10000)
        self.assertTrue("artificial intelligence" in results[0].content)
        print(f"Rust scored 10k items in {dur*1000:.2f}ms")

if __name__ == "__main__":
    unittest.main()
