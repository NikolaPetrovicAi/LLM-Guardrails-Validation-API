import pytest
from unittest.mock import AsyncMock, patch
from src.services.llm_service import LLMValidatorService
from src.models.schemas import ExtractionRequest, StructuredResponse


@pytest.mark.asyncio
async def test_extract_structured_data_success():
    """
    Test successful extraction of structured data from the LLM service.
    This test mocks the OpenAI client to avoid real API calls.
    """
    mock_response = StructuredResponse(
        entities=["OpenAI", "FastAPI"],
        summary="A test summary of the AI service.",
        sentiment_score=0.9,
        sentiment_label="Positive"
    )

    with patch("src.services.llm_service.instructor.from_openai") as mock_instructor:
        # Configure the mock client
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_instructor.return_value = mock_client

        service = LLMValidatorService()
        request = ExtractionRequest(text="This is a test message about OpenAI and FastAPI.")
        
        result = await service.extract_structured_data(request)

        assert isinstance(result, StructuredResponse)
        assert result.sentiment_label == "Positive"
        assert "OpenAI" in result.entities
        mock_client.chat.completions.create.assert_called_once()
