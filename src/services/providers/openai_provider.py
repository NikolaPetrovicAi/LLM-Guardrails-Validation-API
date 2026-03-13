import logging
from collections.abc import AsyncGenerator
from typing import Any

import instructor
import openai
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.core.config import settings
from src.core.exceptions import (
    AppError,
    ConfigurationError,
    LLMTimeoutError,
    LLMValidationError,
)
from src.models.schemas import StructuredResponse
from src.services.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI provider implementation using the 'instructor' library.
    """

    def __init__(self, client: instructor.Instructor, model: str = settings.OPENAI_MODEL) -> None:
        self.client = client
        self.model = model

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(multiplier=settings.RETRY_MIN_SECONDS, max=settings.RETRY_MAX_SECONDS),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError, openai.InternalServerError)),
        reraise=True
    )
    async def validate(self, text: str) -> tuple[StructuredResponse, Any | None]:
        """
        Validate and extract structured data from text using OpenAI.
        """
        try:
            # instructor returns the object directly, but we can access raw response via response_model
            response, raw = await self.client.chat.completions.create_with_completion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional AI data extractor. "
                            "Extract meaningful entities, summary, and sentiment "
                            "metrics from the user's text."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                response_model=StructuredResponse,
            )
            
            # OpenAI raw response contains usage
            usage = getattr(raw, "usage", None)
            return response, usage

        except openai.AuthenticationError as e:
            raise ConfigurationError(
                message=f"LLM Provider Authentication Error: {str(e)}"
            ) from e
        except openai.APITimeoutError as e:
            raise LLMTimeoutError() from e
        except (openai.APIError, openai.RateLimitError, openai.InternalServerError) as e:
            # If it's a retryable error, let it bubble up for tenacity
            if isinstance(e, (openai.RateLimitError, openai.APITimeoutError, openai.InternalServerError)):
                 raise e
            
            status_code = getattr(e, "status_code", 502)
            raise AppError(
                message=f"OpenAI API error: {str(e)}",
                status_code=status_code,
                error_code="OPENAI_API_ERROR"
            ) from e
        except Exception as e:
            if isinstance(e, LLMValidationError):
                raise e
            raise AppError(
                message=f"Unexpected error during extraction: {str(e)}",
                status_code=500,
                error_code="INTERNAL_ERROR"
            ) from e

    async def stream(self, text: str) -> AsyncGenerator[StructuredResponse, None]:
        """
        Asynchronously stream partial extraction results.
        """
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Extract structured data. Stream updates as you process the text.",
                    },
                    {"role": "user", "content": text},
                ],
                response_model=instructor.Partial[StructuredResponse],
                stream=True,
            )
            async for partial_obj in stream:
                yield partial_obj

        except Exception as e:
            logger.error(f"Error during streaming: {str(e)}")
            raise AppError(
                message="Error during data streaming.",
                status_code=500,
                error_code="STREAMING_ERROR"
            ) from e

    async def check_health(self) -> bool:
        """
        Simple health check for OpenAI by listing models (minimal cost/latency).
        """
        try:
            # We use the underlying openai client from instructor
            await self.client.client.models.list()
            return True
        except Exception as e:
            logger.error(f"Health check failed for OpenAI: {str(e)}")
            return False
