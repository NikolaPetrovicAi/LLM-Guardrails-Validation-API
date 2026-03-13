import logging

import numpy as np
from diskcache import Cache
from sentence_transformers import SentenceTransformer

from src.core.config import settings

logger = logging.getLogger(__name__)

class SemanticCacheService:
    """
    Advanced semantic cache using Sentence-Transformers for similarity search.
    Reduces LLM calls by finding semantically similar queries.
    """

    def __init__(
        self, 
        model_name: str = "all-MiniLM-L6-v2", 
        threshold: float = 0.92,
        cache_path: str = f"{settings.CACHE_PATH}_semantic"
    ) -> None:
        """
        Initializes the semantic cache with a local embedding model.
        """
        self.model = SentenceTransformer(model_name)
        self.threshold = threshold
        self.cache = Cache(cache_path)
        # In-memory index for fast search (in production use a real Vector DB like Qdrant/Chroma)
        self.index: list[tuple[np.ndarray, str]] = [] 
        self._load_index()

    def _load_index(self):
        """Load keys from diskcache to rebuild the search index."""
        for key in self.cache:
            if key.startswith("vec:"):
                original_text = key[4:]
                vector = self.cache.get(key)
                self.index.append((vector, original_text))
        logger.info(f"Semantic Cache loaded with {len(self.index)} entries.")

    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Computes cosine similarity between two vectors."""
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        return dot_product / (norm_v1 * norm_v2) if norm_v1 > 0 and norm_v2 > 0 else 0.0

    def get(self, text: str) -> str | None:
        """
        Attempts to find a semantically similar entry in the cache.
        """
        query_vector = self.model.encode(text)
        
        best_similarity = -1.0
        best_match_text = None

        for vector, stored_text in self.index:
            sim = self._cosine_similarity(query_vector, vector)
            if sim > best_similarity:
                best_similarity = sim
                best_match_text = stored_text

        if best_similarity >= self.threshold:
            logger.info(
                f"Semantic Cache HIT (Sim: {best_similarity:.4f})",
                extra={"cache_status": "SEMANTIC_HIT", "similarity": best_similarity}
            )
            # Retrieve the response from cache using the original matched text as key
            return self.cache.get(f"resp:{best_match_text}")
        
        return None

    def set(self, text: str, response_json: str, expire: int = settings.CACHE_EXPIRE):
        """
        Stores a response in the semantic cache.
        """
        vector = self.model.encode(text)
        self.cache.set(f"vec:{text}", vector, expire=expire)
        self.cache.set(f"resp:{text}", response_json, expire=expire)
        self.index.append((vector, text))
        logger.debug(f"Stored in Semantic Cache: {text[:50]}...")
