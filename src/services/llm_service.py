import hashlib
import logging
from collections.abc import AsyncGenerator

from diskcache import Cache
from pydantic import ValidationError

from src.core.config import settings
from src.core.exceptions import (
    LLMValidationError,
)
from src.models.schemas import (
    ExtractionRequest,
    ScriptRequest,
    StructuredResponse,
    ViralScriptResponse,
)
from src.services.guardrails import PIIMaskingService
from src.services.providers.base import BaseLLMProvider
from src.services.semantic_cache import SemanticCacheService
from src.services.usage import UsageTrackerService

logger = logging.getLogger(__name__)

class ViralContentService:
    """
    Service for generating viral video scripts and performing audits.
    Supports PII masking, hybrid caching, and usage tracking.
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

    def _format_request_text(self, request: ScriptRequest) -> str:
        """Formats the ScriptRequest into a prompt for the LLM."""
        return (
            f"Topic: {request.topic}\n"
            f"Target Audience: {request.target_audience}\n"
            f"Tone: {request.tone}\n"
            f"Platform: {request.platform}"
        )

    async def generate_viral_script(
        self, request: ScriptRequest
    ) -> ViralScriptResponse:
        """
        Generates a viral script with hybrid caching and PII protection.
        """
        prompt_text = self._format_request_text(request)
        
        # Step 1: PII Masking
        masked_text = self.pii_service.mask_text(prompt_text)
        
        # Step 2: Exact Match Cache
        cache_key = self._generate_cache_key(masked_text)
        cached_response = self.cache.get(cache_key)

        if cached_response:
            logger.info("Exact Cache HIT", extra={"cache_status": "EXACT_HIT"})
            return ViralScriptResponse.model_validate_json(cached_response)

        # Step 3: Semantic Cache
        semantic_response = self.semantic_cache.get(masked_text)
        if semantic_response:
            return ViralScriptResponse.model_validate_json(semantic_response)

        # Step 4: LLM Generation
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

    async def extract_legacy_data(
        self, request: ExtractionRequest
    ) -> StructuredResponse:
        """
        Legacy extraction for compatibility with judge tests.
        """
        masked_text = self.pii_service.mask_text(request.text)
        
        try:
            response, usage = await self.provider.validate_structured(
                masked_text, StructuredResponse
            )
            
            self.usage_tracker.extract_usage_and_log(
                usage, getattr(self.provider, "model", "unknown")
            )
            
            return response

        except ValidationError as e:
            raise LLMValidationError(
                message="Legacy extraction failed structural validation.",
                details=e.errors()
            ) from e
        except Exception as e:
            raise e

    async def stream_viral_script(
        self, request: ScriptRequest
    ) -> AsyncGenerator[ViralScriptResponse, None]:
        """
        Streams partial script results. Bypasses cache for real-time feedback.
        """
        prompt_text = self._format_request_text(request)
        masked_text = self.pii_service.mask_text(prompt_text)
        
        async for partial in self.provider.stream(masked_text):
            yield partial

    async def check_health(self) -> bool:
        """
        Check health of LLM provider and cache.
        """
        llm_health = await self.provider.check_health()
        
        cache_health = False
        try:
            self.cache.set("__health_check__", "ok", expire=10)
            if self.cache.get("__health_check__") == "ok":
                cache_health = True
        except Exception as e:
            logger.error(f"Cache health check failed: {str(e)}")
            
        return llm_health and cache_health
