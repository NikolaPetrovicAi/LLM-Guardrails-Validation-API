import json
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.models.schemas import (
    ScriptRequest,
    ScriptSegment,
    ViralAudit,
    ViralScriptResponse,
)
from src.services.guardrails import PIIMaskingService
from src.services.llm_service import ViralContentService
from src.services.usage import UsageTrackerService


@pytest.fixture
def temp_metrics_log():
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl") as tmp:
        tmp_path = tmp.name
    yield tmp_path
    if os.path.exists(tmp_path):
        os.remove(tmp_path)


@pytest.fixture
def pii_service():
    return PIIMaskingService()


@pytest.mark.asyncio
async def test_metrics_logging_integration(temp_metrics_log, pii_service):
    """
    Simulates API calls and verifies metrics are correctly logged.
    """
    # 1. Setup Usage Tracker with temp log file
    usage_tracker = UsageTrackerService(metrics_log_path=temp_metrics_log)

    # 2. Setup Mock Provider
    mock_provider = MagicMock()
    mock_provider.model = "test-viral-model-v1"

    # Define 3 different responses to simulate variance
    responses = [
        ViralScriptResponse(
            hook=f"Hook {i}",
            segments=[
                ScriptSegment(text="Test", visual_cue="Test", duration_seconds=5.0)
            ],
            audit=ViralAudit(
                critique_negative="Too slow",
                critique_positive="Good hook",
                hook_strength=0.7 + (i * 0.1),
                retention_score=0.8,
                retention_reasoning="Good",
                suggested_edits=[],
            ),
        )
        for i in range(3)
    ]

    # Mock usage object
    class MockUsage:
        def __init__(self, prompt, completion):
            self.prompt_tokens = prompt
            self.completion_tokens = completion
            self.total_tokens = prompt + completion

    usage_mocks = [MockUsage(100 * (i + 1), 50 * (i + 1)) for i in range(3)]

    # Setup side effects for 3 calls
    mock_provider.validate = AsyncMock()
    mock_provider.validate.side_effect = [
        (responses[0], usage_mocks[0]),
        (responses[1], usage_mocks[1]),
        (responses[2], usage_mocks[2]),
    ]

    # 3. Setup Service
    with tempfile.TemporaryDirectory() as temp_cache:
        mock_semantic_cache = MagicMock()
        mock_semantic_cache.get.return_value = None
        mock_prompt_manager = MagicMock()
        # Mock get_prompt to return a dummy PromptDefinition
        from src.models.schemas import PromptConfig, PromptDefinition
        mock_prompt_def = PromptDefinition(
            id="test_prompt",
            version="1.0.0",
            system_prompt="system",
            user_prompt_template="user",
            config=PromptConfig(model_name="test-viral-model-v1")
        )
        mock_prompt_manager.get_prompt.return_value = mock_prompt_def
        mock_prompt_manager.render_prompt.side_effect = (
            lambda t, **kwargs: f"{t} {kwargs.get('topic', '')}"
        )

        service = ViralContentService(
            provider=mock_provider,
            pii_service=pii_service,
            usage_tracker=usage_tracker,
            semantic_cache=mock_semantic_cache,
            prompt_manager=mock_prompt_manager,
            cache_path=temp_cache,
        )

        # 4. Perform 3 unique calls
        for i in range(3):
            request = ScriptRequest(
                topic=f"Unique Topic {i}",
                target_audience="Devs",
                tone="Hype",
                platform="TikTok",
            )
            await service.generate_viral_script(request)

        # Close cache for Windows
        service.cache.close()

    # 5. Validation of the log file
    assert os.path.exists(temp_metrics_log)  # noqa: ASYNC240

    with open(temp_metrics_log, encoding="utf-8") as f:  # noqa: ASYNC230
        lines = f.readlines()

    assert len(lines) == 3

    for i, line in enumerate(lines):
        data = json.loads(line)
        assert "request_id" in data
        assert data["model_name"] == "test-viral-model-v1"
        assert data["total_tokens"] == (100 * (i + 1) + 50 * (i + 1))
        assert data["self_audit_hook_strength"] == pytest.approx(0.7 + (i * 0.1))
        assert data["latency_ms"] > 0
        assert "cost_usd" in data
        print(
            f"Verified call {i}: cost={data['cost_usd']}, "
            f"latency={data['latency_ms']}, "
            f"score={data['self_audit_hook_strength']}"
        )


if __name__ == "__main__":
    import asyncio

    # Simple runner if called directly
    asyncio.run(
        test_metrics_logging_integration("logs/test_metrics.jsonl", PIIMaskingService())
    )
