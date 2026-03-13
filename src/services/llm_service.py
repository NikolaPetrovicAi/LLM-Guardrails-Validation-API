import hashlib
import logging
from collections.abc import AsyncGenerator

from diskcache import Cache
from pydantic import ValidationError

from src.core.config import settings
from src.core.exceptions import (
    LLMValidationError,
)
from src.models.schemas import ExtractionRequest, StructuredResponse
from src.services.guardrails import PIIMaskingService
from src.services.providers.base import BaseLLMProvider
from src.services.semantic_cache import SemanticCacheService
from src.services.usage import UsageTrackerService

logger = logging.getLogger(__name__)

class LLMValidatorService:
    """
    Service for extracting structured data from text using an LLM provider.
    Supports PII masking, exact & semantic caching, and usage tracking.
    """

    def __init__(
        self, 
        provider: BaseLLMProvider, 
        pii_service: PIIMaskingService,
        usage_tracker: UsageTrackerService,
        semantic_cache: SemanticCacheService,
        cache_path: str = settings.CACHE_PATH,
        cache_expire: int = settings.CACHE_EXPIRE
    ) -> None:
        """
        Initializes the service with hybrid caching capabilities.
        """
        self.provider = provider
        self.pii_service = pii_service
        self.usage_tracker = usage_tracker
        self.semantic_cache = semantic_cache
        self.cache = Cache(cache_path)
        self.cache_expire = cache_expire

    def _generate_cache_key(self, text: str) -> str:
        """Generates a unique cache key for exact match caching."""
        return hashlib.sha256(text.encode()).hexdigest()

    async def extract_structured_data(
        self, request: ExtractionRequest
    ) -> StructuredResponse:
        """
        Extract structured info with hybrid caching and PII protection.
        """
        # Step 1: PII Masking
        masked_text = self.pii_service.mask_text(request.text)
        
        # Step 2: Exact Match Cache (Fastest)
        cache_key = self._generate_cache_key(masked_text)
        cached_response = self.cache.get(cache_key)

        if cached_response:
            logger.info("Exact Cache HIT", extra={"cache_status": "EXACT_HIT"})
            return StructuredResponse.model_validate_json(cached_response)

        # Step 3: Semantic Cache (Smartest)
        semantic_response = self.semantic_cache.get(masked_text)
        if semantic_response:
            # We don't need to log here as semantic_cache already logs HIT
            return StructuredResponse.model_validate_json(semantic_response)

        # Step 4: LLM Validation via Provider
        try:
            response, usage = await self.provider.validate(masked_text)
            
            # Step 5: Cost Tracking
            self.usage_tracker.extract_usage_and_log(
                usage, getattr(self.provider, "model", "unknown")
            )

            # Step 6: Store in both caches
            resp_json = response.model_dump_json()
            self.cache.set(cache_key, resp_json, expire=self.cache_expire)
            self.semantic_cache.set(masked_text, resp_json, expire=self.cache_expire)
            
            return response

        except ValidationError as e:
            raise LLMValidationError(
                message="LLM output failed structural validation.",
                details=e.errors()
            ) from e
        except Exception as e:
            raise e

    async def stream_structured_data(
        self, request: ExtractionRequest
    ) -> AsyncGenerator[StructuredResponse, None]:
        """
        Streams partial extraction results. Bypasses cache for real-time feedback.
        """
        masked_text = self.pii_service.mask_text(request.text)
        
        async for partial in self.provider.stream(masked_text):
            yield partial

    async def check_health(self) -> bool:
        """
        Check health of LLM provider and cache.
        """
        llm_health = await self.provider.check_health()
        
        # Simple cache health check
        cache_health = False
        try:
            self.cache.set("__health_check__", "ok", expire=10)
            if self.cache.get("__health_check__") == "ok":
                cache_health = True
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            
        return llm_health and cache_health
