import logging
from collections.abc import AsyncGenerator
from typing import Any

from src.models.schemas import ViralScriptResponse
from src.services.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)

class AnthropicProvider(BaseLLMProvider):
    """
    Placeholder for Anthropic provider implementation.
    """

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def validate(self, text: str) -> tuple[ViralScriptResponse, Any | None]:
        """
        Generate a viral script using Anthropic (Not Implemented).
        """
        raise NotImplementedError("Anthropic provider is not yet implemented.")

    async def stream(self, text: str) -> AsyncGenerator[ViralScriptResponse, None]:
        """
        Stream viral script using Anthropic (Not Implemented).
        """
        raise NotImplementedError("Anthropic streaming is not yet implemented.")
        yield ViralScriptResponse() # type: ignore

    async def check_health(self) -> bool:
        """
        Health check for Anthropic.
        """
        return False
