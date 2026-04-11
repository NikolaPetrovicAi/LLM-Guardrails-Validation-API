from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from typing import Any

from src.models.schemas import ViralScriptResponse


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    """

    @abstractmethod
    async def validate(
        self,
        text: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> tuple[ViralScriptResponse, Any | None]:
        """
        Validate and extract structured data from text.
        Returns a tuple of (ViralScriptResponse, usage_object).
        """
        pass

    @abstractmethod
    async def validate_structured(
        self,
        text: str,
        response_model: type[Any] | None,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> tuple[Any, Any | None]:
        """
        Validates input against a specific Pydantic model and returns usage.
        If response_model is None, returns raw text.
        """
        pass

    @abstractmethod
    async def stream(
        self,
        text: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[ViralScriptResponse, None]:
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
