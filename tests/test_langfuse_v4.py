from unittest.mock import MagicMock

import pytest

from src.models.schemas import (
    ScriptRequest,
    ScriptSegment,
    ViralAudit,
    ViralScriptResponse,
)
from src.services.llm_service import ViralContentService


@pytest.fixture
def mock_langfuse():
    lf = MagicMock()
    # In v4, we use start_as_current_observation as a context manager
    # The context manager yields the generation object
    gen = MagicMock()
    lf.start_as_current_observation.return_value.__enter__.return_value = gen
    return lf


@pytest.mark.asyncio
async def test_langfuse_logging_v4_issue(mock_langfuse):
    """
    Test that start_as_current_observation is called, and check if it's used correctly.
    """
    # Setup mocks
    mock_provider = MagicMock()
    mock_provider.model = "test-model"

    response = ViralScriptResponse(
        hook="Test Hook",
        segments=[ScriptSegment(text="Test", visual_cue="Test", duration_seconds=5.0)],
        audit=ViralAudit(
            critique_negative="Too slow",
            critique_positive="Good hook",
            hook_strength=0.9,
            retention_score=0.8,
            retention_reasoning="Good",
            suggested_edits=[],
        ),
    )

    class MockUsage:
        prompt_tokens = 10
        completion_tokens = 20
        total_tokens = 30

    from unittest.mock import AsyncMock

    mock_provider.validate = AsyncMock()
    mock_provider.validate.return_value = (response, MockUsage())

    # Other dependencies
    mock_pii = MagicMock()
    mock_pii.mask_text.side_effect = lambda x: x
    mock_usage_tracker = MagicMock()
    mock_usage_tracker.extract_usage_and_log.return_value = {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30,
        "cost_usd": 0.01,
        "request_id": "test_request_id"
    }
    mock_semantic_cache = MagicMock()
    mock_semantic_cache.get.return_value = None
    mock_prompt_manager = MagicMock()
    mock_prompt_def = MagicMock()
    mock_prompt_def.id = "test_prompt"
    mock_prompt_def.version = "1"
    mock_prompt_def.config.model_name = "test-model"
    mock_prompt_def.config.temperature = 0.7
    mock_prompt_def.config.max_tokens = 100
    mock_prompt_def.system_prompt = "system prompt"
    mock_prompt_def.user_prompt_template = "user prompt"
    mock_prompt_def.shadow_version = None # Disable shadow for this test
    mock_prompt_manager.get_prompt.return_value = mock_prompt_def
    mock_prompt_manager.render_prompt.side_effect = lambda x, **kwargs: str(x)

    service = ViralContentService(
        provider=mock_provider,
        pii_service=mock_pii,
        usage_tracker=mock_usage_tracker,
        semantic_cache=mock_semantic_cache,
        prompt_manager=mock_prompt_manager,
        langfuse=mock_langfuse,
        cache_path="dummy_cache",  # Will fail if actually used, but we mock cache
    )
    service.cache = MagicMock()  # Mock the diskcache Cache
    service.cache.get.return_value = None

    request = ScriptRequest(
        topic="Test", target_audience="Test", tone="Test", platform="TikTok"
    )

    # Run the service
    await service.generate_viral_script(request)

    # Verify Langfuse calls
    assert mock_langfuse.start_as_current_observation.called
    call_args = mock_langfuse.start_as_current_observation.call_args[1]
    assert call_args["as_type"] == "generation"
    assert call_args["name"] == "viral_script_generation"

    # VERIFICATION: score_trace should be called on the generation object
    gen = mock_langfuse.start_as_current_observation.return_value.__enter__.return_value
    assert gen.score_trace.called
    assert mock_langfuse.flush.called
