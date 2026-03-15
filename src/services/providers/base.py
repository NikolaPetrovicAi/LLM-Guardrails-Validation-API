from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from src.models.schemas import ViralScriptResponse


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    """

    @abstractmethod
    async def validate(self, text: str) -> tuple[ViralScriptResponse, Any | None]:
        """
        Validate and extract structured data from text.
        Returns a tuple of (ViralScriptResponse, usage_object).
        """
        pass

    @abstractmethod
    async def validate_structured(
        self, text: str, response_model: type[Any]
    ) -> tuple[Any, Any | None]:
        """
        Generic validation for any Pydantic model.
        """
        pass

    @abstractmethod
    async def stream(self, text: str) -> AsyncGenerator[ViralScriptResponse, None]:
        """
        Stream structured data from text as it's being generated.
        Yields partial ViralScriptResponse objects.
        """
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """
        Check the health of the provider connection.
        """
        pass
