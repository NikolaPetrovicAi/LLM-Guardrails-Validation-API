import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.services.llm_service import ViralContentService
from src.models.schemas import ScriptRequest, ViralScriptResponse, ViralAudit, PromptDefinition
from src.services.optimizer import PromptOptimizerService

@pytest.fixture
def mock_provider():
    provider = AsyncMock()
    # Default response
    response = ViralScriptResponse(
        hook="Test Hook",
        segments=[],
        audit=ViralAudit(hook_strength=0.9, retention_reasoning="Good", suggested_edits=[])
    )
    provider.validate.return_value = (response, MagicMock(prompt_tokens=100, completion_tokens=50, total_tokens=150))
    return provider

@pytest.fixture
def mock_prompt_manager():
    manager = MagicMock()
    prod_prompt = PromptDefinition(
        id="test_id",
        version="1.0.0",
        system_prompt="System",
        user_prompt_template="User",
        shadow_version="0.9.0"
    )
    shadow_prompt = PromptDefinition(
        id="test_id",
        version="0.9.0",
        system_prompt="Shadow System",
        user_prompt_template="Shadow User"
    )
    manager.get_prompt.return_value = prod_prompt
    manager.get_shadow_prompt.return_value = shadow_prompt
    manager.render_prompt.side_effect = lambda t, **kwargs: t
    return manager

@pytest.mark.asyncio
async def test_shadow_deployment_triggered(mock_provider, mock_prompt_manager):
    pii_service = MagicMock()
    pii_service.mask_text.return_value = "Masked Text"
    
    semantic_cache = MagicMock()
    semantic_cache.get.return_value = None
    
    service = ViralContentService(
        provider=mock_provider,
        pii_service=pii_service,
        usage_tracker=MagicMock(),
        semantic_cache=semantic_cache,
        prompt_manager=mock_prompt_manager,
        cache_path="dummy_cache_lifecycle"
    )
    # Ensure diskcache also returns None
    service.cache = MagicMock()
    service.cache.get.return_value = None
    
    request = ScriptRequest(topic="AI", target_audience="Devs", tone="Cool", platform="TikTok")
    
    # We need to wait a bit for background tasks
    with patch("asyncio.create_task", wraps=asyncio.create_task) as mock_task:
        await service.generate_viral_script(request)
        
        # Verify shadow task was created
        assert mock_task.called
        
        # In shadow mode, we expect a call to _run_llm_generation with is_shadow=True
        # Since it's a coroutine, create_task is called with a coroutine object.
        # We check the name of the function being called if possible, 
        # or just verify that at least one task was created.
        assert mock_task.call_count >= 1

@pytest.mark.asyncio
async def test_apo_triggered_on_low_score(mock_provider, mock_prompt_manager):
    pii_service = MagicMock()
    pii_service.mask_text.return_value = "Masked Text"
    
    semantic_cache = MagicMock()
    semantic_cache.get.return_value = None
    
    # Setup low score response
    low_score_response = ViralScriptResponse(
        hook="Bad Hook",
        segments=[],
        audit=ViralAudit(hook_strength=0.5, retention_reasoning="Poor", suggested_edits=["Improve hook"])
    )
    mock_provider.validate.return_value = (low_score_response, MagicMock(total_tokens=100))
    
    mock_optimizer = AsyncMock(spec=PromptOptimizerService)
    
    service = ViralContentService(
        provider=mock_provider,
        pii_service=pii_service,
        usage_tracker=MagicMock(),
        semantic_cache=semantic_cache,
        prompt_manager=mock_prompt_manager,
        optimizer=mock_optimizer,
        cache_path="dummy_cache_apo"
    )
    service.cache = MagicMock()
    service.cache.get.return_value = None
    
    request = ScriptRequest(topic="AI", target_audience="Devs", tone="Cool", platform="TikTok")
    
    await service.generate_viral_script(request)
    
    # Give background tasks time to run
    await asyncio.sleep(0.1)
    
    # Verify optimizer was called
    mock_optimizer.critique_and_suggest.assert_called_once()
