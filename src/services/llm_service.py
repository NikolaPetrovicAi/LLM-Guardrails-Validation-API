import instructor
import openai
from openai import AsyncOpenAI
from pydantic import ValidationError

from src.core.config import settings
from src.core.exceptions import LLMTimeoutError, LLMValidationError, AppException, ConfigurationError
from src.models.schemas import ExtractionRequest, StructuredResponse


class LLMValidatorService:
    """
    Service for extracting structured data from text using the 'instructor' library.
    Ensures that the LLM's output conforms to the predefined Pydantic schemas.
    """

    def __init__(self, client: instructor.Instructor, model: str = settings.OPENAI_MODEL) -> None:
        """
        Initializes the service with an instructor-wrapped client.
        
        Args:
            client: The instructor-wrapped OpenAI client.
            model: The OpenAI model identifier to use.
        """
        self.client = client
        self.model = model

    async def extract_structured_data(
        self, request: ExtractionRequest
    ) -> StructuredResponse:
        """
        Asynchronously extract structured information from the input text.

        Args:
            request: The input text and associated metadata for extraction.

        Returns:
            StructuredResponse: The validated structured output from the LLM.

        Raises:
            LLMValidationError: If the LLM output fails schema validation.
            LLMTimeoutError: If the request to OpenAI times out.
            AppException: For other API-related errors.
        """
        try:
            # The 'instructor' library uses the 'response_model' parameter
            # to enforce structural adherence and type validation.
            response: StructuredResponse = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional AI data extractor. Extract meaningful "
                        "entities, summary, and sentiment metrics from the user's text.",
                    },
                    {"role": "user", "content": request.text},
                ],
                response_model=StructuredResponse,
                max_retries=3,
            )
            return response

        except ValidationError as e:
            # Handle cases where LLM's output did not match the Pydantic schema
            raise LLMValidationError(
                message="LLM output failed structural validation.",
                details=e.errors()
            ) from e
        except openai.AuthenticationError as e:
            # Handle authentication/API key issues
            raise ConfigurationError(
                message=f"LLM Provider Authentication Error: {str(e)}"
            ) from e
        except openai.APITimeoutError as e:
            # Handle request timeouts specifically
            raise LLMTimeoutError() from e
        except openai.APIError as e:
            # Handle general OpenAI API errors
            raise AppException(
                message=f"OpenAI API error: {str(e)}",
                status_code=502,
                error_code="OPENAI_API_ERROR"
            ) from e
        except Exception as e:
            # Fallback for any other unexpected errors
            raise AppException(
                message=f"Unexpected error during extraction: {str(e)}",
                status_code=500,
                error_code="INTERNAL_ERROR"
            ) from e
