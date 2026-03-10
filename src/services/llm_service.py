import instructor
from openai import AsyncOpenAI
from pydantic import ValidationError

from src.core.config import settings
from src.models.schemas import ExtractionRequest, StructuredResponse


class LLMValidatorService:
    """
    Service for extracting structured data from text using the 'instructor' library.
    Ensures that the LLM's output conforms to the predefined Pydantic schemas.
    """

    def __init__(self) -> None:
        """
        Initializes the service by wrapping the OpenAI client with instructor.
        """
        self.client = instructor.from_openai(
            AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())
        )
        self.model = settings.OPENAI_MODEL

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
            Exception: If an error occurs during the OpenAI API call or Pydantic validation.
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
            print(f"Validation error during LLM extraction: {e}")
            raise
        except Exception as e:
            # Handle general OpenAI or connectivity errors
            print(f"Error during LLM extraction: {e}")
            raise
