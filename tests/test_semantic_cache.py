import numpy as np
import pytest

from src.services.semantic_cache import SemanticCacheService


def test_semantic_cache_logic():
    """
    Tests if the semantic cache correctly identifies similar sentences.
    """
    # Lower threshold to 0.6 for testing paraphrases as all-MiniLM can be strict
    cache = SemanticCacheService(threshold=0.6, cache_path="tmp_test_semantic_cache")
    
    text_a = "I am very happy today"
    response_a = '{"sentiment": "positive"}'
    
    # Store first version
    cache.set(text_a, response_a)
    
    # Test identical - should HIT
    assert cache.get(text_a) == response_a
    
    # Test similar - should HIT (paraphrase)
    text_b = "I am feeling great today"
    assert cache.get(text_b) == response_a
    
    # Test different - should MISS
    text_c = "The weather is cold in London"
    assert cache.get(text_c) is None

    # Cleanup
    cache.cache.clear()

@pytest.mark.asyncio
async def test_cosine_similarity():
    cache = SemanticCacheService()
    v1 = np.array([1, 0, 0])
    v2 = np.array([1, 0, 0])
    v3 = np.array([0, 1, 0])
    
    assert cache._cosine_similarity(v1, v2) == pytest.approx(1.0)
    assert cache._cosine_similarity(v1, v3) == pytest.approx(0.0)
