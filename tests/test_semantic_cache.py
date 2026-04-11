import numpy as np
import pytest
from unittest.mock import MagicMock
from src.services.semantic_cache import SemanticCacheService, SimpleVectorStore, L1LRUCache


def test_semantic_cache_tiered_logic():
    """
    Tests if L1 and L2 cache work together.
    """
    cache = SemanticCacheService(cache_path="tmp_test_semantic_tiered")
    cache.clear()
    
    # Using a medium query to trigger 0.92 threshold
    text = "What is the main advantage of using a semantic cache in a production LLM application?"
    response = '{"content": "Reduced latency and cost."}'
    
    # Initial set - should populate both L1 and L2
    cache.set(text, response)
    
    # 1. Test L1 Hit (Exact match)
    assert cache.get(text) == response
    
    # 2. Test L2 Semantic Hit (Very close paraphrase)
    # This should have similarity > 0.92
    paraphrase = "What's the main advantage of using a semantic cache in a production LLM application?"
    
    assert cache.get(paraphrase) == response
    # Verify it was promoted to L1
    assert cache.l1_cache.get(paraphrase) == response

    cache.clear()

def test_dynamic_thresholding():
    """
    Verifies that threshold changes based on text length.
    """
    cache = SemanticCacheService()
    
    # Short query (< 10 words) -> 0.95
    short_query = "What is AI?"
    assert cache._get_dynamic_threshold(short_query) == 0.95
    
    # Medium query -> 0.92
    medium_query = "Explain the benefits of using a semantic cache in a production LLM application."
    assert cache._get_dynamic_threshold(medium_query) == 0.92
    
    # Long query (> 50 words) -> 0.88
    long_query = " ".join(["word"] * 60)
    assert cache._get_dynamic_threshold(long_query) == 0.88

def test_l1_lru_behavior():
    """
    Tests LRU evacuation in L1 cache.
    """
    l1 = L1LRUCache(capacity=2)
    l1.set("a", "1")
    l1.set("b", "2")
    l1.get("a") # Move 'a' to end
    l1.set("c", "3") # Should evacuate 'b'
    
    assert l1.get("a") == "1"
    assert l1.get("c") == "3"
    assert l1.get("b") is None

def test_vector_store_search():
    """
    Tests the basic vector store search logic.
    """
    vs = SimpleVectorStore()
    v1 = np.array([1.0, 0.0, 0.0])
    v2 = np.array([0.9, 0.1, 0.0])
    v3 = np.array([0.0, 1.0, 0.0])
    
    vs.add(v1, {"text": "v1"})
    vs.add(v3, {"text": "v3"})
    
    # Search for something close to v1
    results = vs.search(v2, top_k=1)
    assert len(results) == 1
    similarity, metadata = results[0]
    assert metadata["text"] == "v1"
    assert similarity > 0.9

@pytest.mark.asyncio
async def test_cosine_similarity_edge_cases():
    vs = SimpleVectorStore()
    v1 = np.array([1, 0, 0])
    v_zero = np.array([0, 0, 0])
    
    # Should handle zero vectors without crashing
    assert vs._cosine_similarity(v1, v_zero) == 0.0
