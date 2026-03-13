from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from src.models.schemas import StructuredResponse


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    """

    @abstractmethod
    async def validate(self, text: str) -> tuple[StructuredResponse, Any | None]:
        """
        Validate and extract structured data from text.
        Returns a tuple of (StructuredResponse, usage_object).
        """
        pass

    @abstractmethod
    async def stream(self, text: str) -> AsyncGenerator[StructuredResponse, None]:
        """
        Stream structured data from text as it's being generated.
        Yields partial StructuredResponse objects.
        """
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """
        Check the health of the provider connection.
        """
        pass
