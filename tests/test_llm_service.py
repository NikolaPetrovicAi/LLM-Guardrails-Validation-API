import pytest
from unittest.mock import AsyncMock, MagicMock
from src.services.llm_service import LLMValidatorService
from src.services.guardrails import PIIMaskingService
from src.models.schemas import ExtractionRequest, StructuredResponse
import os
import shutil
import tempfile

@pytest.fixture
def pii_service():
    return PIIMaskingService()

@pytest.fixture
def temp_cache_dir():
    # Use a real temporary directory provided by pytest
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

@pytest.mark.asyncio
async def test_extract_structured_data_success(pii_service, temp_cache_dir):
    """
    Test successful extraction of structured data from the LLM service.
    """
    mock_response = StructuredResponse(
        entities=["OpenAI", "FastAPI"],
        summary="A test summary of the AI service.",
        sentiment_score=0.9,
        sentiment_label="Positive"
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    service = LLMValidatorService(
        client=mock_client, 
        pii_service=pii_service,
        cache_path=temp_cache_dir
    )
    request = ExtractionRequest(text="This is a test message about OpenAI and FastAPI.")
    
    try:
        result = await service.extract_structured_data(request)
        assert isinstance(result, StructuredResponse)
        assert result.sentiment_label == "Positive"
        assert "OpenAI" in result.entities
        mock_client.chat.completions.create.assert_called_once()
    finally:
        # Crucial to close Cache to release file handles on Windows
        service.cache.close()

@pytest.mark.asyncio
async def test_extract_structured_data_caching(pii_service, temp_cache_dir):
    """
    Verify that repeated requests for the same input use the cache.
    """
    mock_response = StructuredResponse(
        entities=["OpenAI"],
        summary="Summary",
        sentiment_score=0.9,
        sentiment_label="Positive"
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    service = LLMValidatorService(
        client=mock_client, 
        pii_service=pii_service,
        cache_path=temp_cache_dir
    )
    request = ExtractionRequest(text="Same text")
    
    try:
        # First call: Cache MISS
        await service.extract_structured_data(request)
        assert mock_client.chat.completions.create.call_count == 1

        # Second call: Cache HIT
        await service.extract_structured_data(request)
        assert mock_client.chat.completions.create.call_count == 1
    finally:
        # Crucial to close Cache to release file handles on Windows
        service.cache.close()
