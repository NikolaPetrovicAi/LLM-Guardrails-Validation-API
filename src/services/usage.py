import logging
from typing import Any

from src.core.config import settings

logger = logging.getLogger(__name__)

class UsageTrackerService:
    """
    Service for tracking token usage and estimating costs.
    """

    def __init__(self, price_prompt_1k: float = settings.PRICE_PROMPT_1K, 
                 price_completion_1k: float = settings.PRICE_COMPLETION_1K) -> None:
        self.price_prompt_1k = price_prompt_1k
        self.price_completion_1k = price_completion_1k

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate the cost of the LLM request in USD.
        """
        prompt_cost = (prompt_tokens / 1000) * self.price_prompt_1k
        completion_cost = (completion_tokens / 1000) * self.price_completion_1k
        return round(prompt_cost + completion_cost, 6)

    def extract_usage_and_log(self, usage: Any | None, model: str) -> dict[str, Any]:
        """
        Extract usage data from LLM response and calculate cost.
        Returns usage statistics for logging.
        """
        if not usage:
            return {"usage_tracked": False}

        # Handle different usage object formats (OpenAI, Anthropic)
        prompt_tokens = getattr(usage, "prompt_tokens", 0)
        completion_tokens = getattr(usage, "completion_tokens", 0)
        
        # If OpenAI usage object has total_tokens but not the others
        if not prompt_tokens and hasattr(usage, "total_tokens"):
             prompt_tokens = usage.total_tokens

        estimated_cost = self.calculate_cost(prompt_tokens, completion_tokens)

        usage_data = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "estimated_cost_usd": estimated_cost,
            "model": model,
            "usage_tracked": True
        }

        logger.info(
            "LLM Usage tracked",
            extra=usage_data
        )

        return usage_data
