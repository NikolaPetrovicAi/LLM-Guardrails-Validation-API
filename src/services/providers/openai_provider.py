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
from src.models.schemas import ViralScriptResponse
from src.services.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)

class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI provider implementation for Viral Content Engineer.
    """

    def __init__(
        self, 
        client: instructor.Instructor, 
        model: str = settings.OPENAI_MODEL
    ) -> None:
        self.client = client
        self.model = model

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(
            multiplier=settings.RETRY_MIN_SECONDS, 
            max=settings.RETRY_MAX_SECONDS
        ),
        retry=retry_if_exception_type(
            (openai.RateLimitError, openai.APITimeoutError, openai.InternalServerError)
        ),
        reraise=True
    )
    async def validate(
        self, 
        text: str, 
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None
    ) -> tuple[ViralScriptResponse, Any | None]:
        """
        Generate a viral script and audit from input parameters.
        """
        return await self.validate_structured(
            text, 
            ViralScriptResponse, 
            system_prompt, 
            model, 
            temperature, 
            max_tokens
        )

    async def validate_structured(
        self, 
        text: str, 
        response_model: type[Any] | None,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None
    ) -> tuple[Any, Any | None]:
        """
        Generic validation for any Pydantic model.
        """
        try:
            effective_model = model or self.model
            effective_system = system_prompt or (
                "You are an Elite Viral Video Strategist for TikTok, "
                "Reels, and Shorts. Your goal is to create "
                "high-retention scripts that stop the scroll."
            )
            effective_temp = temperature if temperature is not None else 0.7
            effective_max_tokens = max_tokens or 1000

            if response_model:
                response, raw = await self.client.chat.completions.create_with_completion(
                    model=effective_model,
                    messages=[
                        {"role": "system", "content": effective_system},
                        {"role": "user", "content": text},
                    ],
                    response_model=response_model,
                    temperature=effective_temp,
                    max_tokens=effective_max_tokens
                )
                usage = getattr(raw, "usage", None)
                return response, usage
            else:
                # Raw completion if no model provided
                raw = await self.client.chat.completions.create(
                    model=effective_model,
                    messages=[
                        {"role": "system", "content": effective_system},
                        {"role": "user", "content": text},
                    ],
                    temperature=effective_temp,
                    max_tokens=effective_max_tokens
                )
                content = raw.choices[0].message.content
                usage = getattr(raw, "usage", None)
                return content, usage

        except openai.AuthenticationError as e:
            raise ConfigurationError(
                message=f"LLM Provider Authentication Error: {str(e)}"
            ) from e
        except openai.APITimeoutError as e:
            raise LLMTimeoutError() from e
        except (
            openai.APIError, 
            openai.RateLimitError, 
            openai.InternalServerError
        ) as e:
            if isinstance(
                e, 
                (
                    openai.RateLimitError, 
                    openai.APITimeoutError, 
                    openai.InternalServerError
                )
            ):
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
                message=f"Unexpected error during script generation: {str(e)}",
                status_code=500,
                error_code="INTERNAL_ERROR"
            ) from e

    async def stream(
        self, 
        text: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None
    ) -> AsyncGenerator[ViralScriptResponse, None]:
        """
        Stream partial viral script results.
        """
        try:
            effective_model = model or self.model
            effective_system = system_prompt or (
                "You are an Elite Viral Video Strategist. "
                "Stream the script and audit in real-time."
            )
            effective_temp = temperature if temperature is not None else 0.7
            effective_max_tokens = max_tokens or 1000

            stream = await self.client.chat.completions.create(
                model=effective_model,
                messages=[
                    {"role": "system", "content": effective_system},
                    {"role": "user", "content": text},
                ],
                response_model=instructor.Partial[ViralScriptResponse],
                stream=True,
                temperature=effective_temp,
                max_tokens=effective_max_tokens
            )
            async for partial_obj in stream:
                yield partial_obj

        except Exception as e:
            logger.error(f"Error during streaming: {str(e)}")
            raise AppError(
                message="Error during script streaming.",
                status_code=500,
                error_code="STREAMING_ERROR"
            ) from e

    async def check_health(self) -> bool:
        """
        Simple health check for OpenAI.
        """
        try:
            await self.client.client.models.list()
            return True
        except Exception as e:
            logger.error(f"Health check failed for OpenAI: {str(e)}")
            return False
