from unittest.mock import AsyncMock, MagicMock, patch

import openai
import pytest

from src.core.exceptions import AppError, LLMTimeoutError
from src.models.schemas import StructuredResponse
from src.services.providers.openai_provider import OpenAIProvider


@pytest.mark.asyncio
async def test_openai_provider_retry_on_rate_limit():
    """
    Test that OpenAIProvider retries on RateLimitError.
    """
    mock_client = MagicMock()
    # Mock chat.completions.create_with_completion to fail twice and then succeed
    mock_response = (
        StructuredResponse(
            entities=[],
            summary="Test summary",
            sentiment_score=0.5,
            sentiment_label="neutral"
        ),
        MagicMock(usage=MagicMock(prompt_tokens=10, completion_tokens=5))
    )
    
    mock_client.chat.completions.create_with_completion = AsyncMock(
        side_effect=[
            openai.RateLimitError("Rate limit exceeded", response=MagicMock(), body={}),
            openai.RateLimitError("Rate limit exceeded", response=MagicMock(), body={}),
            mock_response
        ]
    )
    
    provider = OpenAIProvider(client=mock_client)
    
    # We need to patch the settings to speed up the test
    with patch("src.services.providers.openai_provider.settings") as mock_settings:
        mock_settings.MAX_RETRIES = 3
        mock_settings.RETRY_MIN_SECONDS = 0.01
        mock_settings.RETRY_MAX_SECONDS = 0.02
        
        response, usage = await provider.validate("some text")
        
        assert response.summary == "Test summary"
        assert mock_client.chat.completions.create_with_completion.call_count == 3

@pytest.mark.asyncio
async def test_openai_provider_timeout_mapping():
    """
    Test that APITimeoutError is mapped to LLMTimeoutError.
    """
    mock_client = MagicMock()
    mock_client.chat.completions.create_with_completion = AsyncMock(
        side_effect=openai.APITimeoutError(request=MagicMock())
    )
    
    provider = OpenAIProvider(client=mock_client)
    
    with patch("src.services.providers.openai_provider.settings") as mock_settings:
        mock_settings.MAX_RETRIES = 1 # No retries for this test
        
        with pytest.raises(LLMTimeoutError):
            await provider.validate("some text")

@pytest.mark.asyncio
async def test_openai_provider_api_error_mapping():
    """
    Test that generic APIError is mapped to AppError with correct status code.
    """
    mock_client = MagicMock()
    # Create an APIError with a custom status code
    api_error = openai.APIError(
        message="Internal Server Error", 
        request=MagicMock(), 
        body={}
    )
    # Manually set status_code since OpenAI's APIError might not set it 
    # from constructor easily in mock
    api_error.status_code = 500
    
    mock_client.chat.completions.create_with_completion = AsyncMock(
        side_effect=api_error
    )
    
    provider = OpenAIProvider(client=mock_client)
    
    with patch("src.services.providers.openai_provider.settings") as mock_settings:
        mock_settings.MAX_RETRIES = 1
        
        with pytest.raises(AppError) as exc_info:
            await provider.validate("some text")
        
        assert exc_info.value.status_code == 500
        assert exc_info.value.error_code == "OPENAI_API_ERROR"
