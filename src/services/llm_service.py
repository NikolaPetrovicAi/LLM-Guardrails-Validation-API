import hashlib
import logging

import instructor
import openai
from diskcache import Cache
from pydantic import ValidationError

from src.core.config import settings
from src.core.exceptions import (
    AppError,
    ConfigurationError,
    LLMTimeoutError,
    LLMValidationError,
)
from src.models.schemas import ExtractionRequest, StructuredResponse
from src.services.guardrails import PIIMaskingService

logger = logging.getLogger(__name__)

class LLMValidatorService:
    """
    Service for extracting structured data from text using the 'instructor' library.
    Ensures that the LLM's output conforms to the predefined Pydantic schemas.
    Now includes PII masking and response caching.
    """

    def __init__(
        self, 
        client: instructor.Instructor, 
        pii_service: PIIMaskingService,
        model: str = settings.OPENAI_MODEL,
        cache_path: str = settings.CACHE_PATH
    ) -> None:
        """
        Initializes the service.
        """
        self.client = client
        self.model = model
        self.pii_service = pii_service
        self.cache = Cache(cache_path)

    def _generate_cache_key(self, text: str, model: str) -> str:
        """
        Generates a unique cache key based on the prompt and model.
        """
        payload = f"{text}:{model}"
        return hashlib.sha256(payload.encode()).hexdigest()

    async def extract_structured_data(
        self, request: ExtractionRequest
    ) -> StructuredResponse:
        """
        Asynchronously extract structured information from the input text.
        Includes PII masking and caching.
        """
        # Task 1: PII Masking
        original_text = request.text
        masked_text = self.pii_service.mask_text(original_text)
        
        if original_text != masked_text:
            logger.debug("PII detected and masked in input text.")

        # Task 2: Caching
        cache_key = self._generate_cache_key(masked_text, self.model)
        cached_response = self.cache.get(cache_key)

        if cached_response:
            logger.info(
                "LLM Response Cache HIT",
                extra={"cache_status": "HIT", "model": self.model}
            )
            return StructuredResponse.model_validate_json(cached_response)

        logger.info(
            "LLM Response Cache MISS",
            extra={"cache_status": "MISS", "model": self.model}
        )

        try:
            response: StructuredResponse = await self.client.chat.completions.create(
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
                    {"role": "user", "content": masked_text},
                ],
                response_model=StructuredResponse,
                max_retries=3,
            )
            
            # Store in cache (as JSON string)
            self.cache.set(cache_key, response.model_dump_json())
            
            return response

        except ValidationError as e:
            raise LLMValidationError(
                message="LLM output failed structural validation.",
                details=e.errors()
            ) from e
        except openai.AuthenticationError as e:
            raise ConfigurationError(
                message=f"LLM Provider Authentication Error: {str(e)}"
            ) from e
        except openai.APITimeoutError as e:
            raise LLMTimeoutError() from e
        except openai.APIError as e:
            raise AppError(
                message=f"OpenAI API error: {str(e)}",
                status_code=502,
                error_code="OPENAI_API_ERROR"
            ) from e
        except Exception as e:
            raise AppError(
                message=f"Unexpected error during extraction: {str(e)}",
                status_code=500,
                error_code="INTERNAL_ERROR"
            ) from e
