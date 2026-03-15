from functools import lru_cache

import instructor
from openai import AsyncOpenAI

from src.core.config import settings
from src.services.guardrails import PIIMaskingService
from src.services.llm_service import ViralContentService
from src.services.providers.anthropic_provider import AnthropicProvider
from src.services.providers.openai_provider import OpenAIProvider
from src.services.semantic_cache import SemanticCacheService
from src.services.usage import UsageTrackerService


@lru_cache
def get_instructor_client() -> instructor.Instructor:
    """
    Creates and returns a singleton instance of the instructor-wrapped OpenAI client.
    """
    openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())
    return instructor.from_openai(openai_client)

@lru_cache
def get_pii_masking_service() -> PIIMaskingService:
    """
    Returns a singleton instance of the PIIMaskingService.
    """
    return PIIMaskingService()

@lru_cache
def get_usage_tracker_service() -> UsageTrackerService:
    """
    Returns a singleton instance of the UsageTrackerService.
    """
    return UsageTrackerService()

@lru_cache
def get_semantic_cache_service() -> SemanticCacheService:
    """
    Returns a singleton instance of the SemanticCacheService.
    """
    return SemanticCacheService()

def get_llm_provider():
    """
    Factory to get the configured LLM provider.
    """
    if settings.LLM_PROVIDER == "openai":
        client = get_instructor_client()
        return OpenAIProvider(client=client, model=settings.OPENAI_MODEL)
    elif settings.LLM_PROVIDER == "anthropic":
        return AnthropicProvider(
            api_key=settings.ANTHROPIC_API_KEY.get_secret_value(),
            model=settings.ANTHROPIC_MODEL
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.LLM_PROVIDER}")

async def get_llm_service() -> ViralContentService:
    """
    Dependency provider for ViralContentService.
    """
    provider = get_llm_provider()
    pii_service = get_pii_masking_service()
    usage_tracker = get_usage_tracker_service()
    semantic_cache = get_semantic_cache_service()
    
    return ViralContentService(
        provider=provider, 
        pii_service=pii_service,
        usage_tracker=usage_tracker,
        semantic_cache=semantic_cache
    )
