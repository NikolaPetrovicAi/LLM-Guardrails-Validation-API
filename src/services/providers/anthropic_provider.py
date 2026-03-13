import logging
from typing import Any

from src.models.schemas import StructuredResponse
from src.services.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)

class AnthropicProvider(BaseLLMProvider):
    """
    Placeholder for Anthropic provider implementation.
    """

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def validate(self, text: str) -> tuple[StructuredResponse, Any | None]:
        """
        Validate and extract structured data from text using Anthropic
        (Not Implemented).
        """
        raise NotImplementedError("Anthropic provider is not yet implemented.")

    async def check_health(self) -> bool:
        """
        Health check for Anthropic.
        """
        return False
