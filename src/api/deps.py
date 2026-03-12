from functools import lru_cache
import instructor
from openai import AsyncOpenAI

from src.core.config import settings
from src.services.llm_service import LLMValidatorService

@lru_cache()
def get_instructor_client() -> instructor.Instructor:
    """
    Creates and returns a singleton instance of the instructor-wrapped OpenAI client.
    """
    openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())
    return instructor.from_openai(openai_client)

async def get_llm_service() -> LLMValidatorService:
    """
    Dependency provider for LLMValidatorService.
    Uses the instructor client singleton.
    """
    client = get_instructor_client()
    return LLMValidatorService(client=client)
