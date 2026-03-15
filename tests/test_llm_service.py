import sys
import tempfile
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.schemas import ScriptRequest, ViralScriptResponse
from src.services.guardrails import PIIMaskingService
from src.services.llm_service import ViralContentService


@pytest.fixture
def pii_service():
    return PIIMaskingService()

@pytest.fixture
def temp_cache_dir():
    # Use a real temporary directory provided by pytest
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

@pytest.mark.asyncio
async def test_generate_viral_script_success(pii_service, temp_cache_dir):
    """
    Test successful generation of viral script from the service.
    """
    mock_response = ViralScriptResponse(
        hook="Stop scrolling!",
        segments=[{"text": "Python tips", "visual_cue": "Code", "duration_seconds": 5.0}],
        audit={"hook_strength": 0.9, "retention_reasoning": "Fast", "suggested_edits": []}
    )

    mock_provider = MagicMock()
    mock_provider.validate = AsyncMock(return_value=(mock_response, MagicMock()))
    mock_provider.model = "test-model"

    mock_usage_tracker = MagicMock()
    mock_semantic_cache = MagicMock()
    mock_semantic_cache.get.return_value = None  # Ensure semantic cache miss

    service = ViralContentService(
        provider=mock_provider, 
        pii_service=pii_service,
        usage_tracker=mock_usage_tracker,
        semantic_cache=mock_semantic_cache,
        cache_path=temp_cache_dir
    )
    request = ScriptRequest(
        topic="Python Tips",
        target_audience="Devs",
        tone="Hype",
        platform="TikTok"
    )
    
    try:
        result = await service.generate_viral_script(request)
        assert isinstance(result, ViralScriptResponse)
        assert result.hook == "Stop scrolling!"
        mock_provider.validate.assert_called_once()
    finally:
        # Crucial to close Cache to release file handles on Windows
        if sys.platform == "win32":
            service.cache.close()

@pytest.mark.asyncio
async def test_generate_viral_script_caching(pii_service, temp_cache_dir):
    """
    Verify that repeated requests for the same input use the cache.
    """
    mock_response = ViralScriptResponse(
        hook="Stop scrolling!",
        segments=[{"text": "Python tips", "visual_cue": "Code", "duration_seconds": 5.0}],
        audit={"hook_strength": 0.9, "retention_reasoning": "Fast", "suggested_edits": []}
    )

    mock_provider = MagicMock()
    mock_provider.validate = AsyncMock(return_value=(mock_response, MagicMock()))
    mock_provider.model = "test-model"

    mock_usage_tracker = MagicMock()
    mock_semantic_cache = MagicMock()
    mock_semantic_cache.get.return_value = None  # Ensure semantic cache miss

    service = ViralContentService(
        provider=mock_provider, 
        pii_service=pii_service,
        usage_tracker=mock_usage_tracker,
        semantic_cache=mock_semantic_cache,
        cache_path=temp_cache_dir
    )
    request = ScriptRequest(
        topic="Python Tips",
        target_audience="Devs",
        tone="Hype",
        platform="TikTok"
    )
    
    try:
        # First call: Cache MISS
        await service.generate_viral_script(request)
        assert mock_provider.validate.call_count == 1

        # Second call: Cache HIT
        await service.generate_viral_script(request)
        assert mock_provider.validate.call_count == 1
    finally:
        # Crucial to close Cache to release file handles on Windows
        if sys.platform == "win32":
            service.cache.close()
