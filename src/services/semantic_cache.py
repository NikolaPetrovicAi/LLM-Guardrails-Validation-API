import logging
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Any, Optional

import numpy as np
from diskcache import Cache
from sentence_transformers import SentenceTransformer

from src.core.config import settings

logger = logging.getLogger(__name__)

# --- Interfaces (Strategy Pattern) ---

class EmbeddingProvider(ABC):
    @abstractmethod
    def encode(self, text: str) -> np.ndarray:
        """Generates embedding for the given text."""
        pass

class VectorStore(ABC):
    @abstractmethod
    def add(self, vector: np.ndarray, metadata: dict) -> None:
        """Adds a vector and its metadata to the store."""
        pass

    @abstractmethod
    def search(self, query_vector: np.ndarray, top_k: int = 1) -> list[tuple[float, dict]]:
        """Searches for the most similar vectors."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clears the store."""
        pass

# --- Implementations ---

class SentenceTransformerProvider(EmbeddingProvider):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def encode(self, text: str) -> np.ndarray:
        return self.model.encode(text)

class SimpleVectorStore(VectorStore):
    """NumPy-based vector store for fast O(n) search (can be swapped for FAISS)."""
    def __init__(self):
        self.vectors: list[np.ndarray] = []
        self.metadata: list[dict] = []

    def add(self, vector: np.ndarray, metadata: dict) -> None:
        self.vectors.append(vector)
        self.metadata.append(metadata)

    def search(self, query_vector: np.ndarray, top_k: int = 1) -> list[tuple[float, dict]]:
        if not self.vectors:
            return []
        
        similarities = []
        for i, vec in enumerate(self.vectors):
            sim = self._cosine_similarity(query_vector, vec)
            similarities.append((sim, self.metadata[i]))
        
        # Sort by similarity descending
        similarities.sort(key=lambda x: x[0], reverse=True)
        return similarities[:top_k]

    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        return dot_product / (norm_v1 * norm_v2) if norm_v1 > 0 and norm_v2 > 0 else 0.0
    
    def clear(self) -> None:
        self.vectors = []
        self.metadata = []

class L1LRUCache:
    """Ultra-fast In-Memory LRU Cache."""
    def __init__(self, capacity: int = 100):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key: str) -> Optional[str]:
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]

    def set(self, key: str, value: str) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
    
    def clear(self) -> None:
        self.cache.clear()

# --- Main Service ---

class SemanticCacheService:
    """
    Tiered Semantic Cache with Dynamic Thresholding and Performance Analytics.
    """

    def __init__(
        self,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[VectorStore] = None,
        cache_path: str = f"{settings.CACHE_PATH}_semantic_v2",
        l1_capacity: int = 200,
        default_llm_latency_ms: float = 2500.0,
        default_llm_cost_usd: float = 0.01
    ):
        self.embedding_provider = embedding_provider or SentenceTransformerProvider()
        self.vector_store = vector_store or SimpleVectorStore()
        self.l1_cache = L1LRUCache(capacity=l1_capacity)
        self.l2_cache = Cache(cache_path)
        
        self.default_llm_latency_ms = default_llm_latency_ms
        self.default_llm_cost_usd = default_llm_cost_usd
        
        self._load_index_from_l2()

    def _load_index_from_l2(self):
        """Rebuilds the vector index from persistent storage."""
        count = 0
        for key in self.l2_cache:
            if isinstance(key, str) and key.startswith("vec:"):
                original_text = key[4:]
                vector = self.l2_cache.get(key)
                if vector is not None:
                    self.vector_store.add(vector, {"original_text": original_text})
                    count += 1
        logger.info(f"Tiered Semantic Cache loaded with {count} entries into Vector Store.")

    def _get_dynamic_threshold(self, text: str) -> float:
        """
        Determines similarity threshold based on query complexity/intent.
        Short (Informativni) -> High threshold (0.95)
        Long (Kreativni) -> Low threshold (0.88)
        """
        words = text.split()
        word_count = len(words)
        
        if word_count < 10:
            return 0.95
        elif word_count > 50:
            return 0.88
        return 0.92

    def get(self, text: str) -> Optional[str]:
        """
        Attempts to retrieve a response from L1 or L2 cache.
        """
        start_time = time.perf_counter()
        
        # 1. Check L1 (In-Memory LRU) - Exact or near-exact matches if recently seen
        l1_hit = self.l1_cache.get(text)
        if l1_hit:
            self._log_cache_metric("L1_HIT", text, 1.0, start_time)
            return l1_hit

        # 2. Check L2 (Vector Store) - Semantic search
        try:
            query_vector = self.embedding_provider.encode(text)
            results = self.vector_store.search(query_vector, top_k=1)
            
            if not results:
                return None

            similarity, metadata = results[0]
            threshold = self._get_dynamic_threshold(text)

            if similarity >= threshold:
                original_text = metadata["original_text"]
                cached_response = self.l2_cache.get(f"resp:{original_text}")
                
                if cached_response:
                    # Upgrade to L1 for future fast access
                    self.l1_cache.set(text, cached_response)
                    self._log_cache_metric("L2_SEMANTIC_HIT", text, similarity, start_time)
                    return cached_response
        except Exception as e:
            logger.error(f"Semantic Cache lookup failed: {e}")
        
        return None

    def set(self, text: str, response_json: str, expire: int = settings.CACHE_EXPIRE):
        """
        Stores response in both L1 and L2 caches.
        """
        try:
            vector = self.embedding_provider.encode(text)
            
            # Persistent L2
            self.l2_cache.set(f"vec:{text}", vector, expire=expire)
            self.l2_cache.set(f"resp:{text}", response_json, expire=expire)
            
            # In-Memory stores
            self.vector_store.add(vector, {"original_text": text})
            self.l1_cache.set(text, response_json)
            
            logger.debug(f"Stored in Tiered Cache: {text[:50]}...")
        except Exception as e:
            logger.error(f"Semantic Cache storage failed: {e}")

    def _log_cache_metric(self, status: str, text: str, similarity: float, start_time: float):
        """Logs cache performance analytics."""
        lookup_latency = (time.perf_counter() - start_time) * 1000
        latency_savings = self.default_llm_latency_ms - lookup_latency
        
        logger.info(
            f"Cache {status} (Sim: {similarity:.4f}, Savings: {latency_savings:.2f}ms)",
            extra={
                "event": "cache_analytics",
                "cache_status": status,
                "similarity": similarity,
                "latency_savings_ms": round(latency_savings, 2),
                "cost_savings_usd": self.default_llm_cost_usd,
                "text_snippet": text[:50]
            }
        )

    def clear(self):
        """Clears all cache tiers."""
        self.l1_cache.clear()
        self.l2_cache.clear()
        self.vector_store.clear()
