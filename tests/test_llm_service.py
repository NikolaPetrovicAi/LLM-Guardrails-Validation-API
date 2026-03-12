import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.llm_service import LLMValidatorService
from src.models.schemas import ExtractionRequest, StructuredResponse


@pytest.mark.asyncio
async def test_extract_structured_data_success():
    """
    Test successful extraction of structured data from the LLM service.
    """
    mock_response = StructuredResponse(
        entities=["OpenAI", "FastAPI"],
        summary="A test summary of the AI service.",
        sentiment_score=0.9,
        sentiment_label="Positive"
    )

    # Mock the instructor-wrapped client
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Inject the mock client into the service
    service = LLMValidatorService(client=mock_client)
    request = ExtractionRequest(text="This is a test message about OpenAI and FastAPI.")
    
    result = await service.extract_structured_data(request)

    assert isinstance(result, StructuredResponse)
    assert result.sentiment_label == "Positive"
    assert "OpenAI" in result.entities
    mock_client.chat.completions.create.assert_called_once()
