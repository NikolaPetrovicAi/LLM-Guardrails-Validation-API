import json
import logging
import os
from typing import Any

from src.core.config import settings

logger = logging.getLogger(__name__)

class UsageTrackerService:
    """
    Service for tracking token usage and estimating costs.
    Now includes persistent logging for advanced metrics.
    """

    def __init__(self, price_prompt_1k: float = settings.PRICE_PROMPT_1K, 
                 price_completion_1k: float = settings.PRICE_COMPLETION_1K,
                 metrics_log_path: str = "logs/metrics_data.jsonl") -> None:
        self.price_prompt_1k = price_prompt_1k
        self.price_completion_1k = price_completion_1k
        self.metrics_log_path = metrics_log_path
        
        # Ensure the logs directory exists
        os.makedirs(os.path.dirname(self.metrics_log_path), exist_ok=True)

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Estimate the cost of the LLM request in USD.
        """
        prompt_cost = (prompt_tokens / 1000) * self.price_prompt_1k
        completion_cost = (completion_tokens / 1000) * self.price_completion_1k
        return round(prompt_cost + completion_cost, 6)

    def extract_usage_and_log(
        self, 
        usage: Any | None, 
        model: str, 
        request_id: str = "N/A", 
        latency_ms: float = 0.0, 
        self_score: float = 0.0,
        input_text: str = "",
        output_text: str = ""
    ) -> dict[str, Any]:
        """
        Extract usage data from LLM response, calculate cost, and log telemetry.
        Persists data to metrics_data.jsonl for future analysis.
        """
        if not usage:
            return {"usage_tracked": False}

        # Handle different usage object formats (OpenAI, Anthropic)
        prompt_tokens = getattr(usage, "prompt_tokens", 0)
        completion_tokens = getattr(usage, "completion_tokens", 0)
        
        # If OpenAI usage object has total_tokens but not the others
        if not prompt_tokens and hasattr(usage, "total_tokens"):
             prompt_tokens = usage.total_tokens

        total_tokens = prompt_tokens + completion_tokens
        estimated_cost = self.calculate_cost(prompt_tokens, completion_tokens)

        usage_data = {
            "request_id": request_id,
            "model_name": model,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "cost_usd": estimated_cost,
            "latency_ms": latency_ms,
            "self_audit_hook_strength": self_score,
            "input_text": input_text,
            "output_text": output_text,
            "usage_tracked": True
        }

        # Structured standard logging
        logger.info(
            "LLM Usage tracked",
            extra=usage_data
        )

        # Persistent telemetry logging (JSONL)
        try:
            with open(self.metrics_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(usage_data) + "\n")
        except Exception as e:
            logger.error(
                f"Failed to write telemetry data to {self.metrics_log_path}: {e}"
            )

        return usage_data
